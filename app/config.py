import os
from dotenv import load_dotenv

# Load biến môi trường từ file .env nếu đang chạy ở local
load_dotenv()

class Config:
    # Lấy SECRET_KEY, nếu không có thì dùng key mặc định (chỉ cho dev)
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'default-secret-key-datn'
    
    # Lấy DATABASE_URL
    uri = os.environ.get('DATABASE_URL')
    
    # Xử lý fix lỗi "postgres://" -> "postgresql://" cho SQLAlchemy
    if uri and uri.startswith("postgres://"):
        uri = uri.replace("postgres://", "postgresql://", 1)
        
    SQLALCHEMY_DATABASE_URI = uri
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'super-secret-jwt-key-datn'