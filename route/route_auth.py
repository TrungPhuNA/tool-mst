from flask import Blueprint, request, render_template, session, redirect, url_for, current_app
from flask_bcrypt import Bcrypt
from models.connect_db import db_connection
from models.model_user import User
from flask_login import login_user, login_required
import threading
from flask_mail import Mail, Message
from app import mail

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
@login_required
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

        send_welcome_email(email, username)

        return redirect(url_for("route_web.tax_info_list"))

    return render_template("register.html")


@bp.route("/logout")
def logout():
    session.clear()  # Xóa toàn bộ session
    return redirect(url_for("route_auth.login"))


def send_welcome_email(email, username):
    """
    Gửi email chào mừng đến người dùng một cách bất đồng bộ.
    """
    login_url = "http://mst.s-notification.com/login"
    subject = "Welcome to Our App!"
    body_html = f"""
        <html>
        <body>
            <p>Hi {username},</p>
            <p>Thank you for registering with our app. We're excited to have you onboard!</p>
            <p>
                Click the link below to log in to your account:
                <br>
                <a href="{login_url}" target="_blank">Login to Your Account</a>
            </p>
            <p>If you have any questions, feel free to reach out to us.</p>
            <p>Best regards,<br>The Team</p>
        </body>
        </html>
    """

    # Tạo message
    msg = Message(subject, recipients=[email])
    msg.html = body_html  # Sử dụng nội dung HTML

    # Tạo luồng riêng để gửi email
    thread = threading.Thread(target=send_email_thread, args=(current_app._get_current_object(), msg))
    thread.start()

def send_email_thread(app, msg):
    """
    Hàm chạy trong luồng để gửi email.
    """
    with app.app_context():
        try:
            mail.send(msg)
            print(f"Email sent to {msg.recipients[0]}")
        except Exception as e:
            print(f"Failed to send email to {msg.recipients[0]}: {e}")