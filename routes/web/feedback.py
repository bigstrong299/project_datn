from flask import Blueprint, render_template, request, redirect, url_for, flash, g, jsonify
from models.database import db
from models.infrastructure import Employee, Feedback, FeedbackHandling, Account


feedback_bp = Blueprint('admin_feedback', __name__)

@feedback_bp.route('/feedback', methods=['GET', 'POST'])
def feedback():
    # --- XỬ LÝ GIAO VIỆC (POST) ---
    if request.method == 'POST':
        action = request.form.get('action')
        
        # Giao việc cho nhiều nhân viên
        if action == 'assign':
            try:
                feedback_id = request.form.get('feedback_id')
                employee_ids = request.form.getlist('employee_ids[]')  # Nhận danh sách nhiều nhân viên
                admin_note = request.form.get('admin_note')
                
                # 1. Tìm feedback
                fb = Feedback.query.get(feedback_id)
                if not fb:
                    flash('Không tìm thấy phản ánh!', 'danger')
                    return redirect(url_for('admin_feedback.feedback'))
                
                # 2. Kiểm tra có ít nhất 1 nhân viên được chọn
                if not employee_ids:
                    flash('Vui lòng chọn ít nhất một nhân viên!', 'warning')
                    return redirect(url_for('admin_feedback.feedback'))
                
                # 3. Cập nhật trạng thái feedback
                fb.status = 'Đã giao việc'
                
                # 4. Tạo bản ghi giao việc cho từng nhân viên
                employee_names = []
                for emp_id in employee_ids:
                    employee = Employee.query.get(emp_id)
                    if employee:
                        employee_names.append(employee.name)
                        
                        # Tạo ID mới cho handling (theo format FB_HXX)
                        last_handling = FeedbackHandling.query.order_by(FeedbackHandling.id.desc()).first()
                        if last_handling and last_handling.id.startswith('FB_H'):
                            last_num = int(last_handling.id.split('FB_H')[1])
                            new_id = f'FB_H{last_num + 1:02d}'
                        else:
                            new_id = 'FB_H01'
                        
                        handling = FeedbackHandling(
                            id=new_id,
                            feedback_id=feedback_id,
                            employee_id=emp_id,
                            note=admin_note or f'Đã giao việc cho {employee.name}',
                            status='Chờ nhận việc'  # Trạng thái chờ nhân viên nhận
                        )
                        db.session.add(handling)
                
                db.session.commit()
                
                if len(employee_names) > 1:
                    flash(f'Đã giao việc cho {len(employee_names)} nhân viên: {", ".join(employee_names)}', 'success')
                else:
                    flash(f'Đã giao việc cho {employee_names[0]} thành công!', 'success')
                
            except Exception as e:
                db.session.rollback()
                flash(f'Lỗi khi giao việc: {str(e)}', 'danger')
        
        # Duyệt hoàn tất (sau khi nhân viên đã xử lý xong)
        elif action == 'complete':
            try:
                feedback_id = request.form.get('feedback_id')
                completion_note = request.form.get('completion_note')
                
                fb = Feedback.query.get(feedback_id)
                if fb and fb.status == 'Đã xử lý':
                    # Cập nhật trạng thái cuối cùng
                    fb.status = 'Hoàn tất'
                    
                    # Cập nhật ghi chú duyệt của admin vào tất cả handling
                    handlings = FeedbackHandling.query.filter_by(feedback_id=feedback_id).all()
                    for handling in handlings:
                        if completion_note:
                            handling.note += f'\n[Admin duyệt]: {completion_note}'
                        handling.status = 'Đã hoàn thành'
                    
                    db.session.commit()
                    flash('Đã duyệt hoàn tất phản ánh!', 'success')
                else:
                    flash('Không thể duyệt phản ánh này!', 'warning')
                    
            except Exception as e:
                db.session.rollback()
                flash(f'Lỗi khi duyệt: {str(e)}', 'danger')
                
        return redirect(url_for('admin_feedback.feedback'))

    # --- HIỂN THỊ (GET) ---
    # Lấy danh sách nhân viên có role là staff
    staff_employees = Employee.query.filter_by(role='staff').all()
    
    # Áp dụng bộ lọc từ query params
    query = Feedback.query
    
    employee_filter = request.args.get('employee')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    status_filter = request.args.get('status')
    
    if employee_filter:
        query = query.join(FeedbackHandling).filter(FeedbackHandling.employee_id == employee_filter)
    
    if date_from:
        from datetime import datetime
        date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
        query = query.filter(Feedback.date >= date_from_obj)
    
    if date_to:
        from datetime import datetime
        date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
        query = query.filter(Feedback.date <= date_to_obj)
    
    if status_filter:
        if status_filter == 'pending':
            query = query.filter(Feedback.status == 'Chờ xử lý')
        elif status_filter == 'processing':
            query = query.filter(Feedback.status == 'Đã giao việc')
        elif status_filter == 'processed':
            query = query.filter(Feedback.status.in_(['Đã xử lý', 'Hoàn tất']))
    
    # Phân loại danh sách theo 3 trạng thái
    pending_list = Feedback.query.filter(Feedback.status == 'Chờ xử lý').order_by(Feedback.date.desc()).all()
    processing_list = Feedback.query.filter(Feedback.status == 'Đã giao việc').order_by(Feedback.date.desc()).all()
    processed_list = Feedback.query.filter(Feedback.status.in_(['Đã xử lý', 'Hoàn tất'])).order_by(Feedback.date.desc()).all()

    # Lấy danh sách nhân viên được giao cho mỗi feedback đang xử lý
    for feedback in processing_list:
        feedback.assigned_employees = FeedbackHandling.query.filter_by(
            feedback_id=feedback.id
        ).all()

    return render_template('feedback.html', 
                           pending_list=pending_list,
                           processing_list=processing_list,
                           processed_list=processed_list,
                           employees=staff_employees)

# API endpoint để lấy chi tiết feedback (dùng cho modal)
@feedback_bp.route('/feedback/<feedback_id>/detail', methods=['GET'])
def get_feedback_detail(feedback_id):
    try:
        feedback = Feedback.query.get(feedback_id)
        if not feedback:
            return jsonify({'error': 'Không tìm thấy phản ánh'}), 404
        
        # Lấy thông tin nhân viên được giao (nếu có)
        assigned_employees = []
        handlings = FeedbackHandling.query.filter_by(feedback_id=feedback_id).all()
        for handling in handlings:
            if handling.employee:
                assigned_employees.append({
                    'id': handling.employee.id,
                    'name': handling.employee.name,
                    'status': handling.status
                })
        
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
            'assigned_employees': assigned_employees
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500