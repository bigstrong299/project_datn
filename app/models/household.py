from .database import db
from datetime import datetime
from geoalchemy2 import Geometry

class Household(db.Model):
    __tablename__ = "ho_dan"
    id = db.Column(db.Integer, primary_key=True)
    ma_hodan = db.Column(db.String(120), unique=True)
    ten_chu_ho = db.Column(db.String(200))
    diachi = db.Column(db.String(500))
    geom = db.Column(Geometry(geometry_type='POLYGON', srid=4326))
    trang_thai_payment = db.Column(db.Boolean, default=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
