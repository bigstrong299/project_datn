from flask import Blueprint, render_template, request, redirect, url_for, flash
from sqlalchemy import func, case, text
from datetime import datetime, timedelta
from models.database import db
from models.infrastructure import LitterBin, TransferStation, CollectionPoint
from models.infrastructure import LitterBinUpdate, TransferStationUpdate, GarbageCollectionPointUpdate

dashboard_bp = Blueprint('admin_dashboard', __name__)

@dashboard_bp.route('/dashboard')
def dashboard():
    # 1. Thống kê tổng số lượng (Stats Cards)
    count_bins = LitterBin.query.count()
    count_stations = TransferStation.query.count()
    count_points = CollectionPoint.query.count()

    stats = {
        "total_bins": count_bins,
        "total_transfer_stations": count_stations,
        "total_collection_points": count_points
    }

    # 2. Biểu đồ TRÒN (Tỷ lệ hạ tầng - Giữ nguyên)
    chart_distribution = {
        "labels": ["Thùng rác", "Trạm trung chuyển", "Điểm tập kết"],
        "data": [count_bins, count_stations, count_points]
    }

    # 3. Biểu đồ CỘT (Trạng thái hiện tại - Realtime Status)
    # Logic: Lấy status mới nhất của từng loại điểm và cộng dồn
    # Để đơn giản và nhanh cho demo, ta query trực tiếp từ bảng Updates (chấp nhận sai số nhỏ nếu điểm đó chưa update lần nào)
    
    def get_status_counts(UpdateModel):
        return db.session.query(
            UpdateModel.status, func.count(UpdateModel.id)
        ).group_by(UpdateModel.status).all()

    # Tổng hợp status từ 3 bảng update
    status_summary = {"Bình thường": 0, "Đã dọn": 0, "Đầy": 0, "Quá tải": 0, "Hư hỏng": 0}
    
    for Model in [LitterBinUpdate, TransferStationUpdate, GarbageCollectionPointUpdate]:
        results = get_status_counts(Model)
        for status, count in results:
            if status in status_summary:
                status_summary[status] += count
            elif status == "Đầy": # Gộp Đầy/Quá tải nếu muốn
                 status_summary["Đầy"] += count

    chart_status = {
        "labels": list(status_summary.keys()),
        "data": list(status_summary.values())
    }

    # 4. Biểu đồ ĐƯỜNG (Khối lượng rác 30 ngày qua)
    # Query: SELECT date(time_update), SUM(weight) FROM updates WHERE time > 30_days_ago GROUP BY date
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    # Tạo danh sách 30 ngày làm trục X
    date_labels = [(start_date + timedelta(days=i)).strftime('%d/%m') for i in range(31)]
    
    def get_daily_weight(UpdateModel):
        results = db.session.query(
            func.date(UpdateModel.time_update).label('day'),
            func.sum(UpdateModel.weight)
        ).filter(UpdateModel.time_update >= start_date)\
         .group_by('day').all()
        
        # Map dữ liệu vào list 30 ngày (để tránh ngày không có dữ liệu bị khuyết)
        data_map = {res.day.strftime('%d/%m'): float(res[1] or 0) for res in results}
        return [data_map.get(day, 0) for day in date_labels]

    line_chart_data = {
        "labels": date_labels,
        "data_bins": get_daily_weight(LitterBinUpdate),
        "data_stations": get_daily_weight(TransferStationUpdate),
        "data_points": get_daily_weight(GarbageCollectionPointUpdate)
    }

    bins_list = LitterBin.query.all()
    stations_list = TransferStation.query.all()
    points_list = CollectionPoint.query.all()

    return render_template('dashboard.html', 
                           stats=stats, 
                           chart_distribution=chart_distribution,
                           chart_status=chart_status,
                           line_chart_data=line_chart_data,
                           # Truyền danh sách sang HTML
                           bins_list=bins_list,
                           stations_list=stations_list,
                           points_list=points_list)

@dashboard_bp.route('/infrastructure/delete/<type>/<id>', methods=['GET'])
def delete_infrastructure(type, id):
    try:
        item = None
        if type == 'bin': item = LitterBin.query.get(id)
        elif type == 'station': item = TransferStation.query.get(id)
        elif type == 'point': item = CollectionPoint.query.get(id)

        if item:
            db.session.delete(item)
            db.session.commit()
            flash('Đã xóa thành công!', 'success')
        else:
            flash('Không tìm thấy dữ liệu!', 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'Lỗi xóa: {str(e)}', 'danger')
    
    return redirect(url_for('admin_dashboard.dashboard'))

# --- ROUTE CẬP NHẬT HẠ TẦNG ---
@dashboard_bp.route('/infrastructure/update', methods=['POST'])
def update_infrastructure():
    try:
        infra_type = request.form.get('type')
        infra_id = request.form.get('id')
        name = request.form.get('name')
        address = request.form.get('address')

        item = None
        if infra_type == 'bin': item = LitterBin.query.get(infra_id)
        elif infra_type == 'station': item = TransferStation.query.get(infra_id)
        elif infra_type == 'point': item = CollectionPoint.query.get(infra_id)

        if item:
            item.name = name
            item.address = address
            db.session.commit()
            flash('Cập nhật thành công!', 'success')
        else:
            flash('Không tìm thấy dữ liệu!', 'danger')

    except Exception as e:
        db.session.rollback()
        flash(f'Lỗi cập nhật: {str(e)}', 'danger')

    return redirect(url_for('admin_dashboard.dashboard'))