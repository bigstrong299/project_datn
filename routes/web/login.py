from flask import Blueprint, flash, render_template, request, redirect, session, url_for
from werkzeug.security import check_password_hash
from models.database import db
from models.infrastructure import Employee, Account

login_web = Blueprint("login_web", __name__)

@login_web.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    username = request.form.get("username")
    password = request.form.get("password")

    print("---- LOGIN FORM RECEIVED ----")
    print("USERNAME:", username)

    account = Account.query.filter_by(username=username).first()
    print("ACCOUNT:", account)

    if not account:
        flash("Sai tài khoản hoặc mật khẩu.")
        return redirect(url_for('login_web.login'))

    employee = Employee.query.filter_by(id=account.employee_id).first()
    print("EMPLOYEE:", employee)

    print("CHECK PASS HASH")

    if not check_password_hash(account.password, password):
        flash("Sai mật khẩu.")
        return redirect(url_for('login_web.login'))

    # ⚠️ KIỂM TRA ROLE — CHỈ ADMIN ĐƯỢC TRUY CẬP WEB
    if employee.role != "admin":
        flash("Tài khoản không phải admin, không thể truy cập hệ thống.")
        return redirect(url_for('login_web.login'))

    # Đăng nhập OK → set session
    session["logged_in"] = True
    session["username"] = username
    session["role"] = employee.role

    return redirect(url_for("admin_map.map_view"))


@login_web.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('login_web.login'))
