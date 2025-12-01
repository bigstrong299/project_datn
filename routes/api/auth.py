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

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.json
        password = data.get('password')
        username = data.get('username')
        email = data.get('email')

        if not password or (not username and not email):
            return jsonify({"error": "Missing info"}), 400

        account_row = None

        # 1. Tìm Account
        if username:
            account_row = db.session.execute(db.text(
                "SELECT * FROM accounts WHERE username = :u"
            ), {"u": username}).fetchone()
        else:
            # Tìm qua email phải join hoặc query 2 bước
            user_row = db.session.execute(db.text(
                "SELECT id FROM users WHERE email = :e"
            ), {"e": email}).fetchone()
            
            if user_row:
                # Chuyển user_row thành dict để lấy ID an toàn
                user_data = dict(user_row._mapping) 
                account_row = db.session.execute(db.text(
                    "SELECT * FROM accounts WHERE user_id = :uid"
                ), {"uid": user_data['id']}).fetchone()

        if not account_row:
            return jsonify({"error": "User not found"}), 400

        # --- KHẮC PHỤC LỖI Ở ĐÂY ---
        # Chuyển Row Object thành Dictionary Python chuẩn
        # Điều này giúp tránh lỗi account.password không tồn tại
        account = dict(account_row._mapping) 

        # Debug: In ra terminal để xem có password chưa
        print(f"🔍 DEBUG ACCOUNT: {account['username']}") 

        # Check password
        if not check_password_hash(account['password'], password):
            return jsonify({"error": "Incorrect password"}), 400

        # Tạo Token
        access_token = create_access_token(identity=account['user_id'])
        print(f"✅ TOKEN ĐÃ TẠO: {access_token}") # In ra để chắc chắn đã có token

        # Trả về JSON
        return jsonify({
            "message": "Login successful",
            "access_token": access_token,
            "account_id": account['id'],
            "username": account['username'],
            "user_id": account['user_id'],
            # Dùng .get() để tránh lỗi nếu database chưa có cột employee_id
            "employee_id": account.get('employee_id') 
        }), 200

    except Exception as e:
        print(f"❌ LỖI SERVER: {str(e)}") # In lỗi ra terminal nếu có
        return jsonify({"error": str(e)}), 500