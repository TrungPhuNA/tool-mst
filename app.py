from flask import Flask
from dotenv import load_dotenv
import os

# Tải các biến môi trường
load_dotenv()

app = Flask(__name__)

# Tải cấu hình kết nối CSDL từ các biến môi trường
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')

# Import và đăng ký các route từ file route_crawler.py
from route.route_crawler import bp as tax_info_routes
app.register_blueprint(tax_info_routes)

# Bật chế độ debug tự động load lại khi thay đổi code
app.config['DEBUG'] = True

if __name__ == "__main__":
    app.run(debug=True)
