import mysql.connector
import json
import os
import traceback
from datetime import datetime, timedelta
# __all__ = ["save_to_db", "get_db_connection"]

# Kết nối MySQL
def get_db_connection():
    connection = mysql.connector.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        port=os.getenv('DB_PORT'),
        database=os.getenv('DB_NAME'),
    )
    return connection


def save_to_db(data):
    print("============== DATA SAVE DB =========== ", data)
    connection = get_db_connection()
    cursor = connection.cursor()

    # Tạo bảng nếu chưa có
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tax_info (
            id INT AUTO_INCREMENT PRIMARY KEY,
            tax_id VARCHAR(50) UNIQUE,
            name VARCHAR(255) NULL,
            address TEXT NULL,
            status VARCHAR(255) NULL,
            representative VARCHAR(255) NULL,
            international_name VARCHAR(255) NULL,
            management VARCHAR(255) NULL,
            active_date DATE NULL,
            param_search VARCHAR(255) NULL,
            source_url TEXT NULL
        )
    """)

    # Kiểm tra nếu tax_id đã tồn tại trong DB
    cursor.execute("SELECT * FROM tax_info WHERE tax_id = %s", (data['id'],))
    result = cursor.fetchone()
    if result:
        print("Data already exists in DB:", result)
        cursor.close()
        connection.close()
        return result  # Trả về dữ liệu từ DB nếu đã tồn tại

    try:
        # Xử lý active_date
        active_date = data.get('activeDate', '').strip()  # Lấy giá trị hoặc chuỗi rỗng nếu không có
        if not active_date:  # Nếu là chuỗi rỗng, gán thành None
            active_date = None

        print("============== activeDate =========== ", active_date)

        # Chèn dữ liệu mới
        cursor.execute("""
            INSERT INTO tax_info (tax_id, name, address, status, representative, management, active_date, source_url, international_name, param_search)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            data['id'],
            data['name'],
            data['address'],
            data['status'],
            data['representative'],
            data['management'],
            active_date,
            data['source_url'],
            data['internationalName'],
            data['param_search']
        ))

        connection.commit()
        print("Data inserted into DB successfully!")
        return data  # Trả về dữ liệu vừa được chèn
    except Exception as e:
        print(f"Error during INSERT: {e}")
        traceback.print_exc()
        raise  # Gây lỗi lại để debug rõ hơn
    finally:
        cursor.close()
        connection.close()

def save_data_error_to_db(data):
    print("============== DATA SAVE DB ERROR =========== ", data)
    connection = get_db_connection()
    cursor = connection.cursor()

    # Kiểm tra nếu param_search đã tồn tại trong DB
    cursor.execute("SELECT * FROM tax_info WHERE param_search = %s", (data['param_search'],))
    result = cursor.fetchone()

    # Nếu tồn tại, chỉ cập nhật trạng thái nếu có thay đổi
    if result:
        print("Params already exists in DB:", result)
        try:
            # Nếu crawler đã thành công nhưng bị lỗi thì cập nhật lại trạng thái và retry_time
            if result['crawler_status'] == 'error' and (result['retry_time'] is None or result['retry_time'] < datetime.now()):
                cursor.execute("""
                    UPDATE tax_info
                    SET crawler_status = 'retry',
                        retry_time = %s
                    WHERE param_search = %s
                """, (datetime.now() + timedelta(minutes=5), data['param_search']))
                connection.commit()
                print(f"Retrying crawler for {data['param_search']} after 5 minutes.")
        except Exception as e:
            print(f"Error during update: {e}")
            traceback.print_exc()
        cursor.close()
        connection.close()
        return result  # Trả về dữ liệu từ DB nếu đã tồn tại

    # Nếu không tồn tại, thêm dữ liệu mới
    try:
        # Cập nhật trạng thái khi bắt đầu crawler
        cursor.execute("""INSERT INTO tax_info (param_search, crawler_status) VALUES (%s, 'retry') """, (
            data['param_search'],
        ))
        connection.commit()
        print("Data inserted into DB with retry status!")
    except Exception as e:
        print(f"Error during INSERT: {e}")
        traceback.print_exc()
        raise  # Gây lỗi lại để debug rõ hơn

    cursor.close()
    connection.close()

    return data  # Trả về dữ liệu vừa được chèn


def update_crawler_status(param_search, status):
    # Hàm này dùng để cập nhật trạng thái crawler (thành công hoặc lỗi)
    connection = get_db_connection()
    cursor = connection.cursor()

    if status == 'success':
        # Cập nhật thành công
        cursor.execute("""
            UPDATE tax_info
            SET crawler_status = 'success',
                retry_time = NULL
            WHERE param_search = %s
        """, (param_search,))
    elif status == 'error':
        # Cập nhật khi có lỗi và cần retry
        cursor.execute("""
            UPDATE tax_info
            SET crawler_status = 'error',
                retry_time = %s
            WHERE param_search = %s
        """, (datetime.now() + timedelta(minutes=5), param_search))

    connection.commit()
    cursor.close()
    connection.close()
    print(f"Updated crawler status for {param_search} to {status}")