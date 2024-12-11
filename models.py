import mysql.connector
import json
import os

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
            name VARCHAR(255),
            address TEXT,
            status VARCHAR(255),
            representative VARCHAR(255),
            management VARCHAR(255),
            active_date DATE,
            source_url TEXT
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

    # Chèn dữ liệu mới
    cursor.execute("""
        INSERT INTO tax_info (tax_id, name, address, status, representative, management, active_date, source_url)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        data['id'],
        data['name'],
        data['address'],
        data['status'],
        data['representative'],
        data['management'],
        data['activeDate'],
        data['source_url']
    ))

    connection.commit()
    cursor.close()
    connection.close()
    print("Data inserted into DB successfully!")
    return data  # Trả về dữ liệu vừa được chèn
