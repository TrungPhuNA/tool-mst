from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from bs4 import BeautifulSoup
from models.model_tax_info import save_to_db, update_crawler_status
import os

import json
import traceback
import time


def crawl_masothue(query):
    environment = os.getenv('APP_ENV')
    print("============ environment =========== ", environment)
    if environment == 'development':
        driver = initDriveLocal()
    else:
        driver = initDriveProd()

    try:
        url = "https://masothue.com/"
        driver.get(url)
        print("========= Mở URL crawler: ", url)

        # Tìm ô input và nhập query
        search_box = WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='q']"))
        )
        search_box.clear()
        search_box.send_keys(query)
        search_box.send_keys(Keys.RETURN)
        print("========= Input Search ", search_box)

        # Kiểm tra modal
        is_modal_shown = False  # Flag để kiểm tra modal
        try:
            WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.ID, "modal-inform"))
            )
            modal_body = WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "#modal-inform .modal-body"))
            )

            modal_message = modal_body.text.strip()
            print("========= Text modal thông báo: ", repr(modal_message))

            if modal_message:
                is_modal_shown = True
                print("============ STOP =========== [01]")
                return {
                    "code": "01",
                    "desc": "Failed - " + modal_message,  # Sử dụng dấu +
                    "error_message": modal_message,
                    "data": None
                }
        except Exception:
            print("========= Không có modal thông báo.")

        # Dừng luôn nếu modal đã hiển thị
        if is_modal_shown:
            return

        # Nếu không có modal => tiếp tục redirect
        print("=========== REDIRECT =========== ")

        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "table.table-taxinfo"))
        )

        current_url = driver.current_url
        print(f"Redirected to: {current_url}")

        # Lấy HTML của trang đích
        soup = BeautifulSoup(driver.page_source, "html.parser")
        tax_info = parse_tax_info(soup)
        if not tax_info:
            raise ValueError("Không tìm thấy dữ liệu.")

        tax_info["source_url"] = current_url
        tax_info["param_search"] = query

        return {
            "code": "00",
            "desc": "Success - Thành công",
            "data": tax_info,
            "source_url": current_url
        }

    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()
        return None

    finally:
        driver.quit()


def parse_tax_info(soup):
    tax_id = ""
    name = ""
    h1_tag = soup.select_one("h1.h1")
    if h1_tag:
        tax_id = h1_tag.text.split(" - ")[0].strip()
        name = h1_tag.text.split(" - ")[1].strip()

    tax_info_table = soup.select_one("table.table-taxinfo")
    tax_info = {}
    if tax_info_table:
        rows = tax_info_table.select("tbody tr")
        for row in rows:
            try:
                key = row.select_one("td:nth-child(1)").text.strip()
                value = row.select_one("td:nth-child(2)").text.strip()
                tax_info[key] = value
            except AttributeError:
                continue  # Nếu thiếu dữ liệu trong một dòng, bỏ qua dòng đó

    # Định dạng lại tax_info thành key-value cụ thể
    formatted_tax_info = {
        "id": tax_id,
        "name": name,
        "internationalName": tax_info.get("Tên quốc tế", ""),
        "shortName": tax_info.get("Tên viết tắt", ""),
        "address": tax_info.get("Địa chỉ", ""),
        "status": tax_info.get("Tình trạng", ""),
        "representative": tax_info.get("Người đại diện", ""),
        "management": tax_info.get("Quản lý bởi", ""),
        "activeDate": tax_info.get("Ngày hoạt động", "")
    }

    return formatted_tax_info


def initDriveProd():
    selenium_grid_url = "http://localhost:4444/wd/hub"
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')

    driver = webdriver.Remote(
        command_executor=selenium_grid_url,
        options=chrome_options
    )
    return driver

def initDriveLocal():
    options = webdriver.ChromeOptions()
    options.add_argument("--window-size=800,600")  # Chiều rộng 600px, chiều cao 800px
    options.add_argument("--disable-extensions")  # Tắt các extension
    driver = webdriver.Chrome(options=options)
    return driver

def crawlerList(url):
    print("URL => ", url)
    driver = initDriveLocal()

    try:
        driver.get(url)
        time.sleep(3)
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CLASS_NAME, "tax-listing"))
        )
        print("Tìm thấy phần tử 'tax-listing'")
    except TimeoutException:
        print("Không tìm thấy phần tử 'tax-listing'. Kiểm tra lại selector hoặc thời gian chờ.")

    # Lấy nội dung HTML của trang sau khi load
    soup = BeautifulSoup(driver.page_source, "html.parser")

    tax_elements = soup.find_all("div", {"data-prefetch": True})

    links = []
    for tax_element in tax_elements:
        mst_link = tax_element.find("a", href=True)
        if mst_link:
            href = mst_link['href']
            if href.startswith("/"):  # Chỉ lấy link nội bộ
                full_link = "https://masothue.com" + href
                links.append(full_link)

    return links


def extract_details_from_link(links):
    driver = initDriveLocal()
    tax = []
    for link in links:
        print(f"Đang xử lý link: {link}")
        driver.get(link)
        time.sleep(2)  # Chờ trang tải xong

        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "table.table-taxinfo"))
        )

        current_url = driver.current_url
        print(f"Redirected to: {current_url}")

        # Lấy HTML của trang đích
        soup = BeautifulSoup(driver.page_source, "html.parser")
        tax_info = parse_tax_info(soup)
        if not tax_info:
            raise ValueError("Không tìm thấy dữ liệu.")

        tax_info["source_url"] = current_url
        tax_info["param_search"] = tax_info["id"]
        print("======== tax_info", tax_info["id"])

        save_to_db(tax_info)  # Chèn vào DB
        update_crawler_status(tax_info["id"], 'success')  # Cập nhật trạng thái thành công

        tax.append(tax_info)

    return  tax