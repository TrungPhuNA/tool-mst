from flask import Blueprint, request, jsonify, render_template
from tool.crawler import crawl_masothue, crawlerList, extract_details_from_link
from flask_login import login_required, current_user
from models.model_tax_info import save_to_db, get_db_connection, save_data_error_to_db, update_crawler_status

import traceback
import math

# Tạo Blueprint cho các route
bp = Blueprint('route_web', __name__)


@bp.route("/", methods=["GET"])
@login_required
def tax_info_list():
    try:
        print(f"Chào {current_user.username}, bạn đã đăng nhập thành công!")
        # Render giao diện với dữ liệu
        return render_template("tax_info_list.html")
    except Exception as e:
        traceback.print_exc()
        return f"An error occurred: {e}", 500

@bp.route("/init", methods=["GET"])
def init_list():
    try:
        # Render giao diện với dữ liệu
        url = "https://masothue.com/tra-cuu-ma-so-thue-theo-tinh/khanh-hoa-26";
        response = crawlerList(url)
        extract_details_from_link(response)
        return response
    except Exception as e:
        traceback.print_exc()
        return f"An error occurred: {e}", 500