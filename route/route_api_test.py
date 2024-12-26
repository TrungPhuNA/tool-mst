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

from tool.crawler import *

# Tạo Blueprint cho các route
bp = Blueprint('route_api_test', __name__)


@bp.route("/api/fetch-url", methods=["GET"])
def api_fetch_url():
    base_url = "https://masothue.com/tra-cuu-ma-so-thue-theo-tinh/ha-noi-7"
    print("========== Bắt đầu crawler từ URL: ", base_url)
    driver = initDriveLocal()

    all_links = []
    page = 1

    while True:
        # Mở URL của trang hiện tại
        url = f"{base_url}?page={page}"
        print("========== Mở URL crawler: ", url)
        driver.get(url)

        # Chờ trang tải xong
        try:
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CLASS_NAME, "tax-listing"))
            )
        except Exception as e:
            print(f"Trang {page} không thể tải: {e}")
            break

        # Lấy nội dung HTML của trang
        soup = BeautifulSoup(driver.page_source, "html.parser")

        # Tìm các phần tử có chứa thông tin link
        tax_elements = soup.find_all("div", {"data-prefetch": True})
        if not tax_elements:
            print(f"Không tìm thấy dữ liệu trên trang {page}. Kết thúc phân trang.")
            break

        # Thu thập dữ liệu từ các phần tử
        for tax_element in tax_elements:
            mst_link = tax_element.find("a", href=True)
            if mst_link:
                href = mst_link['href']
                text = mst_link.get_text(strip=True)  # Lấy nội dung text trong thẻ <a>
                if href.startswith("/"):  # Chỉ lấy link nội bộ
                    full_link = "https://masothue.com" + href
                    print(f"==== Link crawler: {full_link}, Text: {text}")
                    # Tạo dictionary để lưu link và text
                    item = {
                        "link": full_link,
                        "text": text
                    }
                    all_links.append(item)

        # Kiểm tra nếu có trang tiếp theo
        pagination = soup.find("ul", class_="page-numbers")
        if not pagination or not pagination.find("a", {"href": f"?page={page + 1}"}):
            print(f"Không có trang tiếp theo. Kết thúc tại trang {page}.")
            break

        # Tăng trang
        page += 1

    # Lưu dữ liệu vào file JSON
    output_file = "all_links.json"
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(all_links, f, ensure_ascii=False, indent=4)
        print(f"Danh sách link đã được lưu vào file: {output_file}")
    except Exception as e:
        print(f"Đã xảy ra lỗi khi lưu file JSON: {e}")

    # Đóng driver
    driver.quit()

    return jsonify({
        "code": "00",
        "desc": "Success - Thành công",
        "total_links": len(all_links),
        "links": all_links
    }), 200



@bp.route("/api/fetch-location", methods=["GET"])
def api_fetch_url():
    base_url = "https://masothue.com/"
    print("========== Bắt đầu crawler từ URL: ", base_url)
    driver = initDriveLocal()

    all_links = []
    page = 1

    while True:
        # Mở URL của trang hiện tại
        url = f"{base_url}?page={page}"
        print("========== Mở URL crawler: ", url)
        driver.get(url)

        # Chờ trang tải xong
        try:
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CLASS_NAME, "tax-listing"))
            )
        except Exception as e:
            print(f"Trang {page} không thể tải: {e}")
            break

        # Lấy nội dung HTML của trang
        soup = BeautifulSoup(driver.page_source, "html.parser")

        # Tìm các phần tử có chứa thông tin link
        tax_elements = soup.find_all("div", {"data-prefetch": True})
        if not tax_elements:
            print(f"Không tìm thấy dữ liệu trên trang {page}. Kết thúc phân trang.")
            break

        # Thu thập dữ liệu từ các phần tử
        for tax_element in tax_elements:
            mst_link = tax_element.find("a", href=True)
            if mst_link:
                href = mst_link['href']
                text = mst_link.get_text(strip=True)  # Lấy nội dung text trong thẻ <a>
                if href.startswith("/"):  # Chỉ lấy link nội bộ
                    full_link = "https://masothue.com" + href
                    print(f"==== Link crawler: {full_link}, Text: {text}")
                    # Tạo dictionary để lưu link và text
                    item = {
                        "link": full_link,
                        "text": text
                    }
                    all_links.append(item)

        # Kiểm tra nếu có trang tiếp theo
        pagination = soup.find("ul", class_="page-numbers")
        if not pagination or not pagination.find("a", {"href": f"?page={page + 1}"}):
            print(f"Không có trang tiếp theo. Kết thúc tại trang {page}.")
            break

        # Tăng trang
        page += 1

    # Lưu dữ liệu vào file JSON
    output_file = "all_links.json"
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(all_links, f, ensure_ascii=False, indent=4)
        print(f"Danh sách link đã được lưu vào file: {output_file}")
    except Exception as e:
        print(f"Đã xảy ra lỗi khi lưu file JSON: {e}")

    # Đóng driver
    driver.quit()

    return jsonify({
        "code": "00",
        "desc": "Success - Thành công",
    }), 200
