from flask import Blueprint, request, jsonify
from models.database import db
from models.infrastructure import Feedback, FeedbackHandling, Employee
import datetime
from sqlalchemy import desc

api_task_bp = Blueprint('api_task', __name__)

# --- 1. LẤY DANH SÁCH NHIỆM VỤ ---
@api_task_bp.route('/tasks/<employee_id>', methods=['GET'])
def get_my_tasks(employee_id):
    try:
        print(f"DEBUG: Đang lấy task cho nhân viên {employee_id}")

        # Các trạng thái cần lấy
        valid_statuses = ['Chờ nhận việc', 'Đã phân công', 'Đang xử lý', 'Đã xử lý']
        
        # Query chuẩn theo Model
        # Join FeedbackHandling với Feedback thông qua khóa ngoại feedback_id
        handlings = db.session.query(FeedbackHandling, Feedback)\
            .join(Feedback, FeedbackHandling.feedback_id == Feedback.id)\
            .filter(FeedbackHandling.employee_id == employee_id)\
            .filter(FeedbackHandling.status.in_(valid_statuses))\
            .order_by(desc(FeedbackHandling.time_process))\
            .all()

        results = []
        for h, f in handlings:
            # Xử lý ngày tháng an toàn (tránh lỗi NoneType)
            start_date = h.time_process if h.time_process else datetime.datetime.now()
            deadline = start_date + datetime.timedelta(days=3)
            
            # Xử lý ảnh (tránh lỗi nếu image_urls là None hoặc rỗng)
            customer_img = None
            if f.image_urls and len(f.image_urls) > 0:
                customer_img = f.image_urls[0]

            # Xử lý địa chỉ
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

        print(f"DEBUG: Tìm thấy {len(results)} task.")
        return jsonify(results), 200

    except Exception as e:
        # In lỗi chi tiết ra terminal để bạn debug
        import traceback
        traceback.print_exc() 
        return jsonify({"error": "Lỗi Server", "details": str(e)}), 500


# --- 2. CẬP NHẬT TRẠNG THÁI ---
@api_task_bp.route('/tasks/action', methods=['POST'])
def task_action():
    try:
        data = request.get_json(force=True, silent=True) 
        if not data:
            data = request.form.to_dict()

        handling_id = data.get('handling_id')
        action = data.get('action') 
        note = data.get('note')
        image_base64 = data.get('image_base64') 

        if not handling_id:
            return jsonify({"error": "Thiếu handling_id"}), 400

        handling = FeedbackHandling.query.get(handling_id)
        if not handling:
            return jsonify({"error": "Không tìm thấy nhiệm vụ"}), 404
            
        feedback = Feedback.query.get(handling.feedback_id)

        # Logic Tiếp nhận
        if action == 'accept':
            handling.status = 'Đang xử lý'
            if feedback: feedback.status = 'Đang xử lý'
            handling.time_process = datetime.datetime.now()
            
        # Logic Hoàn thành
        elif action == 'complete':
            handling.status = 'Đã xử lý'
            if feedback: feedback.status = 'Đã xử lý'
            
            # Lưu ghi chú
            current_note = handling.note if handling.note else ""
            if note:
                handling.note = f"{current_note}\n[NV Báo cáo]: {note}"
            
            # Lưu ảnh Base64 vào cột image_urls (vì trong model FeedbackHandling của bạn có cột này)
            # Lưu ý: Model của bạn khai báo image_urls là ARRAY(db.String), nên cần lưu dạng list
            if image_base64:
                if handling.image_urls is None:
                    handling.image_urls = [image_base64]
                else:
                    # SQLAlchemy cần gán lại list mới để nhận biết thay đổi
                    new_list = list(handling.image_urls)
                    new_list.append(image_base64)
                    handling.image_urls = new_list

        db.session.commit()
        return jsonify({"message": "Thao tác thành công"}), 200

    except Exception as e:
        db.session.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500