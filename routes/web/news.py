import os
import uuid
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from werkzeug.utils import secure_filename
from models.database import db
from models.infrastructure import ForumPost, ForumCategory

# Khởi tạo Blueprint
news_bp = Blueprint('admin_news', __name__)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# --- 1. TRANG QUẢN LÝ ---
@news_bp.route('/news')
def manage():
    if 'logged_in' not in session or session.get('role') != 'admin':
        return redirect('/web/login')
        
    posts = ForumPost.query.order_by(ForumPost.time_post.desc()).all()
    categories = ForumCategory.query.all()
    
    stats = {
        'total_posts': len(posts),
        'news_count': ForumPost.query.join(ForumCategory).filter(ForumCategory.name == 'Tin tức & Sự kiện').count(),
        'total_categories': len(categories)
    }
    return render_template('news_create.html', posts=posts, categories=categories, stats=stats)

# --- 2. TẠO BÀI VIẾT MỚI ---
@news_bp.route('/news/create', methods=['GET', 'POST'])
def create_post():
    if 'logged_in' not in session or session.get('role') != 'admin':
        return redirect('/web/login')

    categories = ForumCategory.query.all()

    if request.method == 'POST':
        try:
            title = request.form.get('title')
            category_id = request.form.get('category_id')
            description = request.form.get('description')
            content = request.form.get('content')
            status = request.form.get('status', 'draft')

            image_path = ""
            if 'image' in request.files:
                file = request.files['image']
                if file and file.filename != '' and allowed_file(file.filename):
                    filename = secure_filename(f"{uuid.uuid4().hex[:8]}_{file.filename}")
                    file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                    image_path = f"/static/uploads/{filename}"

            new_post = ForumPost(
                id=uuid.uuid4().hex[:20],
                category_id=category_id,
                title=title,
                content=content,
                description=description,
                image=image_path,
                status=status
            )
            
            db.session.add(new_post)
            db.session.commit()
            flash('Đăng bài thành công!', 'success')
            return redirect(url_for('admin_news.manage'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Lỗi: {str(e)}', 'error')

    # post=None để báo hiệu là đang tạo mới
    return render_template('news_post.html', categories=categories, post=None)

# --- 3. CHỈNH SỬA BÀI VIẾT ---
@news_bp.route('/news/edit/<post_id>', methods=['GET', 'POST'])
def edit_post(post_id):
    if 'logged_in' not in session or session.get('role') != 'admin':
        return redirect('/web/login')

    post = ForumPost.query.get_or_404(post_id)
    categories = ForumCategory.query.all()

    if request.method == 'POST':
        try:
            post.title = request.form.get('title')
            post.category_id = request.form.get('category_id')
            post.description = request.form.get('description')
            post.content = request.form.get('content')
            post.status = request.form.get('status')
            
            if 'image' in request.files:
                file = request.files['image']
                if file and file.filename != '' and allowed_file(file.filename):
                    filename = secure_filename(f"{uuid.uuid4().hex[:8]}_{file.filename}")
                    file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                    post.image = f"/static/uploads/{filename}"

            db.session.commit()
            flash('Cập nhật thành công!', 'success')
            return redirect(url_for('admin_news.manage'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Lỗi cập nhật: {str(e)}', 'error')

    # Truyền post vào để form tự điền dữ liệu cũ
    return render_template('news_post.html', categories=categories, post=post)

# --- 4. XÓA BÀI VIẾT (Chỉ giữ lại 1 hàm này duy nhất) ---
@news_bp.route('/news/delete/<post_id>')
def delete_post(post_id):
    if 'logged_in' not in session or session.get('role') != 'admin':
        return redirect('/web/login')
        
    post = ForumPost.query.get_or_404(post_id)
    try:
        db.session.delete(post)
        db.session.commit()
        flash('Đã xóa bài viết', 'success')
    except Exception as e:
        flash(f'Lỗi xóa: {str(e)}', 'error')
        
    return redirect(url_for('admin_news.manage'))