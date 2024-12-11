from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import traceback
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from bs4 import BeautifulSoup
import json


def crawl_masothue(query):
    selenium_grid_url = "http://localhost:4444/wd/hub"
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')

    driver = webdriver.Remote(
        command_executor=selenium_grid_url,
        options=chrome_options
    )

    try:
        # Mở trang web masothue.com
        driver.get("https://masothue.com/")

        # Tìm ô input và nhập query
        search_box = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='q']"))
        )
        search_box.clear()
        search_box.send_keys(query)
        search_box.send_keys(Keys.RETURN)

        # Đợi trang redirect
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "table.table-taxinfo"))
        )

        # Lấy URL trang đích
        current_url = driver.current_url
        print(f"Redirected to: {current_url}")

        # Lấy HTML của trang đích
        soup = BeautifulSoup(driver.page_source, "html.parser")
        tax_info = parse_tax_info(soup)
        if not tax_info:
            raise ValueError("Không tìm thấy dữ liệu.")
        
        tax_info["source_url"] = current_url

        # Tạo kết quả JSON
        result = {
            "code": "00",
            "desc": "Success - Thành công",
            "data": tax_info,
            "source_url": current_url
        }

        # Ghi ra file JSON
        with open("result.json", "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=4)

        return result

    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()
        return None

    finally:
        driver.quit()

def parse_tax_info(soup):
    tax_id = ""
    h1_tag = soup.select_one("h1.h1")
    if h1_tag:
        tax_id = h1_tag.text.split(" - ")[0].strip()  # Lấy phần mã số thuế trước dấu " - "

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
        "name": tax_info.get("Tên người nộp thuế", ""),
        "internationalName": tax_info.get("Tên quốc tế", ""),
        "shortName": tax_info.get("Tên viết tắt", ""),
        "address": tax_info.get("Địa chỉ", ""),
        "status": tax_info.get("Tình trạng", ""),
        "representative": tax_info.get("Người đại diện", ""),
        "management": tax_info.get("Quản lý bởi", ""),
        "activeDate": tax_info.get("Ngày hoạt động", "")
    }

    return formatted_tax_info

if __name__ == "__main__":
    query = "8489390028"  # Thay bằng MST hoặc CCCD bạn muốn tìm
    result = crawl_masothue(query)
    if result:
        print(json.dumps(result, ensure_ascii=False, indent=4))
    else:
        print("No data found.")
