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
        is_employee = user_id.startswith('NV') or user_id.startswith('QL')

        if is_employee:
            # --- LOGIC CHO NHÂN VIÊN (Giữ nguyên hoặc sửa lọc nếu cần) ---
            handlings = db.session.query(FeedbackHandling, Feedback)\
                .join(Feedback, FeedbackHandling.feedback_id == Feedback.id)\
                .filter(FeedbackHandling.employee_id == user_id)\
                .filter(FeedbackHandling.status.in_(['Đã phân công', 'Chờ nhận việc', 'Hoàn tất']))\
                .order_by(desc(FeedbackHandling.time_process))\
                .all()
            
            seen_tasks = set() # Lọc trùng task

            for h, f in handlings:
                # Key lọc: Feedback ID + Trạng thái
                # Để nếu trạng thái thay đổi thì vẫn hiện thông báo mới
                unique_key = f"{f.id}_{h.status}"
                if unique_key in seen_tasks: continue
                seen_tasks.add(unique_key)

                time_str = ""
                if h.time_process:
                    vn_time = h.time_process + timedelta(hours=7)
                    time_str = vn_time.strftime("%H:%M %d/%m")

                notif_item = {
                    "id": h.id,
                    "feedback_id": f.id,
                    "title": "Nhiệm vụ mới" if h.status != 'Hoàn tất' else "Công việc được duyệt",
                    "message": f"Tại: {f.address}",
                    "time": time_str,
                    "type": "task" if h.status != 'Hoàn tất' else "success"
                }
                notifications.append(notif_item)
           # --- LOGIC CHO NGƯỜI DÂN ---
        else:
            results = db.session.query(FeedbackHandling, Feedback)\
                .join(Feedback, FeedbackHandling.feedback_id == Feedback.id)\
                .filter(Feedback.user_id == user_id)\
                .filter(FeedbackHandling.status.in_([
                    'Đang xử lý',
                    'Đã xử lý',
                    'Hoàn tất'
                ]))\
                .order_by(desc(FeedbackHandling.time_process))\
                .all()

            seen = set()

            for h, f in results:
                unique_key = f"{f.id}_{h.status}"
                if unique_key in seen:
                    continue
                seen.add(unique_key)

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
                    notif_item.update({
                        "title": "Đang xử lý",
                        "message": f"Phản ánh tại {f.address} đang được xử lý.",
                        "type": "processing"
                    })

                elif h.status == 'Đã xử lý':
                    notif_item.update({
                        "title": "Đã xử lý",
                        "message": f"Sự cố tại {f.address} đã được xử lý.",
                        "type": "success"
                    })

                    # ✅ ẢNH KẾT QUẢ – ĐÚNG DB
                    if h.attachment_url:
                        notif_item["completion_image"] = (
                            h.attachment_url[0]
                            if isinstance(h.attachment_url, list)
                            else h.attachment_url
                        )

                elif h.status == 'Hoàn tất':
                    notif_item.update({
                        "title": "Hoàn tất",
                        "message": f"Phản ánh tại {f.address} đã được duyệt hoàn tất.",
                        "type": "done"
                    })

                notifications.append(notif_item)

        return jsonify(notifications), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@api_notification_bp.route('/feedback/<feedback_id>', methods=['GET'])
def get_feedback_detail(feedback_id):
    try:
        feedback = Feedback.query.filter_by(id=feedback_id).first()

        if not feedback:
            return jsonify({"error": "Feedback not found"}), 404

        # Lấy tất cả lịch sử xử lý và sắp xếp theo thời gian giảm dần
        handlings = FeedbackHandling.query \
            .filter_by(feedback_id=feedback_id) \
            .order_by(desc(FeedbackHandling.time_process)) \
            .all()

        # Kết quả trả về
        response = {
            "id": feedback.id,
            "content": feedback.content,
            "address": feedback.address,
            "date": feedback.date.strftime("%H:%M %d/%m/%Y"),
            "image_urls": feedback.image_urls or [],
            "status": feedback.status,
            "history": []
        }

        # ✅ LẤY ẢNH KẾT QUẢ ĐÚNG NGHIỆP VỤ (TỪ 'Đã xử lý')
        handled = None
        for h in handlings:
            if h.status == 'Đã xử lý' and h.attachment_url:
                handled = h
                break

        if handled:
            response["latest_status"] = handled.status
            response["completion_time"] = (
                handled.time_process.strftime("%H:%M %d/%m/%Y")
                if handled.time_process else None
            )
            response["completion_images"] = (
                handled.attachment_url
                if isinstance(handled.attachment_url, list)
                else [handled.attachment_url]
            )
        else:
            # Không có ảnh xử lý → lấy trạng thái mới nhất
            latest = handlings[0] if handlings else None
            response["latest_status"] = latest.status if latest else None
            response["completion_time"] = None
            response["completion_images"] = []

        # Lịch sử xử lý chi tiết
        for h in handlings:
            response["history"].append({
                "status": h.status,
                "note": h.note,
                "employee_id": h.employee_id,
                "employee_name": h.employee.name if h.employee else None,
                "time": h.time_process.strftime("%H:%M %d/%m/%Y") if h.time_process else None,
                "attachment_url": h.attachment_url
            })

        return jsonify(response), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
