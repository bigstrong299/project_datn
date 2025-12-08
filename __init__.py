from flask import Flask
from .models.database import db
from config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # --- THÊM DÒNG NÀY VÀO ĐÂY ---
    # Cho phép upload tối đa 50MB (bao gồm cả ảnh Base64 và nội dung bài viết)
    app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024
    # -----------------------------

    db.init_app(app)

    # Register Blueprint
    from .routes.api.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    
    # (Lưu ý: Bạn nhớ đăng ký các Blueprint khác ở đây nếu chạy qua create_app, 
    # ví dụ: admin_news, v.v... nếu chưa có thì phải thêm vào để web chạy đúng)
    # Ví dụ:
    # from .routes.web.news import news_bp
    # app.register_blueprint(news_bp, url_prefix='/web')

    @app.route("/")
    def home():
        return "Backend running OK!"

    return app