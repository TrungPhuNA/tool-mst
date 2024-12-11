from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
# from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from bs4 import BeautifulSoup
import json


def crawl_masothue(query):

    selenium_grid_url = "http://localhost:4444/wd/hub"
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')

    # Kết nối với Docker container Selenium
    driver = webdriver.Remote(
        command_executor=selenium_grid_url,
        options=chrome_options
    )

    print("=================== driver",driver)
    try:
        # Mở trang web masothue.com
        driver.get("https://masothue.com/")

        # Tìm ô input và nhập query
        search_box = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='q']"))
        )
        search_box.clear()
        search_box.send_keys(query)
        search_box.send_keys(Keys.RETURN)

        # Đợi trang redirect
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "table.table-taxinfo"))
        )

        # Lấy URL trang đích
        current_url = driver.current_url
        print(f"Redirected to: {current_url}")

        # Lấy HTML của trang đích
        soup = BeautifulSoup(driver.page_source, "html.parser")

        # Trích xuất thông tin từ bảng "table-taxinfo"
        tax_info_table = soup.select_one("table.table-taxinfo")
        tax_info = {}
        if tax_info_table:
            rows = tax_info_table.select("tbody tr")
            for row in rows:
                cells = [cell.text.strip() for cell in row.select("td")]
                if len(cells) == 2:
                    tax_info[cells[0]] = cells[1]

        # Trích xuất các thông tin khác từ HTML
        name = soup.select_one("table.table-taxinfo th span.copy").text.strip() if soup.select_one("table.table-taxinfo th span.copy") else "N/A"

        # Trích xuất thông tin kinh doanh (nếu có)
        business_info = []
        business_table = soup.select_one("table.table")
        if business_table:
            for row in business_table.select("tbody tr"):
                columns = [cell.text.strip() for cell in row.select("td")]
                if len(columns) == 2:
                    business_info.append({"ID": columns[0], "Careers": columns[1]})

        # Tạo kết quả JSON
        result = {
            "name": name,
            "tax_info": tax_info,
            "business_info": business_info,
            "source_url": current_url,  # URL nguồn để tham chiếu
        }

        # Ghi ra file JSON
        with open("result.json", "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=4)

        return result

    except Exception as e:
        print(f"Error: {e}")
        return None

    finally:
        driver.quit()


if __name__ == "__main__":
    query = "8489390028"  # Thay bằng MST hoặc CCCD bạn muốn tìm
    result = crawl_masothue(query)
    if result:
        print(json.dumps(result, ensure_ascii=False, indent=4))
    else:
        print("No data found.")
