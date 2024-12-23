from flask import Blueprint, request, jsonify, render_template
from tool.crawler import crawl_masothue
from models.model_tax_info import save_to_db, get_db_connection, save_data_error_to_db, update_crawler_status
import traceback
import math

# Tạo Blueprint cho các route
bp = Blueprint('route_web', __name__)


@bp.route("/", methods=["GET"])
def tax_info_list():
    try:
        # Lấy tham số tìm kiếm và phân trang
        # search_query = request.args.get("search", "").strip()
        # page = int(request.args.get("page", 1))
        # limit = 2
        # offset = (page - 1) * limit
        #
        # # Kết nối database
        # connection = get_db_connection()
        # cursor = connection.cursor(dictionary=True)
        #
        # # Query dữ liệu với sắp xếp theo id giảm dần
        # if search_query:
        #     cursor.execute("""
        #         SELECT * FROM tax_info
        #         WHERE tax_id LIKE %s OR name LIKE %s OR address LIKE %s
        #         ORDER BY id DESC
        #         LIMIT %s OFFSET %s
        #     """, (f"%{search_query}%", f"%{search_query}%", f"%{search_query}%", limit, offset))
        # else:
        #     cursor.execute("""
        #         SELECT * FROM tax_info
        #         ORDER BY id DESC
        #         LIMIT %s OFFSET %s
        #     """, (limit, offset))
        #
        # tax_info_list = cursor.fetchall()
        #
        # # Đếm tổng số bản ghi để tính tổng số trang
        # if search_query:
        #     cursor.execute("""
        #         SELECT COUNT(*) as total FROM tax_info
        #         WHERE tax_id LIKE %s OR name LIKE %s OR address LIKE %s
        #     """, (f"%{search_query}%", f"%{search_query}%", f"%{search_query}%"))
        # else:
        #     cursor.execute("SELECT COUNT(*) as total FROM tax_info")
        # total = cursor.fetchone()["total"]
        # total_pages = math.ceil(total / limit)
        #
        # cursor.close()
        # connection.close()

        # Render giao diện với dữ liệu
        return render_template("tax_info_list.html")
    except Exception as e:
        traceback.print_exc()
        return f"An error occurred: {e}", 500