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


# Lưu dữ liệu vào MySQL
def save_to_db(data):

    print("============== DATA SAVE DB =========== ",data)
    connection = get_db_connection()
    cursor = connection.cursor()

    # Tạo bảng nếu chưa có
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tax_info (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255),
            tax_info JSON,
            business_info JSON,
            source_url TEXT
        )
    """)

    # Chèn dữ liệu
    cursor.execute("""
        INSERT INTO tax_info (name, tax_info, business_info, source_url)
        VALUES (%s, %s, %s, %s)
    """, (
        data['name'],
        json.dumps(data['tax_info']),
        json.dumps(data['business_info']),
        data['source_url']
    ))

    connection.commit()
    cursor.close()
    connection.close()
