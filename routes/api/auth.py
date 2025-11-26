from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token
from models.database import db
import uuid
from datetime import datetime


auth_bp = Blueprint('auth_bp', __name__)


# ============================
# 👉 REGISTER (Đăng ký tài khoản)
# ============================
@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.json
    
    required_fields = ['username', 'password', 'email']
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    username = data['username']
    email = data['email']
    password = data['password']

    # Check trùng email
    existing_email = db.session.execute(
        db.text("SELECT * FROM users WHERE email = :email"),
        {"email": email}
    ).fetchone()

    if existing_email:
        return jsonify({"error": "Email already exists"}), 400

    # Check trùng username
    existing_username = db.session.execute(
        db.text("SELECT * FROM accounts WHERE username = :username"),
        {"username": username}
    ).fetchone()

    if existing_username:
        return jsonify({"error": "Username already exists"}), 400

    # Tạo ID
    user_id = str(uuid.uuid4())[:20]
    account_id = str(uuid.uuid4())[:20]

    # Hash password
    hashed_password = generate_password_hash(password)

    # Insert vào bảng users
    db.session.execute(db.text("""
        INSERT INTO users (id, email)
        VALUES (:id, :email)
    """), {"id": user_id, "email": email})

    # Insert vào bảng accounts
    db.session.execute(db.text("""
        INSERT INTO accounts (id, user_id, username, password)
        VALUES (:id, :user_id, :username, :password)
    """), {
        "id": account_id,
        "user_id": user_id,
        "username": username,
        "password": hashed_password
    })

    db.session.commit()

    return jsonify({
        "message": "User registered successfully",
        "account_id": account_id,
        "user_id": user_id
    }), 201



# ============================
# 👉 LOGIN (Đăng nhập bằng username hoặc email)
# ============================
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.json

    required_fields = ['password']
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing password"}), 400

    password = data['password']
    username = data.get('username')
    email = data.get('email')

    if not username and not email:
        return jsonify({"error": "Provide username or email"}), 400

    # ==============================
    # 1) Tìm account qua username
    # ==============================
    if username:
        account = db.session.execute(db.text("""
            SELECT * FROM accounts WHERE username = :username
        """), {"username": username}).fetchone()
    else:
        # ==============================
        # 2) Tìm account qua email
        # ==============================
        user = db.session.execute(db.text("""
            SELECT * FROM users WHERE email = :email
        """), {"email": email}).fetchone()

        if not user:
            return jsonify({"error": "Invalid email or password"}), 400

        account = db.session.execute(db.text("""
            SELECT * FROM accounts WHERE user_id = :uid
        """), {"uid": user.id}).fetchone()

    if not account:
        return jsonify({"error": "Invalid username/email or password"}), 400

    # Check password xong:
    if not check_password_hash(account.password, password):
        return jsonify({"error": "Incorrect password"}), 400

    # --- THÊM ĐOẠN TẠO TOKEN NÀY ---
    # Tạo token chứa ID của user, hạn dùng mặc định (thường 15 phút)
    access_token = create_access_token(identity=account.user_id)
    
    return jsonify({
        "message": "Login successful",
        "access_token": access_token, # <--- QUAN TRỌNG: Phải trả về cái này Flutter mới chịu
        "account_id": account.id,
        "username": account.username,
        "user_id": account.user_id,
        "employee_id": account.employee_id
    }), 200