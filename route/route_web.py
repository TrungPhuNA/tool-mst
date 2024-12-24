from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from tool.crawler import crawl_masothue, crawlerList, extract_details_from_link
from flask_login import login_required, current_user
from models.model_user import User
from models.model_callback import CallbackInfo

import traceback
import math

# Tạo Blueprint cho các route
bp = Blueprint('route_web', __name__)


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

@bp.route("/callbacks", methods=["GET"])
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