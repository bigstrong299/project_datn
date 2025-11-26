# backend/app/routes/api/auth.py
from flask import Blueprint, request, jsonify
from app import db
from app.models.user import User
from flask_jwt_extended import create_access_token
from sqlalchemy import or_  # <--- QUAN TRỌNG: Nhớ thêm dòng này

auth_bp = Blueprint('auth', __name__)

# --- 1. ĐĂNG KÝ (Cho phép null các trường phụ) ---
@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    # Chỉ bắt buộc 3 trường này
    if not all(k in data for k in ('username', 'password', 'email')):
         return jsonify({'message': 'Thiếu thông tin: username, email hoặc password'}), 400

    # Check trùng
    if User.query.filter((User.username == data['username']) | (User.email == data['email'])).first():
        return jsonify({'message': 'Username hoặc Email đã tồn tại'}), 400

    # Tạo user (full_name và phone dùng .get() để nếu không có thì nó tự là None/Null)
    new_user = User(
        username=data['username'],
        email=data['email'],
        full_name=data.get('full_name'), # Có thể null
        phone=data.get('phone')          # Có thể null
    )
    new_user.set_password(data['password'])
    
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({'message': 'Đăng ký thành công'}), 201

# --- 2. ĐĂNG NHẬP (Chấp nhận cả Username hoặc Email) ---
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    # Biến này chứa text người dùng nhập (có thể là username, có thể là email)
    login_input = data.get('username') 
    password = data.get('password')

    if not login_input or not password:
        return jsonify({'message': 'Vui lòng nhập tài khoản và mật khẩu'}), 400
    
    # Logic tìm kiếm: Username khớp HOẶC Email khớp
    user = User.query.filter(
        or_(
            User.username == login_input,
            User.email == login_input
        )
    ).first()
    
    if user and user.check_password(password):
        access_token = create_access_token(identity=user.id)
        return jsonify({
            'message': 'Login thành công',
            'access_token': access_token,
            'user_id': user.id,
            'username': user.username,
            'full_name': user.full_name # Trả về thêm tên để hiển thị (nếu có)
        }), 200
        
    return jsonify({'message': 'Sai tài khoản hoặc mật khẩu'}), 401