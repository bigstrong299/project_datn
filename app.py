from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
from flask_jwt_extended import JWTManager
import os

# 1. Import Config
from config import Config

# 2. Import DB từ folder models
from models.database import db

# 3. Import Blueprint từ folder routes -> api
from routes.api.auth import auth_bp

load_dotenv()

app = Flask(__name__)
app.config.from_object(Config)

# Cấu hình Secret Key cho Token (Nếu trong Config chưa có thì thêm tạm ở đây)
app.config["JWT_SECRET_KEY"] = "duongxinhdep296"
# Cấu hình CORS (Để Flutter gọi được)
CORS(app)

# Khởi tạo Database
db.init_app(app)
jwt = JWTManager(app)

# Đăng ký Blueprint
# API sẽ là: http://IP:5000/api/auth/login
app.register_blueprint(auth_bp, url_prefix='/api/auth')

# Route test chơi
@app.route("/")
def home():
    return "Backend Smart Waste is running!"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)