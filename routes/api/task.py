from flask import Blueprint, request, jsonify
from models.database import db
from models.infrastructure import Feedback, FeedbackHandling
import datetime
from sqlalchemy import desc

api_task_bp = Blueprint('api_task', __name__)

# --- 1. LẤY DANH SÁCH NHIỆM VỤ ---
@api_task_bp.route('/tasks/<employee_id>', methods=['GET'])
def get_my_tasks(employee_id):
    try:
        print(f"DEBUG: Đang lấy task cho nhân viên {employee_id}")

        valid_statuses = ['Chờ nhận việc', 'Đã phân công', 'Đang xử lý', 'Đã xử lý']
        
        # Query bảng Handling và join với Feedback
        handlings = db.session.query(FeedbackHandling, Feedback)\
            .join(Feedback, FeedbackHandling.feedback_id == Feedback.id)\
            .filter(FeedbackHandling.employee_id == employee_id)\
            .filter(FeedbackHandling.status.in_(valid_statuses))\
            .order_by(desc(FeedbackHandling.time_process))\
            .all()

        results = []
        for h, f in handlings:
            start_date = h.time_process if h.time_process else datetime.datetime.now()
            deadline = start_date + datetime.timedelta(days=3)
            
            # --- XỬ LÝ ẢNH TỪ FEEDBACK (DÂN GỬI) ---
            # Cột này tên là 'image_urls' (dạng danh sách)
            customer_img = None
            if f.image_urls and len(f.image_urls) > 0:
                customer_img = f.image_urls[0] 
            # ---------------------------------------

            addr = f.address if f.address else "Chưa cập nhật vị trí"

            results.append({
                "handling_id": h.id,
                "feedback_id": f.id,
                "title": f"Sự cố tại {addr[:15]}..." if len(addr) > 15 else f"Sự cố tại {addr}",
                "content": f.content,
                "address": addr,
                "status": h.status,
                "assigned_date": start_date.strftime("%d/%m/%Y %H:%M"),
                "deadline": deadline.strftime("%d/%m/%Y"),
                "customer_image": customer_img 
            })

        return jsonify(results), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Lỗi Server", "details": str(e)}), 500


# --- 2. CẬP NHẬT TRẠNG THÁI & GỬI ẢNH BÁO CÁO ---
@api_task_bp.route('/tasks/action', methods=['POST'])
def task_action():
    try:
        data = request.get_json(force=True, silent=True) 
        if not data: data = request.form.to_dict()

        handling_id = data.get('handling_id')
        action = data.get('action') 
        note = data.get('note')
        
        # [THAY ĐỔI] Nhận danh sách ảnh (List)
        # Frontend sẽ gửi key: "images_base64": ["data:...", "data:..."]
        images_base64 = data.get('images_base64') 

        # ... (Phần kiểm tra handling_id giữ nguyên) ...
        handling = FeedbackHandling.query.get(handling_id)
        if not handling: return jsonify({"error": "Task not found"}), 404
        feedback = Feedback.query.get(handling.feedback_id)

        if action == 'accept':
            # ... (Giữ nguyên logic accept) ...
            handling.status = 'Đang xử lý'
            if feedback: feedback.status = 'Đang xử lý'
            handling.time_process = datetime.datetime.now()

        elif action == 'complete':
            handling.status = 'Đã xử lý'
            if feedback: feedback.status = 'Đã xử lý'
            
            # Ghi chú
            current_note = handling.note if handling.note else ""
            if note: handling.note = f"{current_note}\n[NV Báo cáo]: {note}"
            
            # [THAY ĐỔI] Lưu danh sách ảnh vào cột attachment_url (kiểu ARRAY)
            if images_base64 and isinstance(images_base64, list):
                # Nếu muốn giữ ảnh cũ và thêm ảnh mới:
                # current_imgs = list(handling.attachment_url) if handling.attachment_url else []
                # current_imgs.extend(images_base64)
                # handling.attachment_url = current_imgs
                
                # Hoặc ghi đè ảnh mới (thường dùng cho báo cáo hoàn thành):
                handling.attachment_url = images_base64

        db.session.commit()
        return jsonify({"message": "Thao tác thành công"}), 200

    except Exception as e:
        db.session.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500