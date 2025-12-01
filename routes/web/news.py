import os
import uuid
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, session
from werkzeug.utils import secure_filename
from models.database import db
from models.infrastructure import ForumPost, ForumCategory

news_bp = Blueprint('news', __name__)

# --- 1. TRANG QUẢN LÝ (Dashboard) ---
# Đường dẫn: /web/news -> Hiển thị bảng thống kê và danh sách
@news_bp.route('/news')
def manage():
    if 'logged_in' not in session:
        return redirect('/web/login')
        
    # 1. Lấy dữ liệu bài viết và danh mục
    posts = ForumPost.query.order_by(ForumPost.time_post.desc()).all()
    categories = ForumCategory.query.all()
    
    # 2. Tính toán thống kê (Đây là phần bị thiếu gây ra lỗi 'stats undefined')
    stats = {
        'total_posts': len(posts),
        'total_categories': len(categories),
        # Đếm bài viết thuộc danh mục 'Tin tức & Sự kiện' (nếu có)
        'news_count': ForumPost.query.join(ForumCategory).filter(ForumCategory.name == 'Tin tức & Sự kiện').count()
    }

    # Render file news_manage.html (File chứa giao diện dashboard)
    return render_template('news_create.html', 
                           posts=posts, 
                           categories=categories, 
                           stats=stats)

# --- 2. TRANG ĐĂNG BÀI MỚI ---
# Đường dẫn: /web/news/create
@news_bp.route('/news/create', methods=['GET', 'POST'])
def create_post():
    if 'logged_in' not in session:
        return redirect('/web/login')

    # Lấy danh sách danh mục để hiện trong thẻ <select>
    categories = ForumCategory.query.all()

    if request.method == 'POST':
        title = request.form.get('title')
        category_id = request.form.get('category_id')
        description = request.form.get('description')
        content = request.form.get('content')
        
        # Xử lý ảnh
        image_url = None
        if 'image' in request.files:
            file = request.files['image']
            if file.filename != '':
                filename = secure_filename(file.filename)
                unique_filename = f"{uuid.uuid4().hex[:8]}_{filename}"
                save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
                file.save(save_path)
                image_url = f"/static/uploads/{unique_filename}"

        try:
            new_post = ForumPost(
                id=uuid.uuid4().hex[:20],
                category_id=category_id,
                title=title,
                content=content,
                description=description,
                image=image_url
            )
            db.session.add(new_post)
            db.session.commit()
            
            flash('Đăng bài thành công!', 'success')
            # Đăng xong thì quay về trang quản lý (/web/news)
            return redirect(url_for('news.manage')) 
            
        except Exception as e:
            db.session.rollback()
            flash(f'Lỗi khi đăng bài: {str(e)}', 'error')

    # Render file news_create.html (File chứa form đăng bài)
    return render_template('news_post.html', categories=categories)

# --- 3. TRANG XEM TIN (Public - Dành cho người dân) ---
# Đường dẫn: /web/news/list
# @news_bp.route('/news/list')
# def index():
#     handbook_posts = ForumPost.query.join(ForumCategory).filter(
#         ForumCategory.name == 'Cẩm nang môi trường'
#     ).order_by(ForumPost.time_post.desc()).all()

#     news_posts = ForumPost.query.join(ForumCategory).filter(
#         ForumCategory.name == 'Tin tức & Sự kiện'
#     ).order_by(ForumPost.time_post.desc()).all()

#     about_post = ForumPost.query.join(ForumCategory).filter(
#         ForumCategory.name == 'Giới thiệu hệ thống'
#     ).order_by(ForumPost.time_post.desc()).first()

#     return render_template('news_list.html', 
#                            handbook_posts=handbook_posts,
#                            news_posts=news_posts,
#                            about_post=about_post)

# --- 4. TRANG CHI TIẾT BÀI VIẾT ---
@news_bp.route('/news/detail/<post_id>')
def detail(post_id):
    post = ForumPost.query.get_or_404(post_id)
    return render_template('news_create.html', post=post)