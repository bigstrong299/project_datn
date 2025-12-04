import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from models.database import db
from models.infrastructure import Employee, Feedback, FeedbackHandling

feedback_bp = Blueprint('admin_feedback', __name__)

@feedback_bp.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if request.method == 'POST':
        action = request.form.get('action')
        feedback_id = request.form.get('feedback_id')
        
        # 1. ADMIN GIAO VIỆC -> TẠO DÒNG LỊCH SỬ ĐẦU TIÊN
        if action == 'assign':
            try:
                employee_ids = request.form.getlist('employee_ids[]')
                admin_note = request.form.get('admin_note')
                
                fb = Feedback.query.get(feedback_id)
                if fb:
                    fb.status = 'Đã phân công' # Cập nhật trạng thái hiện tại
                    
                    for emp_id in employee_ids:
                        # INSERT DÒNG MỚI
                        new_handling = FeedbackHandling(
                            feedback_id=feedback_id,
                            employee_id=emp_id,
                            status='Chờ nhận việc', # Trạng thái khởi đầu của nhân viên
                            note=f"[Admin giao]: {admin_note}",
                            time_process=datetime.now()
                        )
                        db.session.add(new_handling)
                    
                    db.session.commit()
                    flash('Đã giao việc!', 'success')

            except Exception as e:
                db.session.rollback()
                flash(f'Lỗi: {e}', 'danger')

        # 2. ADMIN DUYỆT HOÀN TẤT -> TẠO DÒNG LỊCH SỬ CUỐI CÙNG
        elif action == 'complete':
            try:
                completion_note = request.form.get('completion_note')
                fb = Feedback.query.get(feedback_id)
                
                if fb:
                    fb.status = 'Hoàn tất' # Trạng thái cuối cùng
                    
                    # Lấy nhân viên làm cuối cùng để ghi nhận
                    last_log = FeedbackHandling.query.filter_by(feedback_id=feedback_id).order_by(FeedbackHandling.time_process.desc()).first()
                    last_emp = last_log.employee_id if last_log else None

                    # INSERT DÒNG MỚI
                    closing_log = FeedbackHandling(
                        feedback_id=feedback_id,
                        employee_id=last_emp,
                        status='Hoàn tất',
                        note=f"[Admin duyệt]: {completion_note}",
                        time_process=datetime.now()
                    )
                    db.session.add(closing_log)
                    
                    db.session.commit()
                    flash('Đã duyệt hoàn tất!', 'success')

            except Exception as e:
                db.session.rollback()
                flash(f'Lỗi: {e}', 'danger')

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
@feedback_bp.route('/feedback/<feedback_id>/detail', methods=['GET'])
def get_feedback_detail(feedback_id):
    try:
        feedback = Feedback.query.get(feedback_id)
        if not feedback:
            return jsonify({'error': 'Không tìm thấy'}), 404
        
        # Lấy danh sách nhân viên liên quan và trạng thái của họ
        assigned_employees = []
        handlings = FeedbackHandling.query.filter_by(feedback_id=feedback_id).all()
        
        # Tìm xem ai là người đang xử lý chính (người có status khác 'Chờ nhận việc')
        active_handler = None
        
        for h in handlings:
            emp_info = {
                'id': h.employee.id,
                'name': h.employee.name,
                'position': h.employee.position,
                'status': h.status, # Quan trọng: 'Chờ nhận việc', 'Đang xử lý', 'Đã xử lý'
                'note': h.note,
                'attachment_url': h.attachment_url
            }
            assigned_employees.append(emp_info)
            
            # Nếu nhân viên này đang làm hoặc đã làm xong -> Ghi nhận là người xử lý chính
            if h.status in ['Đang xử lý', 'Đã xử lý', 'Đã hoàn thành']:
                active_handler = emp_info

        return jsonify({
            'id': feedback.id,
            'user_name': feedback.user.name if feedback.user else 'Cư dân ẩn danh',
            'content': feedback.content,
            'address': feedback.address,
            'latitude': feedback.latitude,
            'longitude': feedback.longitude,
            'image_urls': feedback.image_urls or [],
            'date': feedback.date.strftime('%d/%m/%Y %H:%M'),
            'status': feedback.status,
            'assigned_employees': assigned_employees,
            'active_handler': active_handler # Trả về người đang làm (nếu có)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500