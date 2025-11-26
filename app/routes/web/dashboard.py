from flask import Blueprint, render_template
# from app.models.database import get_db_connection

bp = Blueprint("admin_dashboard", __name__, template_folder="../../templates")

@bp.route("/dashboard")
def dashboard():
    # ======= Chuẩn bị kết nối tới CSDL =======
    # conn = get_db_connection()
    # cur = conn.cursor()

    # ======= Lấy thống kê từ các bảng (có thể đổi sau này) =======
    # try:
    #     cur.execute("SELECT COUNT(*) FROM thung_rac;")
    #     total_bins = cur.fetchone()[0]

    #     cur.execute("SELECT COUNT(*) FROM tram_trung_chuyen;")
    #     total_transfer_stations = cur.fetchone()[0]

    #     cur.execute("SELECT COUNT(*) FROM diem_tap_ket;")
    #     total_collection_points = cur.fetchone()[0]

    #     cur.execute("SELECT COUNT(*) FROM nhan_vien;")
    #     total_employees = cur.fetchone()[0]

    #     cur.execute("SELECT COUNT(*) FROM nguoi_dung;")
    #     total_users = cur.fetchone()[0]

    #     cur.execute("SELECT COUNT(*) FROM tai_khoan;")
    #     total_accounts = cur.fetchone()[0]

    # except Exception as e:
    #     print("⚠️ Database error:", e)
    #     # Nếu DB chưa sẵn sàng, gán giá trị mặc định (mock)
    #     total_bins = 20
    #     total_transfer_stations = 5
    #     total_collection_points = 10
    #     total_employees = 8
    #     total_users = 150
    #     total_accounts = 100

    # finally:
    #     cur.close()
    #     conn.close()

    # ======= Gom dữ liệu thống kê =======
    stats = {
        "total_bins": 120,
        "total_transfer_stations": 5,
        "total_collection_points": 12
    }

    # Truyền qua template
    return render_template("dashboard.html", stats=stats)
