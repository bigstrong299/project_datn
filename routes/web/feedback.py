from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from models.database import db
from models.infrastructure import Employee, Feedback, FeedbackHandling

feedback_bp = Blueprint('admin_feedback', __name__)

@feedback_bp.route('/feedback', methods=['GET', 'POST'])
def feedback():
    # [1] TẠO BIẾN GIỜ VIỆT NAM (Dùng chung)
    # Lấy giờ UTC hiện tại của server + 7 tiếng = Giờ VN
    now_vn = datetime.utcnow() + timedelta(hours=7)

    if request.method == 'POST':
        action = request.form.get('action')
        feedback_id = request.form.get('feedback_id')
        
        # 1. ADMIN GIAO VIỆC
        if action == 'assign':
            try:
                employee_ids = request.form.getlist('employee_ids[]')
                admin_note = request.form.get('admin_note')
                
                fb = Feedback.query.get(feedback_id)
                if fb:
                    fb.status = 'Đã phân công'
                    
                    FeedbackHandling.query.filter_by(feedback_id=feedback_id).delete()

                    for emp_id in employee_ids:
                        new_handling = FeedbackHandling(
                            feedback_id=feedback_id,
                            employee_id=emp_id,
                            status='Chờ nhận việc',
                            note=f"[Admin giao]: {admin_note}",
                            # [SỬA] Lưu giờ VN trực tiếp vào Database
                            time_process=now_vn 
                        )
                        db.session.add(new_handling)
                    
                    db.session.commit()
                    flash('Đã giao việc!', 'success')

            except Exception as e:
                db.session.rollback()
                flash(f'Lỗi: {e}', 'danger')

        # 2. ADMIN DUYỆT HOÀN TẤT
        elif action == 'complete':
            try:
                completion_note = request.form.get('completion_note')
                fb = Feedback.query.get(feedback_id)
                
                if fb:
                    fb.status = 'Hoàn tất'
                    
                    last_log = FeedbackHandling.query.filter_by(feedback_id=feedback_id).order_by(FeedbackHandling.time_process.desc()).first()
                    last_emp = last_log.employee_id if last_log else None

                    closing_log = FeedbackHandling(
                        feedback_id=feedback_id,
                        employee_id=last_emp,
                        status='Hoàn tất',
                        note=f"[Admin duyệt]: {completion_note}",
                        # [SỬA] Lưu giờ VN trực tiếp vào Database
                        time_process=now_vn
                    )
                    db.session.add(closing_log)
                    
                    db.session.commit()
                    flash('Đã duyệt hoàn tất!', 'success')

            except Exception as e:
                db.session.rollback()
                flash(f'Lỗi: {e}', 'danger')

    # --- HIỂN THỊ (GET) ---
    pending_list = Feedback.query.filter_by(status='Chờ xử lý').order_by(Feedback.date.desc()).all()
    processing_list = Feedback.query.filter(Feedback.status.in_(['Đã phân công', 'Đang xử lý'])).order_by(Feedback.date.desc()).all()
    processed_list = Feedback.query.filter(Feedback.status.in_(['Đã xử lý', 'Hoàn tất'])).order_by(Feedback.date.desc()).all()
    staff_employees = Employee.query.filter_by(role='staff').all()

    return render_template('feedback.html', 
                           pending_list=pending_list,
                           processing_list=processing_list,
                           processed_list=processed_list,
                           employees=staff_employees,
                           timedelta=timedelta)

# --- API LẤY CHI TIẾT ---
@feedback_bp.route('/feedback/<feedback_id>/detail', methods=['GET'])
def get_feedback_detail(feedback_id):
    try:
        feedback = Feedback.query.get(feedback_id)
        if not feedback: return jsonify({'error': 'Not found'}), 404
        
        handling = FeedbackHandling.query.filter_by(feedback_id=feedback_id)\
                   .order_by(FeedbackHandling.time_process.desc()).first()
        
        employee_data = None
        report_images = []
        
        if handling and handling.employee:
            employee_data = {
                'id': handling.employee.id,
                'name': handling.employee.name,
                'position': handling.employee.position
            }
            if handling.attachment_url:
                report_images = handling.attachment_url

        # Với Feedback.date (Thời gian người dân gửi), thường được tạo tự động bởi DB (UTC).
        # Nên ta vẫn cần cộng 7 khi hiển thị.
        real_time = feedback.date + timedelta(hours=7) if feedback.date else datetime.now()

        return jsonify({
            'id': feedback.id,
            'user_name': feedback.user.name if feedback.user else 'Ẩn danh',
            'content': feedback.content,
            'address': feedback.address,
            'date': real_time.strftime('%d/%m/%Y %H:%M'),
            'image_urls': feedback.image_urls or [],
            'status': feedback.status,
            'latitude': feedback.latitude,
            'longitude': feedback.longitude,
            'assigned_employee': employee_data,
            'report_images': report_images,
            'handling_note': handling.note if handling else ''
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500