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
    """
    API nhận phản ánh từ người dân.
    Method: POST (multipart/form-data)
    Fields: user_id, content, latitude, longitude, address, images (file list)
    """
    try:
        # 1. Lấy dữ liệu Text
        user_id = request.form.get('user_id')
        content = request.form.get('content')
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')
        address = request.form.get('address')

        if not user_id or not content:
            return jsonify({'error': 'Thiếu thông tin user_id hoặc nội dung'}), 400

        # Kiểm tra user tồn tại
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'Người dùng không tồn tại'}), 404

        # 2. Xử lý Upload Ảnh (Lưu nhiều ảnh)
        image_urls = []
        if 'images' in request.files:
            files = request.files.getlist('images')
            for file in files:
                if file and allowed_file(file.filename):
                    filename = secure_filename(f"{datetime.datetime.now().timestamp()}_{file.filename}")
                    
                    # Tạo folder nếu chưa có
                    save_path = os.path.join(current_app.root_path, UPLOAD_FOLDER)
                    os.makedirs(save_path, exist_ok=True)
                    
                    file.save(os.path.join(save_path, filename))
                    # Lưu đường dẫn tương đối để serve file
                    image_urls.append(f"/{UPLOAD_FOLDER}/{filename}")

        # 3. Lưu vào Database
        # ID sẽ được sinh tự động bởi Trigger DB hoặc logic Python tùy cấu hình
        # Ở đây tôi để DB trigger lo, nhưng SQLAlchemy cần commit mới thấy ID
        new_feedback = Feedback(
            user_id=user_id,
            content=content,
            image_urls=image_urls, # Cần đảm bảo DB column là ARRAY hoặc JSON
            latitude=float(latitude) if latitude else None,
            longitude=float(longitude) if longitude else None,
            address=address,
            status='Chờ xử lý'
        )

        db.session.add(new_feedback)
        db.session.commit()

        return jsonify({
            'message': 'Gửi phản ánh thành công',
            'data': {
                'id': new_feedback.id,
                'status': new_feedback.status
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500