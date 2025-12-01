from flask import Blueprint, render_template
from models.infrastructure import LitterBin, TransferStation, CollectionPoint
from models.database import db

dashboard_bp = Blueprint('admin_dashboard', __name__)

@dashboard_bp.route('/dashboard')
def dashboard():
    # 1. Truy vấn số lượng thực tế từ Database
    count_bins = LitterBin.query.count()
    count_stations = TransferStation.query.count()
    count_points = CollectionPoint.query.count()

    stats = {
        "total_bins": count_bins,
        "total_transfer_stations": count_stations,
        "total_collection_points": count_points
    }

    # 2. Dữ liệu biểu đồ (Data Visualization)
    # Vì dữ liệu cập nhật nằm ở bảng khác, ở đây mình gom nhóm dữ liệu để vẽ biểu đồ tròn
    # Tỷ lệ phân bố hạ tầng
    chart_data = {
        "labels": ["Thùng rác", "Trạm trung chuyển", "Điểm tập kết"],
        "data": [count_bins, count_stations, count_points]
    }
    # 3. Dữ liệu biểu đồ ĐƯỜNG (Biến động theo thời gian - 3 đường)
    # (Dữ liệu giả lập 6 tháng gần nhất - Sau này bạn thay bằng query group by month)
    line_chart_data = {
        "labels": ["Tháng 1", "Tháng 2", "Tháng 3", "Tháng 4", "Tháng 5", "Tháng 6"],
        "data_bins": [12, 19, 15, 25, 22, 30],      # Đường 1: Thùng rác
        "data_points": [5, 7, 6, 8, 10, 12],        # Đường 2: Điểm tập kết
        "data_stations": [1, 1, 2, 2, 3, 3]         # Đường 3: Trạm trung chuyển
    }

    return render_template('dashboard.html', 
                           stats=stats, 
                           chart_data=chart_data, 
                           line_chart_data=line_chart_data)