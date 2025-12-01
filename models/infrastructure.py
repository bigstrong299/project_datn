from .database import db
from geoalchemy2 import Geometry

# Model Thùng rác
class LitterBin(db.Model):
    __tablename__ = 'litter_bins'
    id = db.Column(db.String(20), primary_key=True)
    name = db.Column(db.String(100))
    address = db.Column(db.Text)
    geom = db.Column(Geometry('POINT', srid=4326))

# Model Trạm trung chuyển
class TransferStation(db.Model):
    __tablename__ = 'transfer_stations'
    id = db.Column(db.String(20), primary_key=True)
    name = db.Column(db.String(100))
    address = db.Column(db.Text)
    geom = db.Column(Geometry('POINT', srid=4326))

# Model Điểm tập kết
class CollectionPoint(db.Model):
    __tablename__ = 'garbage_collection_points'
    id = db.Column(db.String(20), primary_key=True)
    name = db.Column(db.String(100))
    address = db.Column(db.Text)
    geom = db.Column(Geometry('POINT', srid=4326))

class Employee(db.Model):
    __tablename__ = 'employees'
    id = db.Column(db.String(20), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    position = db.Column(db.String(50))
    role = db.Column(db.String(50), nullable=False) # 'admin' hoặc 'staff'
    # Các quan hệ khác...

class Account(db.Model):
    __tablename__ = 'accounts'
    id = db.Column(db.String(20), primary_key=True)
    employee_id = db.Column(db.String(20), db.ForeignKey('employees.id'))
    user_id = db.Column(db.String(20), db.ForeignKey('users.id'))
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.String(20), primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    phone = db.Column(db.String(20))

class ForumCategory(db.Model):
    __tablename__ = 'forum_categories'
    id = db.Column(db.String(20), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    # Quan hệ 1-nhiều với bài viết
    posts = db.relationship('ForumPost', backref='category', lazy=True)

class ForumPost(db.Model):
    __tablename__ = 'forum_posts'
    id = db.Column(db.String(20), primary_key=True)
    category_id = db.Column(db.String(20), db.ForeignKey('forum_categories.id'))
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)
    image = db.Column(db.Text) # (Tùy chọn) Link ảnh bìa bài viết
    status = db.Column(db.String(20), default="draft")
    time_post = db.Column(db.DateTime(timezone=True), server_default=db.func.now())

# Feedback - hỗ trợ nhiều ảnh + GPS
class Feedback(db.Model):
    __tablename__ = 'feedbacks'
    id = db.Column(db.String(20), primary_key=True)
    user_id = db.Column(db.String(20), db.ForeignKey('users.id'))
    content = db.Column(db.Text, nullable=False)
    image_urls = db.Column(db.ARRAY(db.Text))  # nhiều ảnh
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    address = db.Column(db.Text)
    date = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    status = db.Column(db.String(50), default='pending')  # pending/received/processing/resolved
    user = db.relationship('User', backref='feedbacks')

    # quan hệ 1 - nhiều (mỗi phản ánh có thể có nhiều bản ghi xử lý theo thời gian)
    handlings = db.relationship('FeedbackHandling', backref='feedback', lazy=True)

class FeedbackHandling(db.Model):
    __tablename__ = 'feedback_handlings'
    id = db.Column(db.String(20), primary_key=True)
    feedback_id = db.Column(db.String(20), db.ForeignKey('feedbacks.id'))
    employee_id = db.Column(db.String(20), db.ForeignKey('employees.id'))
    status = db.Column(db.String(50))  # received / processing / resolved
    note = db.Column(db.Text)
    attachment_url = db.Column(db.Text)
    time_process = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    employee = db.relationship('Employee', backref='handlings')