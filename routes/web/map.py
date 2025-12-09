from flask import Blueprint, render_template
from sqlalchemy import desc, func
from models.database import db
from models.infrastructure import GarbageCollectionPointUpdate, LitterBin, LitterBinUpdate, TransferStation, CollectionPoint, TransferStationUpdate
from datetime import datetime, timedelta # Import

map_bp = Blueprint('admin_map', __name__)

@map_bp.route('/map')
def map_view():
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
                latest = UpdateModelClass.query.filter_by(**{fk_field: row.id})\
                            .order_by(desc(UpdateModelClass.time_update)).first()
                
                status = latest.status if latest else "Bình thường"
                weight = float(latest.weight) if (latest and latest.weight) else 0.0
                updater = latest.employee_id if latest else "N/A" 
                
                # [SỬA LỖI GIỜ BẢN ĐỒ]
                if latest and latest.time_update:
                    # Database server (Render) lưu UTC -> Cần cộng 7h để ra giờ VN
                    time_vn = latest.time_update + timedelta(hours=7)
                    time = time_vn.strftime('%d/%m/%Y %H:%M')
                else:
                    time = "Chưa cập nhật"

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

    bins_data = get_data_with_status(LitterBin, LitterBinUpdate, 'litter_bin_id')
    stations_data = get_data_with_status(TransferStation, TransferStationUpdate, 'transfer_station_id')
    points_data = get_data_with_status(CollectionPoint, GarbageCollectionPointUpdate, 'garbage_collection_point_id')

    return render_template('map.html', 
                           bins=bins_data, 
                           stations=stations_data, 
                           points=points_data)