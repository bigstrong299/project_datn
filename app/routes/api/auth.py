from flask import Blueprint, request, jsonify, current_app
from werkzeug.security import generate_password_hash, check_password_hash

bp = Blueprint("auth", __name__)

# NOTE: This is a minimal example. Replace with real DB queries and JWT.
@bp.route("/login", methods=["POST"])
def login():
    data = request.json or {}
    username = data.get("username")
    password = data.get("password")
    if username == "admin" and password == "admin":
        return jsonify({"token": "dev-token", "role": "admin"})
    return jsonify({"error": "invalid credentials"}), 401
