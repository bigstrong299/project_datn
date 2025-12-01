from flask import Blueprint, render_template, request, redirect, url_for, flash, g
from models.database import db
from models.infrastructure import Employee, Feedback, FeedbackHandling


feedback_bp = Blueprint('admin_feedback', __name__)

@feedback_bp.route('/feedback', methods=['GET', 'POST'])
def feedback():
    # --- XỬ LÝ (POST) ---
    if request.method == 'POST':
        try:
            feedback_id = request.form.get('feedback_id')
            note = request.form.get('note')
            
            # 1. Tìm feedback
            fb = Feedback.query.get(feedback_id)
            if fb:
                # 2. Cập nhật trạng thái
                fb.status = 'Đã xử lý'
                
                # 3. Lưu lịch sử xử lý
                # Lấy ID nhân viên từ session đăng nhập (g.user)
                current_emp_id = g.user.employee.id if (g.user and g.user.employee) else None
                
                handling = FeedbackHandling(
                    feedback_id=feedback_id,
                    employee_id=current_emp_id,
                    note=note
                )
                db.session.add(handling)
                db.session.commit()
                flash('Đã xử lý phản ánh thành công!', 'success')
            else:
                flash('Không tìm thấy phản ánh!', 'danger')
                
        except Exception as e:
            db.session.rollback()
            flash(f'Lỗi xử lý: {str(e)}', 'danger')
            
        return redirect(url_for('admin_feedback.feedback'))

    # --- HIỂN THỊ (GET) ---
    # Phân loại danh sách để hiển thị ra 2 Tab
    pending_list = Feedback.query.filter_by(status='Chờ xử lý').order_by(Feedback.date.desc()).all()
    processed_list = Feedback.query.filter_by(status='Đã xử lý').order_by(Feedback.date.desc()).all()

    return render_template('feedback.html', 
                           pending_list=pending_list, 
                           processed_list=processed_list)