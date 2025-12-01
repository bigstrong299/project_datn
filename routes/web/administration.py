from flask import Blueprint, render_template, request, redirect, url_for, flash
from models.database import db
from models.infrastructure import Employee, Account, User # Import models vừa tạo
from werkzeug.security import generate_password_hash # Để mã hóa mật khẩu
from sqlalchemy import text

admin_bp = Blueprint('admin_administration', __name__)

@admin_bp.route('/administration', methods=['GET', 'POST'])
def administration():
    # --- XỬ LÝ POST (THÊM MỚI HOẶC CẬP NHẬT) ---
    if request.method == 'POST':
        try:
            emp_id = request.form.get('emp_id') # ID ẩn (nếu có là Sửa, không có là Thêm)
            
            # Dữ liệu chung từ Form
            name = request.form.get('name')
            phone = request.form.get('phone')
            position = request.form.get('position')
            role = request.form.get('role')

            if emp_id: 
                # === TRƯỜNG HỢP CẬP NHẬT (EDIT) ===
                emp = Employee.query.get(emp_id)
                if emp:
                    emp.name = name
                    emp.phone = phone
                    emp.position = position
                    emp.role = role
                    
                    # Nếu sửa thì mới lấy username/password từ form (nếu muốn đổi)
                    username = request.form.get('username')
                    password = request.form.get('password')
                    
                    acc = Account.query.filter_by(employee_id=emp_id).first()
                    if acc and username:
                        acc.username = username
                        if password: # Chỉ đổi pass nếu nhập mới
                            acc.password = generate_password_hash(password)
                    
                    flash('Cập nhật thông tin thành công!', 'success')
            else:
                # === TRƯỜNG HỢP THÊM MỚI (ADD) ===
                
                # 1. Sinh ID và Tạo Nhân viên
                emp_seq = db.session.execute(text("SELECT nextval('employees_id_seq')")).scalar()
                prefix_emp = 'QL' if role == 'admin' else 'NV'
                new_emp_id = f"{prefix_emp}{str(emp_seq).zfill(6)}"

                new_emp = Employee(
                    id=new_emp_id,
                    name=name, 
                    phone=phone, 
                    position=position, 
                    role=role
                )
                db.session.add(new_emp)
                
                # --- QUAN TRỌNG NHẤT: THÊM DÒNG NÀY ---
                db.session.flush() 
                # Lệnh này ép Python gửi ngay dữ liệu Nhân viên xuống DB 
                # để DB ghi nhận sự tồn tại của ID này trước khi tạo Account.
                
                # 2. Sinh ID và Tạo Tài khoản
                acc_seq = db.session.execute(text("SELECT nextval('accounts_id_seq')")).scalar()
                new_acc_id = f"TK{str(acc_seq).zfill(6)}"

                default_password = "nv123456@"
                hashed_password = generate_password_hash(default_password)
                
                new_acc = Account(
                    id=new_acc_id,
                    employee_id=new_emp_id, # Lúc này DB đã biết new_emp_id tồn tại nhờ lệnh flush() ở trên
                    username=new_emp_id,
                    password=hashed_password
                )
                db.session.add(new_acc)
                
                flash(f'Thêm thành công! Tài khoản: {new_emp_id} / MK: {default_password}', 'success')
            
            db.session.commit()
            
        except Exception as e:
            db.session.rollback()
            flash(f'Lỗi hệ thống: {str(e)}', 'danger')
            print(f"DEBUG ERROR: {e}")
        
        return redirect(url_for('admin_administration.administration'))

    # --- XỬ LÝ GET (HIỂN THỊ) ---
    try:
        employees = Employee.query.order_by(Employee.id.desc()).all()
        users = User.query.all()
        accounts = Account.query.all()

        stats = {
            'total_employees': len(employees),
            'total_users': len(users),
            'total_accounts': len(accounts)
        }
    except:
        stats = {'total_employees': 0, 'total_users': 0, 'total_accounts': 0}
        employees, users, accounts = [], [], []

    return render_template('administration.html', 
                           stats=stats, 
                           employees=employees, 
                           users=users, 
                           accounts=accounts)