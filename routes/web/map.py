
from flask import Blueprint, render_template
from sqlalchemy import desc, func
from models.database import db
from models.infrastructure import GarbageCollectionPointUpdate, LitterBin, LitterBinUpdate, TransferStation, CollectionPoint, TransferStationUpdate

# Tên 'admin_map' khớp với url_for('admin_map.map_view')
map_bp = Blueprint('admin_map', __name__)

@map_bp.route('/map')
def map_view():
    # Hàm lấy dữ liệu kèm trạng thái mới nhất
    def get_data_with_status(ModelClass, UpdateModelClass, fk_field):
        results = db.session.query(
            ModelClass.id,
            ModelClass.name,
            ModelClass.address,
            func.ST_X(ModelClass.geom).label('lng'),
            func.ST_Y(ModelClass.geom).label('lat')
        ).all()
        
        data = []
        for row in results:
            if row.lat and row.lng:
                # Lấy update mới nhất
                latest = UpdateModelClass.query.filter_by(**{fk_field: row.id})\
                            .order_by(desc(UpdateModelClass.time_update)).first()
                
                # Format dữ liệu
                status = latest.status if latest else "Bình thường"
                weight = float(latest.weight) if (latest and latest.weight) else 0.0
                updater = latest.employee_id if latest else "N/A" # Có thể join bảng Employee để lấy tên
                time = latest.time_update.strftime('%d/%m/%Y %H:%M') if latest else "Chưa cập nhật"

                data.append({
                    "id": row.id,
                    "name": row.name,
                    "address": row.address,
                    "lat": row.lat,
                    "lng": row.lng,
                    "status": status,
                    "weight": weight,
                    "updater": updater,
                    "time": time
                })
        return data

    # Lấy dữ liệu 3 bảng
    bins_data = get_data_with_status(LitterBin, LitterBinUpdate, 'litter_bin_id')
    stations_data = get_data_with_status(TransferStation, TransferStationUpdate, 'transfer_station_id')
    points_data = get_data_with_status(CollectionPoint, GarbageCollectionPointUpdate, 'garbage_collection_point_id')

    return render_template('map.html', 
                           bins=bins_data, 
                           stations=stations_data, 
                           points=points_data)