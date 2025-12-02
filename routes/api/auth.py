import os
from flask import Blueprint, current_app, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token
from models.infrastructure import User, Account, Employee
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
             return jsonify({"error": "Sai mật khẩu hoặc tên đăng nhập"}), 400
             
        account = dict(account_row._mapping)

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

        effective_user_id = account['user_id'] if account['user_id'] else account.get('employee_id')

        return jsonify({
            "message": "Login successful",
            "access_token": access_token,
            "account_id": account['id'],
            "username": account['username'],
            
            # QUAN TRỌNG: Trả về ID thực tế vào key 'user_id' để Flutter đọc được
            "user_id": effective_user_id, 
            
            # Gửi thêm field type để Flutter dễ phân biệt (Optional)
            "role_type": "employee" if account.get('employee_id') else "user"
        }), 200

    except Exception as e:
        print(f"❌ LỖI SERVER: {str(e)}")
        return jsonify({"error": str(e)}), 500
    
@auth_bp.route('/user/<id>', methods=['GET'])
def get_profile(id):
    try:
        # 1. Ưu tiên kiểm tra trong bảng NHÂN VIÊN trước
        employee = Employee.query.get(id)
        if employee:
            # Tìm username trong account
            acc = Account.query.filter_by(employee_id=id).first()
            return jsonify({
                "id": employee.id,
                "name": employee.name,
                "phone": employee.phone,
                "position": employee.position,
                "role": employee.role, # 'admin' hoặc 'staff'
                "username": acc.username if acc else "",
                "type": "employee" # Cờ để Flutter nhận biết
            }), 200

        # 2. Nếu không phải nhân viên, kiểm tra bảng USER
        user = User.query.get(id)
        if user:
            acc = Account.query.filter_by(user_id=id).first()
            return jsonify({
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "phone": user.phone,
                "avatar": user.avatar,
                "role": "user", # Gán cứng role là user
                "type": "user"
            }), 200

        return jsonify({"error": "ID không tồn tại"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# Cấu hình folder upload avatar
UPLOAD_FOLDER_AVATAR = 'static/uploads/avatars'

@auth_bp.route('/user/update', methods=['POST']) # Dùng POST để gửi form-data
def update_user_profile():
    try:
        user_id = request.form.get('user_id')
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')

        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        # 1. Cập nhật thông tin cơ bản
        if name: user.name = name
        if email: user.email = email
        if phone: user.phone = phone

        # 2. Xử lý Avatar (nếu có gửi lên)
        if 'avatar' in request.files:
            file = request.files['avatar']
            if file and file.filename != '':
                # Tạo tên file an toàn
                filename = secure_filename(f"avatar_{user_id}_{int(datetime.datetime.now().timestamp())}.jpg")
                
                # Tạo folder nếu chưa có
                save_path = os.path.join(current_app.root_path, UPLOAD_FOLDER_AVATAR)
                os.makedirs(save_path, exist_ok=True)
                
                # Lưu file
                file.save(os.path.join(save_path, filename))
                
                # Lưu đường dẫn vào DB
                user.avatar = f"/{UPLOAD_FOLDER_AVATAR}/{filename}"

        db.session.commit()

        return jsonify({
            "message": "Cập nhật thành công",
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "phone": user.phone,
                "avatar": user.avatar
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500