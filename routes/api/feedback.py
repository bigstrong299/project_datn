import base64
from flask import Blueprint, request, jsonify, current_app
from sqlalchemy import desc
from models.infrastructure import FeedbackHandling, db, Feedback, User # Import đúng đường dẫn project của bạn
from werkzeug.utils import secure_filename
import os
import datetime

api_feedback_bp = Blueprint('api_feedback', __name__)

# Cấu hình upload (Nên chuyển vào config chung của app)
UPLOAD_FOLDER = 'static/uploads/feedbacks'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@api_feedback_bp.route('/feedback/create', methods=['POST'])
def create_feedback():
    try:
        user_id = request.form.get('user_id')
        content = request.form.get('content')
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')
        address = request.form.get('address')

        image_urls = []
        
        # --- XỬ LÝ ẢNH THÀNH BASE64 ---
        if 'images' in request.files:
            files = request.files.getlist('images')
            for file in files:
                if file:
                    # 1. Đọc dữ liệu file
                    file_data = file.read()
                    # 2. Mã hóa thành Base64
                    base64_str = base64.b64encode(file_data).decode('utf-8')
                    # 3. Tạo chuỗi hoàn chỉnh để hiển thị được trên Web/App
                    # Lưu ý: file.content_type thường là 'image/jpeg' hoặc 'image/png'
                    full_string = f"data:{file.content_type};base64,{base64_str}"
                    
                    image_urls.append(full_string)
        # ------------------------------

        # Lưu vào DB
        new_feedback = Feedback(
            user_id=user_id,
            content=content,
            image_urls=image_urls, # Lúc này nó là list các chuỗi Base64 rất dài
            latitude=float(latitude) if latitude else None,
            longitude=float(longitude) if longitude else None,
            address=address,
            status='Chờ xử lý'
        )

        db.session.add(new_feedback)
        db.session.commit()

        return jsonify({'message': 'Gửi phản ánh thành công'}), 201

    except Exception as e:
        db.session.rollback()
        print(f"Lỗi: {e}") # In lỗi ra terminal để xem
        return jsonify({'error': str(e)}), 500
    
# --- API 2: Lấy chi tiết (BỔ SUNG CÁI NÀY ĐỂ APP CHẠY ĐƯỢC) ---
@api_feedback_bp.route('/feedback/<feedback_id>', methods=['GET'])
def get_feedback_detail_mobile(feedback_id):
    try:
        # 1. Lấy thông tin phản ánh
        feedback = Feedback.query.get(feedback_id)
        if not feedback:
            return jsonify({'error': 'Không tìm thấy'}), 404

        # 2. Tìm thông tin hoàn thành (Ảnh & Thời gian)
        # Lấy dòng handling mới nhất có trạng thái 'Đã xử lý' hoặc 'Hoàn tất'
        completion_data = FeedbackHandling.query.filter_by(feedback_id=feedback_id)\
            .filter(FeedbackHandling.status.in_(['Đã xử lý', 'Hoàn tất']))\
            .order_by(desc(FeedbackHandling.time_process))\
            .first()

        completion_images = []
        completion_time = None

        if completion_data:
            # Lấy ảnh báo cáo (attachment_url)
            if completion_data.attachment_url:
                # Xử lý an toàn dù là List hay String
                if isinstance(completion_data.attachment_url, list):
                    completion_images = completion_data.attachment_url
                else:
                    completion_images = [completion_data.attachment_url]
            
            # Lấy thời gian (+7 tiếng cho giờ Việt Nam)
            if completion_data.time_process:
                vn_time = completion_data.time_process + datetime.timedelta(hours=7)
                completion_time = vn_time.strftime("%H:%M %d/%m/%Y")

        # 3. Trả về JSON đầy đủ cho App
        return jsonify({
            'id': feedback.id,
            'content': feedback.content,
            'address': feedback.address,
            'status': feedback.status,
            'image_urls': feedback.image_urls,
            # Xử lý tọa độ để không bị null
            'latitude': feedback.latitude if feedback.latitude else 10.762622,
            'longitude': feedback.longitude if feedback.longitude else 106.660172,
            'date': feedback.date.strftime("%H:%M %d/%m/%Y"),
            
            # Dữ liệu kết quả xử lý
            'completion_images': completion_images, 
            'completion_time': completion_time
        }), 200

    except Exception as e:
        print(f"Error Mobile Detail: {e}")
        return jsonify({'error': str(e)}), 500