import mysql.connector
import json
import os
import traceback

# Kết nối MySQL
def db_connection():
    connection = mysql.connector.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        port=os.getenv('DB_PORT'),
        database=os.getenv('DB_NAME'),
        pool_size=5,
        connection_timeout=300
    )
    return connection