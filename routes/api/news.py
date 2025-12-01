from flask import Blueprint, jsonify, request
from models.database import db
# Bỏ import User vì không dùng nữa
from models.infrastructure import ForumPost, ForumCategory
from bs4 import BeautifulSoup # Import thư viện xử lý HTML

news_api_bp = Blueprint('api_news', __name__)

# --- HÀM HỖ TRỢ: Trích xuất ảnh đầu tiên từ HTML ---
def extract_first_image(html_content):
    if not html_content:
        return ""
    try:
        # Dùng BeautifulSoup để phân tích HTML
        soup = BeautifulSoup(html_content, 'lxml')
        # Tìm thẻ <img> đầu tiên
        img_tag = soup.find('img')
        if img_tag and img_tag.get('src'):
            # Trả về đường dẫn ảnh (src)
            return img_tag['src']
    except Exception as e:
        print(f"Lỗi trích xuất ảnh: {e}")
    # Không tìm thấy thì trả về rỗng
    return ""

# Method: GET
@news_api_bp.route('/news', methods=['GET'])
def get_news_api():
    try:
        # 1. Lấy tham số loại tin tức
        category_type = request.args.get('type', default='news') 

        # 2. Xác định tên danh mục cần lấy
        target_category = 'Tin tức & Sự kiện'
        if category_type == 'handbook':
            target_category = 'Cẩm nang môi trường'
        elif category_type == 'about':
            target_category = 'Giới thiệu hệ thống'

        # 3. Query Database
        query = db.session.query(ForumPost) \
            .join(ForumCategory, ForumPost.category_id == ForumCategory.id) \
            .filter(ForumCategory.name == target_category) \
            .order_by(ForumPost.time_post.desc())

        posts = query.all()

        # 4. Chuyển đổi dữ liệu sang JSON
        result_list = []
        for post in posts:
            # ===> GỌI HÀM TRÍCH XUẤT ẢNH Ở ĐÂY <===
            first_image_src = extract_first_image(post.content)

            result_list.append({
                "id": post.id,
                "title": post.title,
                "description": post.description if post.description else "", 
                "content": post.content,
                "author": "Ban quản trị",
                "time_post": post.time_post.isoformat() if post.time_post else "",
                # Sử dụng kết quả vừa trích xuất được
                "image": first_image_src 
            })

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