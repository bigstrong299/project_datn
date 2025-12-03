import base64
from flask import Blueprint, request, jsonify, current_app
from models.infrastructure import db, Feedback, User # Import đúng đường dẫn project của bạn
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