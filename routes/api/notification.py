from datetime import timedelta
from flask import Blueprint, jsonify
from models.database import db
from models.infrastructure import Feedback, FeedbackHandling, User
from sqlalchemy import desc

api_notification_bp = Blueprint('api_notification', __name__)

@api_notification_bp.route('/notifications/<user_id>', methods=['GET'])
def get_notifications(user_id):
    try:
        notifications = []
        
        # Xác định vai trò
        is_employee = user_id.startswith('NV') or user_id.startswith('QL')

        if is_employee:
            # --- LOGIC CHO NHÂN VIÊN ---
            handlings = db.session.query(FeedbackHandling, Feedback)\
                .join(Feedback, FeedbackHandling.feedback_id == Feedback.id)\
                .filter(FeedbackHandling.employee_id == user_id)\
                .filter(FeedbackHandling.status.in_(['Đã phân công', 'Chờ nhận việc', 'Hoàn tất']))\
                .order_by(desc(FeedbackHandling.time_process))\
                .all()

            # Dùng set để lọc trùng lặp (nếu có)
            seen_ids = set()

            for h, f in handlings:
                # Nếu cùng 1 feedback mà có nhiều trạng thái, chỉ lấy cái mới nhất (do đã sort DESC)
                # Tuy nhiên với NV thì thường cần xem lịch sử, nhưng nếu bạn muốn gọn thì bỏ comment dòng dưới
                # if f.id in seen_ids: continue
                # seen_ids.add(f.id)

                # [SỬA LỖI 1] Xử lý giờ VN (+7)
                time_str = ""
                if h.time_process:
                    vn_time = h.time_process + timedelta(hours=7)
                    time_str = vn_time.strftime("%H:%M %d/%m")

                notif_item = {
                    "id": h.id,
                    "feedback_id": f.id,
                    "time": time_str,
                    "is_read": True
                }

                if h.status in ['Đã phân công', 'Chờ nhận việc']:
                    notif_item['title'] = "Nhiệm vụ mới"
                    notif_item['message'] = f"Bạn được giao xử lý sự cố tại: {f.address}"
                    notif_item['type'] = "task"
                
                elif h.status == 'Hoàn tất':
                    notif_item['title'] = "Công việc được duyệt"
                    notif_item['message'] = f"Báo cáo tại {f.address} đã được Admin duyệt."
                    notif_item['type'] = "success"

                if 'title' in notif_item:
                    notifications.append(notif_item)

        else:
            # --- LOGIC CHO NGƯỜI DÂN ---
            results = db.session.query(FeedbackHandling, Feedback)\
                .join(Feedback, FeedbackHandling.feedback_id == Feedback.id)\
                .filter(Feedback.user_id == user_id)\
                .filter(FeedbackHandling.status.in_(['Đang xử lý', 'Hoàn tất', 'Đã hủy']))\
                .order_by(desc(FeedbackHandling.time_process))\
                .all()

            # [SỬA LỖI 4] Lọc trùng lặp: Chỉ lấy trạng thái MỚI NHẤT của mỗi Feedback
            seen_feedback_ids = set()

            for h, f in results:
                if f.id in seen_feedback_ids:
                    continue # Bỏ qua các trạng thái cũ hơn của cùng 1 feedback
                seen_feedback_ids.add(f.id)

                # [SỬA LỖI 1] Xử lý giờ VN (+7)
                time_str = ""
                if h.time_process:
                    vn_time = h.time_process + timedelta(hours=7)
                    time_str = vn_time.strftime("%H:%M %d/%m")

                notif_item = {
                    "id": h.id,
                    "feedback_id": f.id, 
                    "time": time_str,
                    "is_read": True
                }

                if h.status == 'Đang xử lý':
                    notif_item['title'] = "Đang xử lý"
                    notif_item['message'] = f"Phản ánh tại {f.address} đã được tiếp nhận."
                    notif_item['type'] = "processing"
                
                elif h.status == 'Hoàn tất':
                    notif_item['title'] = "Đã xử lý xong"
                    notif_item['message'] = f"Sự cố tại {f.address} đã giải quyết xong."
                    notif_item['type'] = "success"
                    
                    # [SỬA LỖI 2] Lấy ảnh kết quả (attachment_url) gửi kèm notification
                    # Tìm dòng 'Đã xử lý' hoặc 'Hoàn tất' có ảnh
                    staff_handling = FeedbackHandling.query.filter_by(feedback_id=f.id)\
                        .filter(FeedbackHandling.attachment_url != None)\
                        .order_by(desc(FeedbackHandling.time_process)).first()
                    
                    if staff_handling and staff_handling.attachment_url:
                        # Kiểm tra list hay string
                        if isinstance(staff_handling.attachment_url, list) and len(staff_handling.attachment_url) > 0:
                            notif_item['completion_image'] = staff_handling.attachment_url[0]
                        elif isinstance(staff_handling.attachment_url, str):
                            notif_item['completion_image'] = staff_handling.attachment_url

                elif h.status == 'Đã hủy':
                    notif_item['title'] = "Phản ánh bị hủy"
                    notif_item['message'] = f"Lý do: {h.note}"
                    notif_item['type'] = "error"

                if 'title' in notif_item:
                    notifications.append(notif_item)

        return jsonify(notifications), 200

    except Exception as e:
        print(f"Notif Error: {e}")
        return jsonify({"error": str(e)}), 500
    
@api_notification_bp.route('/feedback/<feedback_id>', methods=['GET'])
def get_feedback_detail(feedback_id):
    try:
        # Lấy feedback theo ID
        feedback = Feedback.query.filter_by(id=feedback_id).first()

        if not feedback:
            return jsonify({"error": "Feedback not found"}), 404

        # Lấy lịch sử xử lý
        handling = FeedbackHandling.query\
            .filter_by(feedback_id=feedback_id)\
            .order_by(desc(FeedbackHandling.time_process))\
            .all()

        # Build response
        response = {
            "id": feedback.id,
            "content": feedback.content,
            "address": feedback.address,
            "date": feedback.date.strftime("%d/%m/%Y %H:%M"),
            "images": feedback.image_urls,   # nếu bạn có trường image_urls
            "status": feedback.status,
            "history": []
        }

        # Lịch sử xử lý
        for h in handling:
            response["history"].append({
                "status": h.status,
                "note": h.note,
                "employee_id": h.employee_id,
                "employee_name": h.employee.name if h.employee else None,
                "time": h.time_process.strftime("%d/%m/%Y %H:%M") if h.time_process else None,
                "attachment_url": h.attachment_url
            })

        return jsonify(response), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
