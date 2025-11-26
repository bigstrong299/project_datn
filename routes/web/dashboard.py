# backend/routes/web/dashboard.py
from flask import Blueprint, render_template
from models.database import db
from sqlalchemy import text

# Định nghĩa Blueprint
dashboard_bp = Blueprint('admin_dashboard', __name__, template_folder='../../templates')

@dashboard_bp.route('/manager') 
def dashboard():
    stats = {
        'total_bins': 0,
        'total_collection_points': 0,
        'total_transfer_stations': 0
    }
    
    # Dữ liệu chi tiết để hiển thị list (nếu cần)
    recent_bins = []

    try:
        # 1. Đếm tổng Thùng rác
        total_bins = db.session.execute(text("SELECT COUNT(*) FROM litter_bins")).scalar()
        
        # 2. Đếm tổng Điểm tập kết
        total_cp = db.session.execute(text("SELECT COUNT(*) FROM garbage_collection_points")).scalar()
        
        # 3. Đếm tổng Trạm trung chuyển
        total_ts = db.session.execute(text("SELECT COUNT(*) FROM transfer_stations")).scalar()

        # 4. (Tùy chọn) Lấy danh sách 5 thùng rác đầy để cảnh báo
        full_bins_query = db.session.execute(text("SELECT address FROM litter_bins WHERE status = 'Full' LIMIT 5")).fetchall()
        
        # Cập nhật vào dictionary stats
        stats['total_bins'] = total_bins
        stats['total_collection_points'] = total_cp
        stats['total_transfer_stations'] = total_ts
        
        # Có thể truyền thêm danh sách thùng rác đầy ra view nếu muốn
        # stats['full_bins'] = full_bins_query

    except Exception as e:
        print(f"❌ Lỗi truy vấn Dashboard: {str(e)}")
        # Nếu chưa tạo bảng thì nó sẽ giữ giá trị 0 mặc định để không crash web

    # Trả về giao diện dashboard.html với dữ liệu thật
    return render_template('dashboard.html', stats=stats)