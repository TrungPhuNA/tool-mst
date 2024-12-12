from flask import Blueprint, request, jsonify, render_template
from tool.crawler import crawl_masothue
from models.model_tax_info import save_to_db, get_db_connection, save_data_error_to_db, update_crawler_status
import traceback
import math

# Tạo Blueprint cho các route
bp = Blueprint('tax_info_routes', __name__)


@bp.route("/", methods=["GET"])
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


# @bp.route("/api/get-tax-info", methods=["GET"])
# def get_tax_info():
#     # Lấy tham số từ request
#     param = request.args.get("param")
#     if not param:
#         return jsonify({"error": "Missing required parameter 'param'"}), 400
#
#     connection = get_db_connection()
#     cursor = connection.cursor(dictionary=True)
#
#     # Kiểm tra nếu mã số thuế đã tồn tại trong DB
#     cursor.execute("SELECT * FROM tax_info WHERE tax_id = %s", (param,))
#     result = cursor.fetchone()
#     cursor.close()
#     connection.close()
#
#     if result:
#         return jsonify({
#             "code": "00",
#             "desc": "Success - Thành công",
#             "data": {
#                 "id": result["tax_id"],
#                 "name": result["name"],
#                 "internationalName": result["international_name"],
#                 "address": result["address"],
#                 "status": result["status"],
#                 "representative": result["representative"],
#                 "management": result["management"],
#                 "activeDate": result["active_date"].strftime('%Y-%m-%d') if result["active_date"] else None,
#                 "source_url": result["source_url"]
#             }
#         }), 200
#
#     result = crawl_masothue(param)
#     if not result:
#         save_data_error_to_db({
#             "param_search": param
#         })
#         return jsonify({
#             "code": "99",
#             "desc": "Failed to fetch data",
#             "data": {}
#         }), 500
#
#     if result["code"] == "00":
#         save_to_db(result["data"])
#
#     return jsonify(result), 200



@bp.route("/api/get-tax-info", methods=["GET"])
def get_tax_info():
    # Lấy tham số từ request
    param = request.args.get("param")
    if not param:
        return jsonify({"error": "Missing required parameter 'param'"}), 400

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    # Kiểm tra nếu mã số thuế đã tồn tại trong DB
    cursor.execute("SELECT * FROM tax_info WHERE param_search = %s", (param,))
    result = cursor.fetchone()
    cursor.close()

    if result:
        # Nếu có dữ liệu, kiểm tra trạng thái của crawler
        if result['crawler_status'] == 'retry' and result['retry_time'] > datetime.now():
            return jsonify({
                "code": "99",
                "desc": "Crawler is retrying, please try again later",
                "data": {}
            }), 500

        return jsonify({
            "code": "00",
            "desc": "Success - Thành công",
            "data": {
                "id": result["tax_id"],
                "name": result["name"],
                "internationalName": result["international_name"],
                "address": result["address"],
                "status": result["status"],
                "representative": result["representative"],
                "management": result["management"],
                "activeDate": result["active_date"].strftime('%Y-%m-%d') if result["active_date"] else None,
                "source_url": result["source_url"]
            }
        }), 200

    # Nếu không có dữ liệu trong DB, crawl dữ liệu từ nguồn bên ngoài
    result = crawl_masothue(param)
    if not result:
        update_crawler_status(param, 'error')  # Cập nhật trạng thái lỗi
        return jsonify({
            "code": "99",
            "desc": "Failed to fetch data",
            "data": {}
        }), 500

    if result["code"] == "00":
        save_to_db(result["data"])  # Chèn vào DB
        update_crawler_status(param, 'success')  # Cập nhật trạng thái thành công

    return jsonify(result), 200

@bp.route("/api/delete-tax-info", methods=["POST"])
def delete_tax_info():
    data = request.get_json()
    tax_id = data.get("tax_id")
    if not tax_id:
        return jsonify({"error": "Missing required parameter 'tax_id'"}), 400

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        # Xóa dữ liệu theo tax_id
        cursor.execute("DELETE FROM tax_info WHERE id = %s", (tax_id,))
        connection.commit()

        cursor.close()
        connection.close()
        return jsonify({"code": "00", "desc": "Deleted successfully"}), 200
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
