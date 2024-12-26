from flask import Blueprint, request, jsonify, render_template
from tool.crawler import crawl_masothue
from models.model_tax_info import save_to_db, get_db_connection, save_data_error_to_db, update_crawler_status
from models.model_callback import CallbackInfo
from datetime import datetime
import traceback
import threading
import math
import requests
import json
import time

# Tạo Blueprint cho các route
bp = Blueprint('route_api_crawler', __name__)

@bp.route("/api/v2/get-tax-info", methods=["GET"])
def get_tax_info_v2():
    param = request.args.get("param")
    auth_key = request.args.get("auth_key")
    request_id = request.args.get("request_id")
    print("==========get_tax_info_v2 params :  ", param, auth_key, request_id)
    if not param or not auth_key or not request_id:
        return jsonify({"error": "Missing required parameters 'param', 'auth_key', or 'request_id'"}), 400

    connection = get_db_connection()
    print("connection : ", connection)
    try:
        with connection.cursor(dictionary=True) as cursor:
            # Truy vấn thông tin callback dựa trên auth_key
            cursor.execute("SELECT * FROM callback_info WHERE auth_key = %s", (auth_key,))
            callback_info = cursor.fetchone()
            if not callback_info:
                return jsonify({"error": "Invalid auth_key or no callback configuration found"}), 401

        with connection.cursor(dictionary=True) as cursor:
            # Kiểm tra nếu mã số thuế đã tồn tại trong log
            cursor.execute("SELECT * FROM tax_request_log WHERE param = %s AND request_id = %s", (param, request_id))
            request_log = cursor.fetchone()
            print('========== request_log: ', request_log)
            if request_log:
                if request_log['crawler_status'] in ['init', 'retry','error']:
                    threading.Thread(target=process_crawler_request, args=(param, request_id, callback_info)).start()
                    return jsonify({
                        "code": "99",
                        "desc": "Crawler is still processing, please try again later",
                        "data": {},
                        "request_id": request_id
                    }), 202

                if request_log['crawler_status'] == 'success':
                    cursor.execute("SELECT * FROM tax_info WHERE param_search = %s", (param,))
                    result = cursor.fetchone()
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
                        },
                        "request_id": request_id
                    }), 200


        with connection.cursor(dictionary=True) as cursor:
            # Nếu không có log, tạo request mới
            cursor.execute(
                "INSERT INTO tax_request_log (param, request_id, crawler_status, callback_id) VALUES (%s, %s, 'init', %s)",
                (param, request_id, callback_info['id'])
            )
            connection.commit()

        threading.Thread(target=process_crawler_request, args=(param, request_id, callback_info)).start()

        return jsonify({
            "code": "01",
            "desc": "Request accepted, processing",
            "data": {},
            "request_id": request_id
        }), 202

    finally:
        connection.close()

def process_crawler_request(param, request_id, callback_info):
    print("============= process_crawler_request ======= ", param, request_id)
    start_time = time.time()
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    # Crawl dữ liệu
    result = crawl_masothue(param)

    if result and result["code"] == "00":
        end_time = time.time()
        duration = end_time - start_time
        result["data"]["crawler_status"] = "success"
        result["data"]["duration"] = duration
        # Lưu dữ liệu vào bảng tax_info
        dataInsert = save_to_db(result["data"])
        print("============ dataInsert: ", dataInsert)
        tax_info_id = dataInsert["tax_info_id"]
        # Cập nhật trạng thái và liên kết với tax_info_id
        cursor.execute(
            "UPDATE tax_request_log SET crawler_status = 'success', tax_info_id = %s, duration_process = %s WHERE param = %s AND request_id = %s",
            (tax_info_id, result["data"].get("duration", 0), param, request_id)
        )

        # Gửi postback
        success = send_postback_success(param, request_id, result["data"], callback_info)
        cursor.execute(
            """
            UPDATE tax_request_log 
            SET postback_status = %s 
            WHERE param = %s AND request_id = %s
            """,
            ("success" if success else "error", param, request_id)
        )
    else:
        # Xử lý lỗi và cập nhật trạng thái
        cursor.execute(
            "UPDATE tax_request_log SET crawler_status = 'error', retry_time = NOW() + INTERVAL 1 HOUR WHERE param = %s AND request_id = %s",
            (param, request_id)
        )
        # Gửi postback
        success = send_postback_error(param, request_id, callback_info)
        cursor.execute(
            """
            UPDATE tax_request_log 
            SET postback_status = %s 
            WHERE param = %s AND request_id = %s
            """,
            ("success" if success else "error", param, request_id)
        )

    connection.commit()
    cursor.close()

def send_postback_success(param, request_id, data, callback_info):
    """
    Gửi postback thành công với dữ liệu.

    Args:
        param (str): Tham số đầu vào từ người dùng (mã số thuế, căn cước công dân, ...).
        request_id (str): ID của request.
        data (dict): Dữ liệu từ crawler.
        callback_info (dict): Thông tin callback.
    """
    payload = {
        "query": param,
        "request_id": request_id,
        "data": data,
        "status": "success",
        "timestamp": datetime.now().isoformat()
    }
    return send_postback(callback_info, payload, method=callback_info['method'].upper())


def send_postback_error(param, request_id, callback_info):
    """
    Gửi postback thông báo lỗi.

    Args:
        param (str): Tham số đầu vào từ người dùng (mã số thuế, căn cước công dân, ...).
        request_id (str): ID của request.
        callback_info (dict): Thông tin callback.
    """
    payload = {
        "query": param,
        "request_id": request_id,
        "status": "error",
        "message": "Failed to process the request. Please try again later.",
        "timestamp": datetime.now().isoformat()
    }
    return send_postback(callback_info, payload, method=callback_info['method'].upper())



def send_postback(callback_info, payload, method="POST"):
    """
    Gửi postback đến URL được cấu hình trong callback_info.

    Args:
        callback_info (dict): Thông tin callback (URL, headers, auth_key, method).
        payload (dict): Dữ liệu cần gửi trong postback.
        method (str): Phương thức HTTP (POST, PUT, GET, DELETE). Mặc định là POST.
    """
    print("======== data payload post back: ", payload)
    url = callback_info['url']
    headers = json.loads(callback_info['headers']) if callback_info['headers'] else {}
    auth_key = callback_info['auth_key']

    # Thêm Authorization header nếu có auth_key
    if auth_key:
        headers['Authorization'] = f"Bearer {auth_key}"

    try:
        # Gửi request dựa trên phương thức HTTP
        if method == "POST":
            response = requests.post(url, json=payload, headers=headers)
        elif method == "PUT":
            response = requests.put(url, json=payload, headers=headers)
        elif method == "GET":
            response = requests.get(url, params=payload, headers=headers)
        elif method == "DELETE":
            response = requests.delete(url, json=payload, headers=headers)
        else:
            print(f"Unsupported HTTP method: {method}")
            return False

        print(f"Postback sent to {url}, response status: {response.status_code}, response: {response.text}")
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        print(f"Error sending postback: {e}")
        return False
