from flask import Blueprint, request, render_template, session, redirect, url_for
from flask_bcrypt import Bcrypt
from models.connect_db import db_connection
from models.model_user import User
from flask_login import login_user

bcrypt = Bcrypt()  # Sử dụng bcrypt

bp = Blueprint("route_auth", __name__)

@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        connection = db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        connection.close()
        print("=============== user ========== ", user)
        if user and bcrypt.check_password_hash(user["password_hash"], password):
            user_obj = User.from_dict(user)  # Tạo đối tượng User từ dữ liệu
            login_user(user_obj)  # Đăng nhập với Flask-Login
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("route_web.tax_info_list"))

        return render_template("login.html", error="Sai email hoặc mật khẩu.")

    return render_template("login.html")


@bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        # Mã hóa mật khẩu
        password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

        # Lưu thông tin vào database
        connection = db_connection()
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
            (username, email, password_hash),
        )
        connection.commit()
        connection.close()

        return redirect(url_for("route_auth.login"))

    return render_template("register.html")


@bp.route("/logout")
def logout():
    session.clear()  # Xóa toàn bộ session
    return redirect(url_for("route_auth.login"))
