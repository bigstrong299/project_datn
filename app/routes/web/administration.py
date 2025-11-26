from flask import Blueprint, render_template

bp = Blueprint("admin_administration", __name__, template_folder="../../templates")

@bp.route("/administration")
def administration():
    # Thống kê mẫu (sau này bạn có thể truy vấn từ PostgreSQL)
    stats = {
        "total_users": 250,          # Người dùng hệ thống (cộng đồng)
        "total_employees": 15,       # Nhân viên thu gom, vận hành
        "total_accounts": 265,       # Tài khoản đăng nhập hệ thống
    }

    return render_template("administration.html", stats=stats)
