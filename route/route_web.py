from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from tool.crawler import crawl_masothue, crawlerList, extract_details_from_link
from flask_login import login_required, current_user
from models.model_user import User
from models.model_callback import CallbackInfo

import traceback
import math
import os

# Tạo Blueprint cho các route
bp = Blueprint('route_web', __name__)


LOG_FILES = {
    "nohup": "nohup.out",
    "gunicorn_error": "gunicorn_error.log"
}

@bp.route("/logs/table/<log_type>")
def logs_table(log_type):
    """API hiển thị log dưới dạng JSON."""
    if log_type not in LOG_FILES:
        return jsonify({"error": "Invalid log type"}), 400

    log_path = LOG_FILES[log_type]

    if not os.path.exists(log_path):
        return jsonify({"error": f"Log file '{log_path}' not found"}), 404

    try:
        with open(log_path, "r", encoding="utf-8") as log_file:
            # Đọc nội dung log
            lines = log_file.readlines()[-500:]  # Lấy 500 dòng cuối
            logs = []
            for i, line in enumerate(reversed(lines)):
                logs.append({"id": i + 1, "content": line.strip()})
        return jsonify({"data": logs})
    except Exception as e:
        return jsonify({"error": f"Unable to read log file: {e}"}), 500

@bp.route("/logs/<log_type>")
def view_logs_table(log_type):
    """Hiển thị bảng log."""
    if log_type not in LOG_FILES:
        return "Log type không hợp lệ!", 400
    return render_template("logs/log_view.html", log_type=log_type)


@bp.route("/", methods=["GET"])
@login_required
def tax_info_list():
    try:
        return render_template("tax_info_list.html")
    except Exception as e:
        traceback.print_exc()
        return f"An error occurred: {e}", 500



@bp.route("/users", methods=["GET"])
@login_required
def get_lists_users():
    try:
        users = User.get_all_users()
        return render_template("users/index.html",users=users)
    except Exception as e:
        traceback.print_exc()
        return f"An error occurred: {e}", 500

@bp.route("/logs/post-back", methods=["GET"])
@login_required
def get_lists_log_postback():
    try:
        users = User.get_all_users()
        return render_template("logs/post_back.html",users=users)
    except Exception as e:
        traceback.print_exc()
        return f"An error occurred: {e}", 500

@bp.route("/setup-post-back", methods=["GET"])
def manage_callbacks():
    callbacks = CallbackInfo.get_all()
    return render_template("callbacks/index.html", callbacks=callbacks)

@bp.route("/callbacks/add", methods=["GET", "POST"])
def add_callback_page():
    if request.method == "POST":
        url = request.form.get("url")
        method = request.form.get("method", "POST")
        auth_key = request.form.get("auth_key")
        user_id = request.form.get("user_id")  # Lấy user_id từ select
        additional_info = request.form.get("additional_info")

        # Xử lý headers động
        header_keys = request.form.getlist("header_keys[]")
        header_values = request.form.getlist("header_values[]")
        headers = dict(zip(header_keys, header_values))

        if not url or not auth_key or not user_id:
            flash("Vui lòng nhập đầy đủ thông tin!", "danger")
            return redirect(url_for("route_web.manage_callbacks"))

        # Lưu callback vào database
        CallbackInfo.create(url, method, auth_key, user_id, additional_info, headers)
        flash("Callback đã được thêm thành công!", "success")
        return redirect(url_for("route_web.manage_callbacks"))

    users = User.get_all_users()
    return render_template("callbacks/create.html",users=users)

@bp.route("/callbacks/edit/<int:callback_id>", methods=["GET", "POST"])
def edit_callback_page(callback_id):
    from models.model_callback import CallbackInfo

    if request.method == "POST":
        url = request.form.get("url")
        method = request.form.get("method", "POST")
        auth_key = request.form.get("auth_key")
        user_id = request.form.get("user_id")
        additional_info = request.form.get("additional_info")

        # Xử lý headers động
        header_keys = request.form.getlist("header_keys[]")
        header_values = request.form.getlist("header_values[]")
        headers = dict(zip(header_keys, header_values))

        if not url or not auth_key or not user_id:
            flash("Vui lòng nhập đầy đủ thông tin!", "danger")
            return redirect(url_for("route_web.edit_callback_page", callback_id=callback_id))

        # Cập nhật callback trong database
        CallbackInfo.update(callback_id, url, method, auth_key, user_id, additional_info, headers)
        flash("Callback đã được cập nhật thành công!", "success")
        return redirect(url_for("route_web.manage_callbacks"))

    users = User.get_all_users()
    callback = CallbackInfo.get_by_id(callback_id)
    return render_template("callbacks/update.html", callback=callback,users=users)

@bp.route("/init", methods=["GET"])
def init_list():
    try:
        # Render giao diện với dữ liệu
        url = "https://masothue.com/tra-cuu-ma-so-thue-theo-tinh/xa-cam-thuong-5361"
        response = crawlerList(url)
        extract_details_from_link(response)
        return response
    except Exception as e:
        traceback.print_exc()
        return f"An error occurred: {e}", 500