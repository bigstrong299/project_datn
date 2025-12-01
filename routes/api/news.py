from flask import Blueprint, jsonify, request
from models.database import db
from models.infrastructure import ForumPost, ForumCategory
from bs4 import BeautifulSoup # type: ignore

news_api_bp = Blueprint('api_news', __name__)

# --- HÀM TRÍCH XUẤT & XỬ LÝ LINK ẢNH ---
def extract_first_image(html_content):
    if not html_content:
        return ""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        img_tag = soup.find('img')
        
        if img_tag and img_tag.get('src'):
            src = img_tag['src']
            
            # QUAN TRỌNG: Xử lý ảnh nội bộ (lưu trong static/uploads)
            if src.startswith('/static'):
                # request.host_url sẽ tự lấy địa chỉ IP server hiện tại (VD: http://192.168.1.5:5000/)
                # Kết quả nối lại: http://192.168.1.5:5000/static/uploads/hinh.jpg
                base_url = request.host_url.rstrip('/')
                return base_url + src
            
            return src # Nếu là ảnh online (https://...) thì giữ nguyên
    except Exception as e:
        print(f"Lỗi trích xuất ảnh: {e}")
    return ""

@news_api_bp.route('/news', methods=['GET'])
def get_news_api():
    try:
        # ... (giữ nguyên phần query database của bạn) ...
        query = db.session.query(ForumPost) \
            .join(ForumCategory, ForumPost.category_id == ForumCategory.id) \
            .order_by(ForumPost.time_post.desc())
        posts = query.all()

        result_list = []
        for post in posts:
            # 1. Lấy đường dẫn ảnh ĐẦY ĐỦ (có cả http://...)
            full_image_url = extract_first_image(post.content)

            result_list.append({
                "id": post.id,
                "title": post.title,
                "description": post.description if post.description else "",
                "content": post.content,
                "time_post": post.time_post.isoformat() if post.time_post else "",
                
                # 2. Trả về cho App
                "image": full_image_url 
            })

        return jsonify({"success": True, "data": result_list}), 200

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500