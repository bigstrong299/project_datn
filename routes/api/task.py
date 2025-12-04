from flask import Blueprint, request, jsonify
from models.database import db
from models.infrastructure import Feedback, FeedbackHandling
import datetime
import os
from werkzeug.utils import secure_filename

api_task_bp = Blueprint('api_task', __name__)

# 1. Lấy danh sách nhiệm vụ của nhân viên
@api_task_bp.route('/tasks/<employee_id>', methods=['GET'])
def get_my_tasks(employee_id):
    try:
        # Lấy các task trong bảng Handling được giao cho nhân viên này
        handlings = db.session.query(FeedbackHandling, Feedback)\
            .join(Feedback, FeedbackHandling.feedback_id == Feedback.id)\
            .filter(FeedbackHandling.employee_id == employee_id)\
            .filter(FeedbackHandling.status.in_(['Chờ nhận việc', 'Đang xử lý']))\
            .order_by(FeedbackHandling.time_process.desc())\
            .all()

        results = []
        for h, f in handlings:
            # Tính deadline (3 ngày từ lúc giao)
            start_date = h.time_process if h.time_process else datetime.datetime.now()
            deadline = start_date + datetime.timedelta(days=3)
            
            results.append({
                "handling_id": h.id,
                "feedback_id": f.id,
                "title": f"Sự cố tại {f.address[:20]}...",
                "content": f.content,
                "address": f.address,
                "status": h.status, # 'Chờ nhận việc' hoặc 'Đang xử lý'
                "assigned_date": start_date.strftime("%d/%m/%Y %H:%M"),
                "deadline": deadline.strftime("%d/%m/%Y"),
                "customer_image": f.image_urls[0] if f.image_urls else None
            })

        return jsonify(results), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 2. Nhân viên Thao tác (Tiếp nhận / Hoàn thành)
@api_task_bp.route('/tasks/action', methods=['POST'])
def task_action():
    try:
        # Lấy dữ liệu dạng JSON
        data = request.json
        
        handling_id = data.get('handling_id')
        action = data.get('action') # 'accept' hoặc 'complete'
        note = data.get('note')
        
        # Nhận chuỗi Base64 (Ví dụ: data:image/jpeg;base64,/9j/4AAQSk...)
        image_base64 = data.get('image_base64') 
        
        handling = FeedbackHandling.query.get(handling_id)
        if not handling:
            return jsonify({"error": "Không tìm thấy nhiệm vụ"}), 404
            
        feedback = Feedback.query.get(handling.feedback_id)

        # A. TIẾP NHẬN
        if action == 'accept':
            handling.status = 'Đang xử lý'
            feedback.status = 'Đang xử lý'
            handling.time_process = datetime.datetime.now()
            db.session.commit()
            return jsonify({"message": "Đã tiếp nhận nhiệm vụ"}), 200

        # B. HOÀN THÀNH (Lưu Base64)
        elif action == 'complete':
            handling.status = 'Đã xử lý'
            handling.note = (handling.note or "") + f"\n[NV Báo cáo]: {note}"
            
            # --- LƯU TRỰC TIẾP CHUỖI BASE64 VÀO DB ---
            if image_base64:
                handling.attachment_url = image_base64 
            # -----------------------------------------
            
            feedback.status = 'Đã xử lý' 
            
            db.session.commit()
            return jsonify({"message": "Đã báo cáo hoàn thành"}), 200

    except Exception as e:
        db.session.rollback()
        print(f"Lỗi Task: {e}")
        return jsonify({"error": str(e)}), 500