from flask import Blueprint, jsonify, request
from models.database import db
from models.infrastructure import ForumPost, ForumCategory, User # Import thêm User để lấy tên tác giả

news_api_bp = Blueprint('api_news', __name__)

# URL API sẽ là: http://ip:8000/news
# Method: GET
@news_api_bp.route('/news', methods=['GET'])
def get_news_api():
    try:
        # 1. Lấy tham số loại tin tức (nếu muốn lọc sau này)
        # Ví dụ: /news?type=handbook sẽ lấy cẩm nang
        category_type = request.args.get('type', default='news') 

        # 2. Xác định tên danh mục cần lấy
        target_category = 'Tin tức & Sự kiện'
        if category_type == 'handbook':
            target_category = 'Cẩm nang môi trường'
        elif category_type == 'about':
            target_category = 'Giới thiệu hệ thống'

        # 3. Query Database (Join User để lấy tên tác giả)
        # Tương đương: SELECT p.*, u.name FROM forum_posts p JOIN categories c ... JOIN users u ...
        query = db.session.query(ForumPost, User.name.label("author_name")) \
            .join(ForumCategory, ForumPost.category_id == ForumCategory.id) \
            .join(User, ForumPost.user_id == User.id) \
            .filter(ForumCategory.name == target_category) \
            .order_by(ForumPost.time_post.desc())

        posts = query.all()

        # 4. Chuyển đổi dữ liệu sang list Dictionary (JSON)
        result_list = []
        for post, author_name in posts:
            result_list.append({
                "id": post.id,
                "title": post.title,
                "description": post.description if post.description else "", # Xử lý nếu null
                "content": post.content,
                "author": author_name if author_name else "Ban quản trị",
                # Chuyển ngày giờ sang chuỗi ISO 8601 để Flutter dễ parse
                "time_post": post.time_post.isoformat() if post.time_post else "",
                # Nếu chưa có ảnh thật, trả về rỗng để Flutter hiện ảnh mặc định
                "image": "" 
            })

        # 5. Trả về JSON chuẩn format mà Flutter đã viết
        return jsonify({
            "success": True,
            "data": result_list
        }), 200

    except Exception as e:
        print(f"❌ Lỗi API News: {str(e)}")
        return jsonify({
            "success": False,
            "message": "Lỗi server: " + str(e)
        }), 500