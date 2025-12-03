from flask import Blueprint, jsonify, request
from sqlalchemy import func
from models.infrastructure import GarbageCollectionPointUpdate, TransferStationUpdate, db, LitterBin, TransferStation, CollectionPoint, LitterBinUpdate

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

# --- API CẬP NHẬT TRẠNG THÁI (Dành cho nhân viên) ---
@api_map_bp.route('/map/update', methods=['POST'])
def update_infrastructure():
    try:
        data = request.json
        
        # Lấy dữ liệu từ App gửi lên
        infra_id = data.get('id')          # ID điểm (VD: TR001)
        infra_type = data.get('type')      # Loại (litter_bin, transfer_station...)
        weight = data.get('weight')        # Khối lượng
        status = data.get('status')        # Trạng thái (Đầy, Rỗng...)
        employee_id = data.get('employee_id') # ID nhân viên thực hiện

        if not all([infra_id, infra_type, employee_id]):
            return jsonify({"error": "Thiếu thông tin bắt buộc"}), 400

        # Phân loại để lưu vào đúng bảng
        if infra_type == 'litter_bin':
            new_update = LitterBinUpdate(
                litter_bin_id=infra_id,
                employee_id=employee_id,
                weight=float(weight) if weight else 0,
                status=status
            )
            db.session.add(new_update)

        elif infra_type == 'transfer_station':
            new_update = TransferStationUpdate(
                transfer_station_id=infra_id,
                employee_id=employee_id,
                weight=float(weight) if weight else 0,
                status=status
            )
            db.session.add(new_update)

        elif infra_type == 'collection_point':
            new_update = GarbageCollectionPointUpdate(
                garbage_collection_point_id=infra_id,
                employee_id=employee_id,
                weight=float(weight) if weight else 0,
                status=status
            )
            db.session.add(new_update)
        
        else:
            return jsonify({"error": "Loại địa điểm không hợp lệ"}), 400

        db.session.commit()
        return jsonify({"message": "Cập nhật thành công"}), 200

    except Exception as e:
        db.session.rollback()
        print(f"Lỗi update map: {e}")
        return jsonify({"error": str(e)}), 500