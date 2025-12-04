from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from models.database import db
from models.infrastructure import Employee, Feedback, FeedbackHandling

feedback_bp = Blueprint('admin_feedback', __name__)

@feedback_bp.route('/feedback', methods=['GET', 'POST'])
def feedback():
    # --- XỬ LÝ GIAO VIỆC (POST) ---
    if request.method == 'POST':
        action = request.form.get('action')
        
        # 1. TRƯỜNG HỢP GIAO VIỆC (Từ tab Chờ xử lý)
        if action == 'assign':
            try:
                feedback_id = request.form.get('feedback_id')
                employee_ids = request.form.getlist('employee_ids[]') # Nhận danh sách ID
                admin_note = request.form.get('admin_note')
                
                fb = Feedback.query.get(feedback_id)
                if fb:
                    # Cập nhật trạng thái Feedback -> Đã phân công
                    fb.status = 'Đã phân công'
                    
                    # Tạo handling cho TỪNG nhân viên được chọn
                    for emp_id in employee_ids:
                        handling = FeedbackHandling(
                            feedback_id=feedback_id,
                            employee_id=emp_id,
                            status='Chờ nhận việc', # Trạng thái con của nhân viên
                            note=admin_note
                        )
                        db.session.add(handling)
                    
                    db.session.commit()
                    flash(f'Đã giao việc cho {len(employee_ids)} nhân viên!', 'success')
                
            except Exception as e:
                db.session.rollback()
                flash(f'Lỗi giao việc: {str(e)}', 'danger')

        # 2. TRƯỜNG HỢP DUYỆT HOÀN TẤT (Từ tab Đã xử lý)
        elif action == 'complete':
            # ... (Giữ nguyên logic duyệt cũ nếu có) ...
            pass

        return redirect(url_for('admin_feedback.feedback'))

    # --- HIỂN THỊ (GET) ---
    # Lấy danh sách theo quy trình mới
    pending_list = Feedback.query.filter_by(status='Chờ xử lý').order_by(Feedback.date.desc()).all()
    
    # Tab Đang xử lý: Bao gồm "Đã phân công" (chờ NV nhận) và "Đang xử lý" (NV đang làm)
    processing_list = Feedback.query.filter(Feedback.status.in_(['Đã phân công', 'Đang xử lý'])).order_by(Feedback.date.desc()).all()
    
    # Tab Đã xử lý (Chờ Admin duyệt) & Hoàn tất
    processed_list = Feedback.query.filter(Feedback.status.in_(['Đã xử lý', 'Hoàn tất'])).order_by(Feedback.date.desc()).all()

    # Lấy danh sách nhân viên là STAFF để giao việc
    staff_employees = Employee.query.filter_by(role='staff').all()

    return render_template('feedback.html', 
                           pending_list=pending_list,
                           processing_list=processing_list,
                           processed_list=processed_list,
                           employees=staff_employees)

# --- API LẤY CHI TIẾT (Cho Modal) ---
@feedback_bp.route('/feedback/<id>/detail', methods=['GET'])
def get_feedback_detail(id):
    fb = Feedback.query.get(id)
    if fb:
        return jsonify({
            'id': fb.id,
            'user_name': fb.user.name if fb.user else 'Ẩn danh',
            'content': fb.content,
            'address': fb.address,
            'latitude': fb.latitude,
            'longitude': fb.longitude,
            'date': fb.date.strftime('%d/%m/%Y %H:%M'),
            'image_urls': fb.image_urls,
            'status': fb.status
        })
    return jsonify({'error': 'Not found'}), 404