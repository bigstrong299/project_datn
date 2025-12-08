import re
from flask import Blueprint, jsonify, request
from models.database import db
from models.infrastructure import ForumPost, ForumCategory

# Khởi tạo Blueprint cho API
news_api_bp = Blueprint('news_api', __name__)

def extract_first_image(html_content):
    """Hàm trích xuất ảnh đầu tiên từ nội dung HTML nếu không có ảnh bìa"""
    if not html_content:
        return ""
    # Tìm thẻ <img src="..."> đầu tiên
    match = re.search(r'<img[^>]+src="([^">]+)"', html_content)
    if match:
        return match.group(1)
    return ""

@news_api_bp.route('/news', methods=['GET'])
def get_news_api():
    try:
        # 1. Lọc theo loại (News, Handbook, About)
        category_type = request.args.get('type', default='news')
        
        target_category = 'Tin tức & Sự kiện' # Mặc định
        if category_type == 'handbook':
            target_category = 'Cẩm nang môi trường'
        elif category_type == 'about':
            target_category = 'Giới thiệu hệ thống'

        # 2. Truy vấn DB
        query = db.session.query(ForumPost) \
            .join(ForumCategory, ForumPost.category_id == ForumCategory.id) \
            .filter(ForumCategory.name == target_category) \
            .filter(ForumPost.status == 'published') \
            .order_by(ForumPost.time_post.desc())

        posts = query.all()

        # 3. Chuẩn bị URL cơ sở (Base URL) để nối vào ảnh
        # Lấy host hiện tại (VD: http://192.168.1.5:5000)
        base_url = request.host_url.rstrip('/')
        
        # FIX QUAN TRỌNG: Nếu server chạy localhost, đổi thành 10.0.2.2 cho Android Emulator
        if '127.0.0.1' in base_url or 'localhost' in base_url:
            base_url = base_url.replace('127.0.0.1', '10.0.2.2').replace('localhost', '10.0.2.2')

        result_list = []
        for post in posts:
            final_image_url = ""

            # --- LOGIC XỬ LÝ ẢNH ---
            if post.image:
                db_img = post.image.strip()
                
                # Nếu là đường dẫn nội bộ (bắt đầu bằng /static) -> Nối IP vào
                if db_img.startswith('/'):
                    final_image_url = f"{base_url}{db_img}"
                
                # Nếu là Base64 hoặc Link Online (http) -> Giữ nguyên
                else:
                    final_image_url = db_img
            
            # Nếu chưa có ảnh bìa -> Tìm trong nội dung bài viết
            if not final_image_url:
                extracted = extract_first_image(post.content)
                if extracted:
                    if extracted.startswith('/'):
                        final_image_url = f"{base_url}{extracted}"
                    else:
                        final_image_url = extracted

            # Thêm vào danh sách kết quả
            result_list.append({
                "id": post.id,
                "title": post.title,
                "description": post.description if post.description else "",
                "content": post.content, # HTML content
                "time_post": post.time_post.isoformat() if post.time_post else "",
                "image": final_image_url # URL ảnh đầy đủ
            })

        return jsonify({
            "success": True,
            "data": result_list
        }), 200

    except Exception as e:
        print(f"News API Error: {e}")
        return jsonify({
            "success": False,
            "message": "Lỗi server: " + str(e)
        }), 500