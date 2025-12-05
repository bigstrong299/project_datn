from flask import Blueprint, jsonify
from models.database import db
from models.infrastructure import Feedback, FeedbackHandling, User
from sqlalchemy import desc

api_notification_bp = Blueprint('api_notification', __name__)

@api_notification_bp.route('/notifications/<user_id>', methods=['GET'])
def get_notifications(user_id):
    try:
        notifications = []
        
        # KIỂM TRA XEM ID LÀ CỦA USER HAY EMPLOYEE
        # (Giả sử ID nhân viên bắt đầu bằng NV hoặc QL, User bắt đầu bằng ND hoặc khác)
        is_employee = user_id.startswith('NV') or user_id.startswith('QL')

        if is_employee:
            # --- LOGIC CHO NHÂN VIÊN ---
            # Tìm các sự kiện liên quan đến nhân viên này trong bảng Handling
            # 1. Nhiệm vụ mới (Trạng thái: 'Đã phân công' hoặc 'Chờ nhận việc')
            # 2. Được duyệt (Trạng thái: 'Hoàn tất')
            
            handlings = db.session.query(FeedbackHandling, Feedback)\
                .join(Feedback, FeedbackHandling.feedback_id == Feedback.id)\
                .filter(FeedbackHandling.employee_id == user_id)\
                .filter(FeedbackHandling.status.in_(['Đã phân công', 'Chờ nhận việc', 'Hoàn tất']))\
                .order_by(desc(FeedbackHandling.time_process))\
                .all()

            for h, f in handlings:
                notif_item = {
                    "id": h.id,
                    "feedback_id": f.id,
                    "time": h.time_process.strftime("%H:%M %d/%m") if h.time_process else "",
                    "is_read": True # Mặc định là true vì không lưu trạng thái đọc
                }

                if h.status in ['Đã phân công', 'Chờ nhận việc']:
                    notif_item['title'] = "Nhiệm vụ mới"
                    notif_item['message'] = f"Bạn được giao xử lý sự cố tại: {f.address}"
                    notif_item['type'] = "task"
                
                elif h.status == 'Hoàn tất':
                    notif_item['title'] = "Công việc đã được duyệt"
                    notif_item['message'] = f"Báo cáo xử lý tại {f.address} đã được Admin chấp thuận."
                    notif_item['type'] = "system"

                notifications.append(notif_item)

        else:
            # --- LOGIC CHO NGƯỜI DÂN ---
            # Tìm các Feedback của người này và xem lịch sử xử lý của nó
            # Join: Feedback -> Handling
            
            results = db.session.query(FeedbackHandling, Feedback)\
                .join(Feedback, FeedbackHandling.feedback_id == Feedback.id)\
                .filter(Feedback.user_id == user_id)\
                .filter(FeedbackHandling.status.in_(['Đang xử lý', 'Hoàn tất', 'Đã hủy']))\
                .order_by(desc(FeedbackHandling.time_process))\
                .all()

            for h, f in results:
                notif_item = {
                    "id": h.id,
                    "feedback_id": f.id,
                    "time": h.time_process.strftime("%H:%M %d/%m") if h.time_process else "",
                    "is_read": True
                }

                if h.status == 'Đang xử lý':
                    notif_item['title'] = "Đang xử lý"
                    notif_item['message'] = f"Phản ánh của bạn tại {f.address} đã được nhân viên tiếp nhận."
                    notif_item['type'] = "feedback"
                
                elif h.status == 'Hoàn tất':
                    notif_item['title'] = "Đã xử lý xong"
                    notif_item['message'] = f"Sự cố tại {f.address} đã được giải quyết hoàn toàn."
                    notif_item['type'] = "success"

                elif h.status == 'Đã hủy':
                    notif_item['title'] = "Phản ánh bị hủy"
                    notif_item['message'] = f"Phản ánh tại {f.address} đã bị hủy. Lý do: {h.note}"
                    notif_item['type'] = "error"

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
