from flask import Flask, request, jsonify
from crawler import crawl_masothue
from models import save_to_db, get_db_connection
from dotenv import load_dotenv
import traceback
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

    #Kiểm tra trong cơ sở dữ liệu trước
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        # Kiểm tra nếu mã số thuế đã tồn tại trong DB
        cursor.execute("SELECT * FROM tax_info WHERE tax_id = %s", (param,))
        result = cursor.fetchone()
        cursor.close()
        connection.close()

        if result:
            print("Data fetched from DB:", result)
            return jsonify({
                "id": result["tax_id"],
                "name": result["name"],
                "address": result["address"],
                "status": result["status"],
                "representative": result["representative"],
                "management": result["management"],
                "activeDate": result["active_date"],
                "source_url": result["source_url"]
            }), 200
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

    # Nếu không tồn tại, crawler dữ liệu
    print("================ param: ", param)
    result = crawl_masothue(param)
    if not result:
        return jsonify({"error": "Failed to fetch data"}), 500

    # Lưu vào database
    try:
        if result["code"] == "00":
            save_to_db(result["data"])
        
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

    # Trả về kết quả JSON
    return jsonify(result), 200



if __name__ == "__main__":
    app.run(debug=True)
