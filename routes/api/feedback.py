from flask import Blueprint, request, jsonify
from models.infrastructure import db, Feedback, FeedbackHandling
import uuid, os

feedback_api = Blueprint("feedback_api", __name__)

UPLOAD_FOLDER = "static/feedback_images"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@feedback_api.route("/feedback", methods=["POST"])
def create_feedback():
    try:
        id = str(uuid.uuid4())[:20]
        user_id = request.form.get("user_id")
        content = request.form.get("content")
        latitude = request.form.get("latitude")
        longitude = request.form.get("longitude")
        address = request.form.get("address")

        images = request.files.getlist("images")
        saved_images = []

        for img in images:
            filename = f"{id}_{img.filename}"
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            img.save(filepath)
            saved_images.append(filename)

        feedback = Feedback(
            id=id,
            user_id=user_id,
            content=content,
            image_urls=saved_images,
            latitude=latitude,
            longitude=longitude,
            address=address,
            status="pending"
        )

        db.session.add(feedback)
        db.session.commit()

        return jsonify({"message": "success", "feedback_id": id}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500



# ================================
# 2. API xem danh sách Feedback
# ================================
@feedback_api.route("/feedback", methods=["GET"])
def list_feedback():
    feedbacks = Feedback.query.order_by(Feedback.date.desc()).all()

    data = []
    for fb in feedbacks:
        data.append({
            "id": fb.id,
            "user_id": fb.user_id,
            "content": fb.content,
            "images": fb.image_urls,
            "latitude": fb.latitude,
            "longitude": fb.longitude,
            "address": fb.address,
            "date": fb.date,
            "status": fb.status
        })

    return jsonify(data), 200



# ==========================================
# 3. API nhân viên cập nhật xử lý phản ánh
# ==========================================
@feedback_api.route("/feedback/handling", methods=["POST"])
def handle_feedback():
    try:
        id = str(uuid.uuid4())[:20]
        feedback_id = request.form.get("feedback_id")
        employee_id = request.form.get("employee_id")
        status = request.form.get("status")
        note = request.form.get("note")

        attachment = request.files.get("attachment")
        filename = None

        if attachment:
            filename = f"{id}_{attachment.filename}"
            attachment.save(os.path.join(UPLOAD_FOLDER, filename))

        handling = FeedbackHandling(
            id=id,
            feedback_id=feedback_id,
            employee_id=employee_id,
            status=status,
            note=note,
            attachment_url=filename
        )

        # Cập nhật trạng thái tổng của Feedback
        fb = Feedback.query.get(feedback_id)
        fb.status = status

        db.session.add(handling)
        db.session.commit()

        return jsonify({"message": "updated"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
