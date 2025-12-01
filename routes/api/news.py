from flask import Blueprint, jsonify, request, current_app
from models.database import db
from models.infrastructure import ForumPost, ForumCategory
from bs4 import BeautifulSoup

news_api_bp = Blueprint('api_news', __name__)

def extract_first_image(html_content):
    if not html_content:
        return ""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        img_tag = soup.find('img')
        
        if img_tag and img_tag.get('src'):
            src = img_tag['src']
            
            # --- LOGIC FIX ẢNH MỚI ---
            
            # Trường hợp 1: Ảnh tương đối (/static/...) -> Phải nối thêm host
            if src.startswith('/static'):
                base_url = request.host_url.rstrip('/') # VD: http://10.0.2.2:5000
                
                # Fix cho Android Emulator: Nếu server nhận là localhost, ép về 10.0.2.2
                # (Chỉ dùng khi debug local, khi deploy thì request.host_url sẽ đúng)
                if '127.0.0.1' in base_url or 'localhost' in base_url:
                     # Kiểm tra xem request đến từ đâu, nếu từ Android Emulator thì host header thường khác
                     # Nhưng để chắc ăn, ta cứ ép về 10.0.2.2 cho môi trường dev
                     base_url = base_url.replace('127.0.0.1', '10.0.2.2').replace('localhost', '10.0.2.2')

                return base_url + src

            # Trường hợp 2: Ảnh tuyệt đối nhưng bị dính localhost cũ trong DB
            if '127.0.0.1' in src or 'localhost' in src:
                # Tách lấy phần đuôi /static...
                if '/static' in src:
                    part = src.split('/static')[1]
                    clean_path = '/static' + part
                    
                    # Lấy host hiện tại để nối vào
                    base_url = request.host_url.rstrip('/')
                    if '127.0.0.1' in base_url or 'localhost' in base_url:
                        base_url = base_url.replace('127.0.0.1', '10.0.2.2').replace('localhost', '10.0.2.2')
                        
                    return base_url + clean_path

            # Trường hợp 3: Ảnh online (http...) hoặc Base64 -> Giữ nguyên
            return src

    except Exception as e:
        print(f"Lỗi trích xuất ảnh: {e}")
    return ""

@news_api_bp.route('/news', methods=['GET'])
def get_news_api():
    try:
        # ... (Phần code query giữ nguyên) ...
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
            image_url = extract_first_image(post.content)

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