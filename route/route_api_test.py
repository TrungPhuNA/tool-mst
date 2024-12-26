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

import hashlib
import mysql.connector
from mysql.connector import Error
import concurrent.futures

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
def api_fetch_location():
    base_url = "https://masothue.com/"
    print("========== Bắt đầu crawler từ URL: ", base_url)

    # Selenium driver
    driver = initDriveLocal()

    # Mở trang chính và lấy danh sách tỉnh/thành
    driver.get(base_url)
    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.CLASS_NAME, "sidebar-blog"))
    )
    soup = BeautifulSoup(driver.page_source, "html.parser")
    sidebar = soup.find("aside", class_="widget_categories")

    province_links = []
    if sidebar:
        links = sidebar.find_all("a", href=True)
        for link in links:
            province_href = link['href']
            province_text = link.get_text(strip=True)
            if province_href.startswith("/"):
                full_link = base_url.rstrip("/") + province_href
                save_link_to_db("province", province_text, full_link)
                province_links.append((province_text, full_link))

    # Xử lý các tỉnh/thành bất đồng bộ
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        for province_text, province_link in province_links:
            executor.submit(process_link, driver, "province", province_text, province_link)

    driver.quit()
    return jsonify({
        "code": "00",
        "desc": "Success - Thành công",
    }), 200


def close_ads(driver):
    try:
        # Chờ iframe của quảng cáo xuất hiện
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "iframe[id^='aswift']"))
        )
        print("Quảng cáo xuất hiện, thử đóng...")

        # Chuyển vào iframe quảng cáo
        ad_iframe = driver.find_element(By.CSS_SELECTOR, "iframe[id^='aswift']")
        driver.switch_to.frame(ad_iframe)

        # Tìm và nhấn nút đóng
        close_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "div[aria-label='Close']"))
        )
        close_button.click()
        print("Đã đóng quảng cáo.")

        # Chuyển lại frame chính
        driver.switch_to.default_content()
    except TimeoutException:
        print("Không tìm thấy quảng cáo hoặc nút đóng trong thời gian giới hạn.")
    except NoSuchElementException:
        print("Không tìm thấy nút đóng quảng cáo.")
    except Exception as e:
        print(f"Lỗi khi đóng quảng cáo: {e}")
    finally:
        # Chuyển lại frame chính để tiếp tục xử lý
        driver.switch_to.default_content()


@bp.route("/api/crawl-locations", methods=["GET"])
def api_crawl_locations():
    driver = initDriveLocal()

    try:
        # Xử lý cấp tỉnh/thành -> quận/huyện
        print("==== Bắt đầu xử lý quận/huyện...")
        # process_level_links("province", "district", driver)

        # Xử lý cấp quận/huyện -> phường/xã
        print("==== Bắt đầu xử lý phường/xã...")
        process_level_links("district", "ward", driver)
    except Exception as e:
        print(f"Đã xảy ra lỗi: {e}")
    finally:
        driver.quit()

    return jsonify({
        "code": "00",
        "desc": "Success - Thành công"
    }), 200


def process_link(driver, level, text, link):
    """Xử lý từng link (tỉnh/thành, quận/huyện, phường/xã)."""
    try:
        print(f"Đang xử lý {level}: {text} - {link}")
        driver.get(link)
        time.sleep(2)  # Thời gian chờ để đảm bảo trang tải xong
        save_link_to_db(level, text, link, status="success")
    except Exception as e:
        print(f"Lỗi khi xử lý {level}: {link} - {e}")
        update_link_status(link, status="error", error_message=str(e))


def process_level_links(level_from, level_to, driver):
    """Xử lý các link từ một cấp (level_from) đến cấp tiếp theo (level_to)."""
    print("=========== init process_level_links =========== ")
    links = get_links_by_status(level_from, status="error")
    # links = get_links_by_status(level_from, status="pending")
    print("============= links ==========", links)
    for link in links:
        try:
            print(f"Đang xử lý {level_from}: {link['text']} - {link['link']}")
            driver.get(link['link'])

            # Chờ trang tải
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CLASS_NAME, "sidebar-blog"))
            )

            # Lấy link cấp tiếp theo
            soup = BeautifulSoup(driver.page_source, "html.parser")
            sidebar = soup.find("aside", class_="widget_categories")
            if sidebar:
                sub_links = sidebar.find_all("a", href=True)
                for sub_link in sub_links:
                    href = sub_link['href']
                    text = sub_link.get_text(strip=True)
                    if href.startswith("/"):
                        full_link = "https://masothue.com" + href
                        print(f"==== {level_to}: {text}, Link: {full_link}")
                        save_link_to_db(level_to, text, full_link)

            # Cập nhật trạng thái của link hiện tại thành "success"
            update_link_status(link['link'], status="success")
        except Exception as e:
            print(f"Lỗi khi xử lý {level_from}: {link['link']} - {e}")
            update_link_status(link['link'], status="error", error_message=str(e))

    print("============ Done for Link ============= ")


def get_links_by_status(level, status='pending'):
    """Lấy danh sách link theo trạng thái từ MySQL."""
    connection = init_db_connection()
    if connection is None:
        return []

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT * FROM crawler_links
            WHERE level = %s AND status = %s
        """, (level, status))
        return cursor.fetchall()
    except Error as e:
        print(f"Lỗi khi lấy danh sách link: {e}")
        return []
    finally:
        cursor.close()
        connection.close()


def init_db_connection():
    """Khởi tạo kết nối MySQL."""
    try:
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            port=os.getenv('DB_PORT'),
            database=os.getenv('DB_NAME'),
        )
        return connection
    except Error as e:
        print(f"Lỗi kết nối MySQL: {e}")
        return None

def save_link_to_db(level, text, link, status='pending'):
    """Lưu link vào cơ sở dữ liệu."""
    connection = init_db_connection()
    if connection is None:
        return

    link_md5 = hashlib.md5(link.encode('utf-8')).hexdigest()
    try:
        cursor = connection.cursor()
        # Kiểm tra và chèn link mới nếu chưa tồn tại
        cursor.execute("""
            INSERT IGNORE INTO crawler_links (level, text, link, link_md5, status)
            VALUES (%s, %s, %s, %s, %s)
        """, (level, text, link, link_md5, status))
        connection.commit()
        print(f"Đã lưu link: {text} - {link}")
    except Error as e:
        print(f"Lỗi lưu link: {e}")
    finally:
        cursor.close()
        connection.close()

def update_link_status(link, status, error_message=None):
    """Cập nhật trạng thái link."""
    connection = init_db_connection()
    if connection is None:
        return

    link_md5 = hashlib.md5(link.encode('utf-8')).hexdigest()
    try:
        cursor = connection.cursor()
        cursor.execute("""
            UPDATE crawler_links
            SET status = %s, error_message = %s
            WHERE link_md5 = %s
        """, (status, error_message, link_md5))
        connection.commit()
        print(f"Đã cập nhật trạng thái link: {link} -> {status}")
    except Error as e:
        print(f"Lỗi cập nhật trạng thái link: {e}")
    finally:
        cursor.close()
        connection.close()