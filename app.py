from flask import Flask, redirect, session, request
from flask_cors import CORS
from dotenv import load_dotenv
from flask_jwt_extended import JWTManager
import os

from models.infrastructure import Account
from config import Config
from models.database import db

# API
from routes.api.auth import auth_bp
from routes.api.news import news_api_bp
from routes.api.feedback import feedback_api

# WEB
from routes.web.login import login_web
from routes.web.map import map_bp
from routes.web.news import news_bp
from routes.web.dashboard import dashboard_bp
from routes.web.administration import admin_bp
from routes.web.feedback import feedback_bp

load_dotenv()

app = Flask(__name__)
app.config.from_object(Config)

# Đường dẫn này sẽ nằm trong thư mục project của bạn: static/uploads
UPLOAD_FOLDER = os.path.join('static', 'uploads') 
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Tạo thư mục nếu chưa có
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Khóa session (quan trọng!)
app.secret_key = "supersecret_session_key_123"

app.config["JWT_SECRET_KEY"] = "duongxinhdep296"
CORS(app)

db.init_app(app)
jwt = JWTManager(app)

# -------------------------
#  FORCING LOGIN FOR /web/*
# -------------------------
@app.before_request
def require_login():
    path = request.path

    # Chỉ áp dụng kiểm tra cho /web/*
    if path.startswith("/web"):

        # CHO PHÉP TRUY CẬP login page để tránh loop
        if path.startswith("/web/login"):
            return

        # CHO PHÉP TRUY CẬP static (css, js, img)
        if path.startswith("/static"):
            return

        # 1. CHƯA LOGIN → CHẶN
        if "logged_in" not in session:
            return redirect("/web/login")

        # 2. LOGIN RỒI NHƯNG ROLE ≠ ADMIN → CHẶN
        if session.get("role") != "admin":
            return redirect("/web/login")

        # 3. LOGIN OK VÀ ROLE ADMIN → ĐƯỢC TRUY CẬP
        return

# -------------------------
# Đăng ký Blueprint
# -------------------------
app.register_blueprint(auth_bp, url_prefix='/api')
app.register_blueprint(news_api_bp, url_prefix='/api')
app.register_blueprint(feedback_api, url_prefix='/api')

app.register_blueprint(login_web, url_prefix="/web")       # login
app.register_blueprint(map_bp, url_prefix="/web")          # map
app.register_blueprint(news_bp, url_prefix="/web")         # news
app.register_blueprint(dashboard_bp, url_prefix="/web")    # dashboard
app.register_blueprint(admin_bp, url_prefix="/web")
app.register_blueprint(feedback_bp, url_prefix="/web")            # admin pages

@app.route("/")
def home():
    return "Backend Smart Waste is running!"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
