import mysql.connector
import json
import os
import traceback
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
            INSERT INTO tax_info (tax_id, name, address, status, representative, management, active_date, source_url, international_name)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            data['id'],
            data['name'],
            data['address'],
            data['status'],
            data['representative'],
            data['management'],
            active_date,
            data['source_url'],
            data['internationalName']
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
