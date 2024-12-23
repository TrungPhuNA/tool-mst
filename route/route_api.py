from flask import Blueprint, request, jsonify, render_template
from tool.crawler import crawl_masothue
from models.model_tax_info import save_to_db, get_db_connection, save_data_error_to_db, update_crawler_status
import traceback
import math

# Tạo Blueprint cho các route
bp = Blueprint('route_api', __name__)

@bp.route("/api/get-tax-info", methods=["GET"])
def get_tax_info():
    # Lấy tham số từ request
    param = request.args.get("param")
    print("============ param: ", param)
    if not param:
        return jsonify({"error": "Missing required parameter 'param'"}), 400

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    print("=========== connect success")
    # Kiểm tra nếu mã số thuế đã tồn tại trong DB
    cursor.execute("SELECT * FROM tax_info WHERE param_search = %s", (param,))
    result = cursor.fetchone()
    cursor.close()
    print("=========== close connect success")
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


@bp.route("/api/get-all", methods=["POST"])
def get_tax_all():
    try:
        # Lấy dữ liệu JSON từ body
        data = request.get_json()
        draw = int(data.get("draw", 1))  # Số lần gửi request
        start = int(data.get("start", 0))  # Bản ghi bắt đầu
        length = int(data.get("length", 10))  # Số bản ghi trên mỗi trang
        search_value = data.get("search", {}).get("value", "").strip()  # Giá trị tìm kiếm

        # Kết nối database
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # Lấy tổng số bản ghi
        cursor.execute("SELECT COUNT(*) as total FROM tax_info")
        total_records = cursor.fetchone()["total"]

        # Lọc dữ liệu nếu có giá trị tìm kiếm
        if search_value:
            query = """
                SELECT * FROM tax_info
                WHERE tax_id LIKE %s OR name LIKE %s OR address LIKE %s
                ORDER BY id DESC
                LIMIT %s OFFSET %s
            """
            params = (f"%{search_value}%", f"%{search_value}%", f"%{search_value}%", length, start)
            cursor.execute(query, params)

            # Lấy tổng số bản ghi sau khi lọc
            cursor.execute("""
                SELECT COUNT(*) as total FROM tax_info
                WHERE tax_id LIKE %s OR name LIKE %s OR address LIKE %s
            """, (f"%{search_value}%", f"%{search_value}%", f"%{search_value}%"))
            total_filtered = cursor.fetchone()["total"]
        else:
            query = """
                SELECT * FROM tax_info
                ORDER BY id DESC
                LIMIT %s OFFSET %s
            """
            params = (length, start)
            cursor.execute(query, params)

            # Tổng số bản ghi sau khi lọc là tổng số bản ghi ban đầu
            total_filtered = total_records

        records = cursor.fetchall()

        # Đóng kết nối
        cursor.close()
        connection.close()

        # Chuẩn bị JSON trả về cho DataTables
        return jsonify({
            "draw": draw,
            "recordsTotal": total_records,  # Tổng số bản ghi trong database
            "recordsFiltered": total_filtered,  # Tổng số bản ghi sau khi lọc (nếu có)
            "data": records  # Dữ liệu trả về
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@bp.route("/api/get-users", methods=["POST"])
def api_get_users():
    try:
        # Lấy dữ liệu JSON từ body
        data = request.get_json()
        draw = int(data.get("draw", 1))  # Số lần gửi request
        start = int(data.get("start", 0))  # Bản ghi bắt đầu
        length = int(data.get("length", 10))  # Số bản ghi trên mỗi trang
        search_value = data.get("search", {}).get("value", "").strip()  # Giá trị tìm kiếm

        # Kết nối database
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # Lấy tổng số bản ghi
        cursor.execute("SELECT COUNT(*) as total FROM users")
        total_records = cursor.fetchone()["total"]

        # Lọc dữ liệu nếu có giá trị tìm kiếm
        if search_value:
            query = """
                SELECT * FROM users
                WHERE username LIKE %s OR email LIKE %s
                ORDER BY id DESC
                LIMIT %s OFFSET %s
            """
            params = (f"%{search_value}%", f"%{search_value}%", length, start)
            cursor.execute(query, params)

            # Lấy tổng số bản ghi sau khi lọc
            cursor.execute("""
                SELECT COUNT(*) as total FROM users
                WHERE username LIKE %s OR email LIKE %s 
            """, (f"%{search_value}%", f"%{search_value}%"))
            total_filtered = cursor.fetchone()["total"]
        else:
            query = """
                SELECT * FROM users
                ORDER BY id DESC
                LIMIT %s OFFSET %s
            """
            params = (length, start)
            cursor.execute(query, params)

            # Tổng số bản ghi sau khi lọc là tổng số bản ghi ban đầu
            total_filtered = total_records

        records = cursor.fetchall()

        # Đóng kết nối
        cursor.close()
        connection.close()

        # Chuẩn bị JSON trả về cho DataTables
        return jsonify({
            "draw": draw,
            "recordsTotal": total_records,  # Tổng số bản ghi trong database
            "recordsFiltered": total_filtered,  # Tổng số bản ghi sau khi lọc (nếu có)
            "data": records  # Dữ liệu trả về
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

