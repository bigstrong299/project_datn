
from flask import Blueprint, render_template
from sqlalchemy import func
from models.database import db
from models.infrastructure import LitterBin, TransferStation, CollectionPoint

# Tên 'admin_map' khớp với url_for('admin_map.map_view')
map_bp = Blueprint('admin_map', __name__)

@map_bp.route('/map')
def map_view(): # Đã đổi tên hàm thành map_view tránh trùng tên module
    # Hàm phụ trợ để format dữ liệu GeoJSON đơn giản
    def get_geojson_data(ModelClass):
        # ST_X là Kinh độ (Longitude), ST_Y là Vĩ độ (Latitude)
        results = db.session.query(
            ModelClass.id,
            ModelClass.name,
            ModelClass.address,
            func.ST_X(ModelClass.geom).label('lng'),
            func.ST_Y(ModelClass.geom).label('lat')
        ).all()
        
        data = []
        for row in results:
            if row.lat and row.lng: # Chỉ lấy điểm có tọa độ
                data.append({
                    "id": row.id,
                    "name": row.name,
                    "address": row.address,
                    "lat": row.lat,
                    "lng": row.lng
                })
        return data

    # Lấy dữ liệu 3 bảng
    bins_data = get_geojson_data(LitterBin)
    stations_data = get_geojson_data(TransferStation)
    points_data = get_geojson_data(CollectionPoint)

    return render_template('map.html', 
                           bins=bins_data, 
                           stations=stations_data, 
                           points=points_data)