from flask import Blueprint, jsonify, request
from sqlalchemy import desc, func
from models.infrastructure import GarbageCollectionPointUpdate, TransferStationUpdate, db, LitterBin, TransferStation, CollectionPoint, LitterBinUpdate

api_map_bp = Blueprint('api_map', __name__)

@api_map_bp.route('/map', methods=['GET'])
def get_map():
    # ... (Giữ nguyên phần GET cũ của bạn) ...
    try:
        results = []
        # ... (Code lấy bins, stations, points giữ nguyên) ...
        # (Chỉ cần copy y nguyên phần get_map cũ)
        
        # 1. THÙNG RÁC
        bins = db.session.query(LitterBin.id, LitterBin.name, LitterBin.address, func.ST_X(LitterBin.geom).label('lng'), func.ST_Y(LitterBin.geom).label('lat')).all()
        for b in bins:
            latest = LitterBinUpdate.query.filter_by(litter_bin_id=b.id).order_by(desc(LitterBinUpdate.time_update)).first()
            results.append({
                "id": b.id, "name": b.name, "address": b.address, "latitude": b.lat, "longitude": b.lng, "type": "litter_bin",
                "status": latest.status if latest else "Bình thường",
                "weight": float(latest.weight) if (latest and latest.weight) else 0.0
            })

        # 2. TRẠM TRUNG CHUYỂN
        stations = db.session.query(TransferStation.id, TransferStation.name, TransferStation.address, func.ST_X(TransferStation.geom).label('lng'), func.ST_Y(TransferStation.geom).label('lat')).all()
        for s in stations:
            latest = TransferStationUpdate.query.filter_by(transfer_station_id=s.id).order_by(desc(TransferStationUpdate.time_update)).first()
            results.append({
                "id": s.id, "name": s.name, "address": s.address, "latitude": s.lat, "longitude": s.lng, "type": "transfer_station",
                "status": latest.status if latest else "Bình thường",
                "weight": float(latest.weight) if (latest and latest.weight) else 0.0
            })

        # 3. ĐIỂM TẬP KẾT
        points = db.session.query(CollectionPoint.id, CollectionPoint.name, CollectionPoint.address, func.ST_X(CollectionPoint.geom).label('lng'), func.ST_Y(CollectionPoint.geom).label('lat')).all()
        for p in points:
            latest = GarbageCollectionPointUpdate.query.filter_by(garbage_collection_point_id=p.id).order_by(desc(GarbageCollectionPointUpdate.time_update)).first()
            results.append({
                "id": p.id, "name": p.name, "address": p.address, "latitude": p.lat, "longitude": p.lng, "type": "collection_point",
                "status": latest.status if latest else "Bình thường",
                "weight": float(latest.weight) if (latest and latest.weight) else 0.0
            })

        return jsonify(results), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --- API CẬP NHẬT (ĐÃ SỬA ĐỂ LƯU NOTE) ---
@api_map_bp.route('/map/update', methods=['POST'])
def update_infrastructure():
    try:
        data = request.json
        
        infra_id = data.get('id')
        infra_type = data.get('type')
        weight = data.get('weight')
        status = data.get('status')
        employee_id = data.get('employee_id')
        note = data.get('note', '') # [MỚI] Nhận ghi chú từ App

        if not all([infra_id, infra_type, employee_id]):
            return jsonify({"error": "Thiếu thông tin bắt buộc"}), 400

        if infra_type == 'litter_bin':
            new_update = LitterBinUpdate(
                litter_bin_id=infra_id,
                employee_id=employee_id,
                weight=float(weight) if weight else 0,
                status=status,
                note=note # [MỚI]
            )
            db.session.add(new_update)

        elif infra_type == 'transfer_station':
            new_update = TransferStationUpdate(
                transfer_station_id=infra_id,
                employee_id=employee_id,
                weight=float(weight) if weight else 0,
                status=status,
                note=note # [MỚI]
            )
            db.session.add(new_update)

        elif infra_type == 'collection_point':
            new_update = GarbageCollectionPointUpdate(
                garbage_collection_point_id=infra_id,
                employee_id=employee_id,
                weight=float(weight) if weight else 0,
                status=status,
                note=note # [MỚI]
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