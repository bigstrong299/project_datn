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

        # 1. Thêm 'Hoàn tất' vào đây nếu bạn muốn hiện cả task đã xong
        valid_statuses = ['Chờ nhận việc', 'Đã phân công', 'Đang xử lý', 'Đã xử lý', 'Hoàn tất']
        
        handlings = db.session.query(FeedbackHandling, Feedback)\
            .join(Feedback, FeedbackHandling.feedback_id == Feedback.id)\
            .filter(FeedbackHandling.employee_id == employee_id)\
            .filter(FeedbackHandling.status.in_(valid_statuses))\
            .order_by(desc(FeedbackHandling.time_process))\
            .all()

        results = []
        # Dùng set để lọc trùng lặp (nếu 1 feedback có nhiều dòng handling cho cùng 1 nv)
        seen_feedback_ids = set()

        for h, f in handlings:
            if f.id in seen_feedback_ids:
                continue
            seen_feedback_ids.add(f.id)

            # ... (Code xử lý ngày tháng giữ nguyên) ...
            start_date = h.time_process if h.time_process else datetime.datetime.now()
            deadline = start_date + datetime.timedelta(days=3)
            customer_img = f.image_urls[0] if f.image_urls and len(f.image_urls) > 0 else None
            addr = f.address if f.address else "Chưa cập nhật vị trí"

            results.append({
                "handling_id": h.id,
                "feedback_id": f.id,
                "title": f"Sự cố tại {addr[:15]}..." if len(addr) > 15 else f"Sự cố tại {addr}",
                "content": f.content,
                "address": addr,
                
                # [QUAN TRỌNG - SỬA TẠI ĐÂY]
                # Lấy status của bảng Feedback (f.status) thay vì bảng Handling (h.status)
                # Để khi Admin duyệt 'Hoàn tất', App sẽ thấy ngay 'Hoàn tất'
                "status": f.status, 
                
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
        data = request.get_json(force=True, silent=True) or request.form.to_dict()

        feedback_id = data.get('feedback_id')
        employee_id = data.get('employee_id') # App phải gửi cái này lên
        action = data.get('action') 
        note = data.get('note')
        images_base64 = data.get('images_base64')

        feedback = Feedback.query.get(feedback_id)
        if not feedback: return jsonify({"error": "Not found"}), 404

        # A. NHÂN VIÊN TIẾP NHẬN -> TẠO DÒNG LỊCH SỬ "ĐANG XỬ LÝ"
        if action == 'accept':
            feedback.status = 'Đang xử lý'
            
            # INSERT DÒNG MỚI
            new_handling = FeedbackHandling(
                feedback_id=feedback_id,
                employee_id=employee_id,
                status='Đang xử lý',
                note="Nhân viên đã bắt đầu xử lý",
                time_process=datetime.datetime.now()
            )
            db.session.add(new_handling)

        # B. NHÂN VIÊN BÁO CÁO -> TẠO DÒNG LỊCH SỬ "ĐÃ XỬ LÝ"
        elif action == 'complete':
            feedback.status = 'Đã xử lý'
            
            # INSERT DÒNG MỚI
            final_handling = FeedbackHandling(
                feedback_id=feedback_id,
                employee_id=employee_id,
                status='Đã xử lý',
                note=f"[NV Báo cáo]: {note}",
                image_urls=images_base64 if images_base64 else [], # Lưu ảnh vào dòng này
                time_process=datetime.datetime.now()
            )
            db.session.add(final_handling)

        db.session.commit()
        return jsonify({"message": "Success"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500