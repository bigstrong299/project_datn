from flask import Blueprint, jsonify
from sqlalchemy import func
from models.infrastructure import db, LitterBin, TransferStation, CollectionPoint

api_map_bp = Blueprint('api_map', __name__)

@api_map_bp.route('/map', methods=['GET'])
def get_map():
    try:
        results = []

        # 1. Lấy dữ liệu Thùng rác (Litter Bins)
        # Sử dụng func.ST_X (Kinh độ) và func.ST_Y (Vĩ độ) để tách tọa độ từ cột Geometry
        bins = db.session.query(
            LitterBin.id, 
            LitterBin.name, 
            LitterBin.address, 
            func.ST_X(LitterBin.geom).label('lng'), 
            func.ST_Y(LitterBin.geom).label('lat')
        ).all()

        for b in bins:
            results.append({
                "id": b.id,
                "name": b.name,
                "address": b.address,
                "latitude": b.lat,
                "longitude": b.lng,
                "type": "litter_bin" # Đánh dấu loại để App hiển thị màu khác nhau
            })

        # 2. Lấy dữ liệu Trạm trung chuyển
        stations = db.session.query(
            TransferStation.id, 
            TransferStation.name, 
            TransferStation.address, 
            func.ST_X(TransferStation.geom).label('lng'), 
            func.ST_Y(TransferStation.geom).label('lat')
        ).all()

        for s in stations:
            results.append({
                "id": s.id,
                "name": s.name,
                "address": s.address,
                "latitude": s.lat,
                "longitude": s.lng,
                "type": "transfer_station"
            })

        # 3. Lấy dữ liệu Điểm tập kết
        points = db.session.query(
            CollectionPoint.id, 
            CollectionPoint.name, 
            CollectionPoint.address, 
            func.ST_X(CollectionPoint.geom).label('lng'), 
            func.ST_Y(CollectionPoint.geom).label('lat')
        ).all()

        for p in points:
            results.append({
                "id": p.id,
                "name": p.name,
                "address": p.address,
                "latitude": p.lat,
                "longitude": p.lng,
                "type": "collection_point"
            })

        return jsonify(results), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500