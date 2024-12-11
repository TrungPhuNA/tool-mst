from flask import Flask, request, jsonify, render_template
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


@app.route("/tax-info-list", methods=["GET"])
def tax_info_list():
    try:
        # Lấy tham số tìm kiếm và phân trang
        search_query = request.args.get("search", "").strip()
        page = int(request.args.get("page", 1))
        limit = 10
        offset = (page - 1) * limit

        # Kết nối database
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # Query dữ liệu
        if search_query:
            cursor.execute("""
                SELECT * FROM tax_info 
                WHERE tax_id LIKE %s OR name LIKE %s OR address LIKE %s 
                LIMIT %s OFFSET %s
            """, (f"%{search_query}%", f"%{search_query}%", f"%{search_query}%", limit, offset))
        else:
            cursor.execute("SELECT * FROM tax_info LIMIT %s OFFSET %s", (limit, offset))
        
        tax_info_list = cursor.fetchall()

        # Đếm tổng số bản ghi để tính tổng số trang
        if search_query:
            cursor.execute("""
                SELECT COUNT(*) as total FROM tax_info 
                WHERE tax_id LIKE %s OR name LIKE %s OR address LIKE %s
            """, (f"%{search_query}%", f"%{search_query}%", f"%{search_query}%"))
        else:
            cursor.execute("SELECT COUNT(*) as total FROM tax_info")
        total = cursor.fetchone()["total"]
        total_pages = math.ceil(total / limit)

        cursor.close()
        connection.close()

        # Render giao diện với dữ liệu
        return render_template("tax_info_list.html", 
                               tax_info_list=tax_info_list, 
                               search_query=search_query, 
                               page=page, 
                               total_pages=total_pages)
    except Exception as e:
        traceback.print_exc()
        return f"An error occurred: {e}", 500



@app.route("/api/get-tax-info", methods=["GET"])
def get_tax_info():
    # Lấy tham số từ request
    param = request.args.get("param")
    if not param:
        return jsonify({"error": "Missing required parameter 'param'"}), 400

    #Kiểm tra trong cơ sở dữ liệu trước
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # Kiểm tra nếu mã số thuế đã tồn tại trong DB
        cursor.execute("SELECT * FROM tax_info WHERE tax_id = %s", (param,))
        result = cursor.fetchone()
        cursor.close()
        connection.close()

        if result:
            print("Data fetched from DB:", result)
            return jsonify({
                "code": "00",
                "desc": "Success - Thành công",
                "data": {
                    "id": result["tax_id"],
                    "name": result["name"],
                    "address": result["address"],
                    "status": result["status"],
                    "representative": result["representative"],
                    "management": result["management"],
                    "activeDate": result["active_date"].strftime('%Y-%m-%d') if result["active_date"] else None,
                    "source_url": result["source_url"]
                }
            }), 200
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

    # Nếu không tồn tại, crawler dữ liệu
    print("================ param: ", param)
    result = crawl_masothue(param)
    if not result:
        return jsonify({
            "code": "99",
            "desc": "Failed to fetch data",
            "data": {}
        }), 500

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
