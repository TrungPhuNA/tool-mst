from flask import Flask, request, jsonify
from crawler import crawl_masothue
from models import save_to_db
from dotenv import load_dotenv
import os

load_dotenv()
app = Flask(__name__)

DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')

@app.route("/api/get-tax-info", methods=["GET"])
def get_tax_info():
    # Lấy tham số từ request
    param = request.args.get("param")
    if not param:
        return jsonify({"error": "Missing required parameter 'param'"}), 400

    # Crawler dữ liệu
    print("================ param: ", param)
    result = crawl_masothue(param)
    if not result:
        return jsonify({"error": "Failed to fetch data"}), 500

    # Lưu vào database
    try:
        save_to_db(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    # Trả về kết quả JSON
    return jsonify(result), 200


if __name__ == "__main__":
    app.run(debug=True)
