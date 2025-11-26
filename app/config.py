import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/mydb")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MODE = os.getenv("MODE", "public")  # public or internal
