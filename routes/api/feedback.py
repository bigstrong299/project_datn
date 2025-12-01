from flask import Blueprint, request, jsonify
from models.infrastructure import db, Feedback, FeedbackHandling
import uuid, os, json

feedback_api = Blueprint("feedback_api", __name__)

UPLOAD_FOLDER = "static/feedback_images"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ==============================
# 1. API tạo Feedback
# ==============================
@feedback_api.route("/feedback", methods=["POST"])
def create_feedback():
    try:
        id = str(uuid.uuid4())[:20]

        user_id = request.form.get("user_id")
        content = request.form.get("content")
        latitude = float(request.form.get("latitude", 0))
        longitude = float(request.form.get("longitude", 0))
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
            image=json.dumps(saved_images),
            latitude=latitude,
            longitude=longitude,
            address=address,
            status="Chờ xử lý"
        )

        db.session.add(feedback)
        db.session.commit()

        return jsonify({"message": "success", "feedback_id": id}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500



# ==============================
# 2. API danh sách Feedback
# ==============================
@feedback_api.route("/feedback", methods=["GET"])
def list_feedback():
    feedbacks = Feedback.query.order_by(Feedback.date.desc()).all()
    data = []

    for fb in feedbacks:
        data.append({
            "id": fb.id,
            "user_id": fb.user_id,
            "content": fb.content,
            "images": json.loads(fb.image) if fb.image else [],
            "latitude": fb.latitude,
            "longitude": fb.longitude,
            "address": fb.address,
            "date": fb.date.isoformat(),
            "status": fb.status
        })

    return jsonify(data), 200



# ==========================================
# 3. API nhân viên xử lý phản ánh
# ==========================================
@feedback_api.route("/feedback/handling", methods=["POST"])
def handle_feedback():
    try:
        id = str(uuid.uuid4())[:20]

        feedback_id = request.form.get("feedback_id")
        employee_id = request.form.get("employee_id")
        note = request.form.get("note")

        fb = Feedback.query.get(feedback_id)
        if not fb:
            return jsonify({"error": "Feedback not found"}), 404

        # cập nhật trạng thái
        fb.status = "Đã xử lý"

        handling = FeedbackHandling(
            id=id,
            feedback_id=feedback_id,
            employee_id=employee_id,
            note=note
        )

        db.session.add(handling)
        db.session.commit()

        return jsonify({"message": "updated"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
