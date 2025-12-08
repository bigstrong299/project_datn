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

        else:
            # --- LOGIC CHO NGƯỜI DÂN (SỬA LẠI ĐỂ HIỆN CẢ ĐANG XỬ LÝ & HOÀN TẤT) ---
            results = db.session.query(FeedbackHandling, Feedback)\
                .join(Feedback, FeedbackHandling.feedback_id == Feedback.id)\
                .filter(Feedback.user_id == user_id)\
                .filter(FeedbackHandling.status.in_(['Đang xử lý', 'Hoàn tất', 'Đã hủy']))\
                .order_by(desc(FeedbackHandling.time_process))\
                .all()

            # [QUAN TRỌNG] Set để lọc
            seen_status_per_feedback = set()

            for h, f in results:
                # Tạo key duy nhất: ID Phản ánh + Trạng thái
                # Ví dụ: "FB001_Đang xử lý" và "FB001_Hoàn tất" là khác nhau -> Cả 2 đều được hiện
                unique_key = f"{f.id}_{h.status}"
                
                if unique_key in seen_status_per_feedback:
                    continue # Bỏ qua nếu trùng trạng thái cũ của cùng 1 feedback
                
                seen_status_per_feedback.add(unique_key)

                # Xử lý giờ
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
                    
                    # Lấy ảnh kết quả
                    if h.attachment_url:
                        imgs = h.attachment_url
                        if isinstance(imgs, list) and len(imgs) > 0:
                            notif_item['completion_image'] = imgs[0]
                        elif isinstance(imgs, str):
                            notif_item['completion_image'] = imgs

                elif h.status == 'Đã hủy':
                    notif_item['title'] = "Phản ánh bị hủy"
                    notif_item['message'] = f"Lý do: {h.note}"
                    notif_item['type'] = "error"

                if 'title' in notif_item:
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

        # Lấy xử lý mới nhất
        latest_status = None
        latest_images = []
        latest_time = None

        if handlings:
            latest = handlings[0]
            latest_status = latest.status
            latest_time = latest.time_process.strftime("%H:%M %d/%m/%Y") if latest.time_process else None

            # Lấy ảnh xử lý
            if latest.attachment_url:
                if isinstance(latest.attachment_url, list):
                    latest_images = latest.attachment_url
                else:
                    latest_images = [latest.attachment_url]

        response["latest_status"] = latest_status
        response["completion_time"] = latest_time
        response["completion_images"] = latest_images

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
