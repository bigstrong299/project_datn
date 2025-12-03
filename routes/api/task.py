from flask import Blueprint, request, jsonify
from models.infrastructure import db, Feedback, FeedbackHandling, User
from datetime import datetime

api_task_bp = Blueprint('api_task', __name__)

# 1. Lấy danh sách nhiệm vụ của nhân viên
@api_task_bp.route('/tasks/<employee_id>', methods=['GET'])
def get_employee_tasks(employee_id):
    try:
        # Join bảng Handling và Feedback để lấy công việc được giao cho nhân viên này
        # Lấy các trạng thái mà nhân viên quan tâm
        tasks = db.session.query(Feedback, FeedbackHandling)\
            .join(FeedbackHandling, Feedback.id == FeedbackHandling.feedback_id)\
            .filter(FeedbackHandling.employee_id == employee_id)\
            .filter(Feedback.status.in_(['Đã phân công', 'Đang xử lý', 'Đã xử lý']))\
            .order_by(Feedback.date.desc())\
            .all()

        results = []
        for fb, hd in tasks:
            user_name = fb.user.name if fb.user else "Ẩn danh"
            results.append({
                "id": fb.id,
                "title": f"Phản ánh từ {user_name}",
                "content": fb.content,
                "address": fb.address,
                "status": fb.status,
                "date": fb.date.strftime("%d/%m/%Y %H:%M"),
                "image": fb.image_urls[0] if fb.image_urls else None,
                "latitude": fb.latitude,
                "longitude": fb.longitude
            })

        return jsonify(results), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 2. Nhân viên cập nhật tiến độ (Bắt đầu / Hoàn thành)
@api_task_bp.route('/tasks/update', methods=['POST'])
def update_task_status():
    try:
        feedback_id = request.json.get('feedback_id')
        new_status = request.json.get('status') # 'Đang xử lý' hoặc 'Đã xử lý'
        note = request.json.get('note') # Ghi chú của nhân viên (ví dụ: Đã dọn xong)

        feedback = Feedback.query.get(feedback_id)
        handling = FeedbackHandling.query.filter_by(feedback_id=feedback_id).first()

        if feedback and handling:
            feedback.status = new_status
            
            # Nếu nhân viên update ghi chú, ta lưu đè hoặc nối thêm
            if note:
                handling.note = (handling.note or "") + f"\n[NV]: {note}"
            
            # Cập nhật thời gian
            handling.time_process = datetime.now()
            
            db.session.commit()
            return jsonify({"message": "Cập nhật thành công"}), 200
        
        return jsonify({"error": "Không tìm thấy nhiệm vụ"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500