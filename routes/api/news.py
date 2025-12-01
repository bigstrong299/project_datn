from flask import Blueprint, jsonify, request, current_app
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
            
            # Lấy URL gốc của server hiện tại (Ví dụ: https://project-datn.onrender.com)
            # rstrip('/') để bỏ dấu gạch chéo thừa ở cuối nếu có
            current_host = request.host_url.rstrip('/')
            
            # Render thường chạy sau proxy, nên đôi khi host_url trả về http thay vì https
            # Dòng này ép nó thành https để App load được (Android cấm http thường)
            if 'onrender.com' in current_host and current_host.startswith('http:'):
                current_host = current_host.replace('http:', 'https:')

            # TRƯỜNG HỢP 1: Ảnh đường dẫn tương đối (/static/uploads/...)
            if src.startswith('/static'):
                full_url = current_host + src
                print(f"✅ [LIVE] Fix ảnh relative: {full_url}")
                return full_url

            # TRƯỜNG HỢP 2: Dữ liệu cũ trong DB lỡ lưu 'localhost' hoặc '127.0.0.1'
            # (Do lúc bạn đăng bài bạn đang chạy máy local)
            if '127.0.0.1' in src or 'localhost' in src:
                # Cắt bỏ phần domain cũ, chỉ lấy từ /static trở đi
                if '/static' in src:
                    clean_path = '/static' + src.split('/static')[1]
                    full_url = current_host + clean_path
                    print(f"✅ [LIVE] Fix ảnh localhost cũ: {full_url}")
                    return full_url

            # TRƯỜNG HỢP 3: Ảnh online (Imgur, Google...) hoặc Base64
            return src 
            
    except Exception as e:
        print(f"❌ [LIVE] Lỗi trích xuất: {e}")
    
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