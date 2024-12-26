from flask import Flask, request, session, redirect, url_for, render_template
from dotenv import load_dotenv
from flask_bcrypt import Bcrypt
from datetime import timedelta
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from models.model_user import User
from flask_mail import Mail

import os
import fnmatch

from models.connect_db import db_connection

# Tải các biến môi trường
load_dotenv()

app = Flask(__name__)
app.secret_key = "PhuPhan"
app.permanent_session_lifetime = timedelta(days=1)

bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = "route_auth.login"

# Tải cấu hình kết nối CSDL từ các biến môi trường
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = ('Your App Name', os.getenv('MAIL_USERNAME'))

mail = Mail(app)

# Import và đăng ký các route từ file route_crawler.py
# from route.route_crawler import bp as tax_info_routes
from route.route_api import bp as route_api
from route.route_web import bp as route_web
from route.route_auth import bp as route_auth
from route.route_api_crawler import bp as route_api_crawler
from route.route_api_test import bp as route_api_test

app.register_blueprint(route_api)
app.register_blueprint(route_web)
app.register_blueprint(route_auth)
app.register_blueprint(route_api_crawler)
app.register_blueprint(route_api_test)

@login_manager.user_loader
def load_user(user_id):
    connection = db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    connection.close()
    if user:
        return User.from_dict(user)
    return None

@app.before_request
def require_login():
    # Danh sách URL không yêu cầu login
    exempt_routes = ["/login", "/register"]
    exempt_patterns = ["/api/*"]

    # Kiểm tra route hiện tại
    if request.path in exempt_routes:
        return

    # Kiểm tra pattern
    for pattern in exempt_patterns:
        if fnmatch.fnmatch(request.path, pattern):
            return

    # Chặn các route cần login
    if "user_id" not in session:
        return redirect(url_for("route_auth.login"))

    return

# Bật chế độ debug tự động load lại khi thay đổi code
app.config['DEBUG'] = True
app.config['TEMPLATES_AUTO_RELOAD'] = True

if __name__ == "__main__":
    app.run(debug=True)
