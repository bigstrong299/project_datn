from flask import Flask
from .models.database import db
from config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    # ví dụ đăng ký blueprint
    from .routes.api.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')

    return app
