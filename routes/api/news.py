from flask import Blueprint, jsonify, request
from models.database import db
from models.infrastructure import ForumPost, ForumCategory
from bs4 import BeautifulSoup # type: ignore

news_api_bp = Blueprint('api_news', __name__)

# --- HÀM TRÍCH XUẤT ẢNH THÔNG MINH ---
def extract_first_image(html_content):
    if not html_content:
        return ""
    try:
        # Dùng html.parser (có sẵn trong Python, không cần lxml để tránh lỗi)
        soup = BeautifulSoup(html_content, 'html.parser')
        img_tag = soup.find('img')
        
        if img_tag and img_tag.get('src'):
            src = img_tag['src']
            
            # XỬ LÝ QUAN TRỌNG: Nếu là ảnh nội bộ (bắt đầu bằng /static...), 
            # phải nối thêm domain server vào trước.
            if src.startswith('/'):
                # request.host_url sẽ tự lấy http://ip:port hiện tại
                base_url = request.host_url.rstrip('/')
                return base_url + src
            
            return src # Nếu là link online (http...) hoặc base64 thì giữ nguyên
    except Exception as e:
        print(f"Lỗi trích xuất ảnh: {e}")
    return ""

@news_api_bp.route('/news', methods=['GET'])
def get_news_api():
    try:
        category_type = request.args.get('type', default='news') 
        target_category = 'Tin tức & Sự kiện'
        if category_type == 'handbook':
            target_category = 'Cẩm nang môi trường'
        elif category_type == 'about':
            target_category = 'Giới thiệu hệ thống'

        query = db.session.query(ForumPost) \
            .join(ForumCategory, ForumPost.category_id == ForumCategory.id) \
            .filter(ForumCategory.name == target_category) \
            .order_by(ForumPost.time_post.desc())

        posts = query.all()

        result_list = []
        for post in posts:
            # Lấy ảnh bìa chuẩn
            image_url = extract_first_image(post.content)
            
            # Nếu bài viết không có ảnh nào, dùng ảnh mặc định của app
            # Bạn có thể để rỗng để App tự xử lý placeholder
            if not image_url: 
                image_url = "" 

            result_list.append({
                "id": post.id,
                "title": post.title,
                "description": post.description if post.description else "", 
                "content": post.content,
                "time_post": post.time_post.isoformat() if post.time_post else "",
                "image": image_url 
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