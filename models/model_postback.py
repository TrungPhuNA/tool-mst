from models.connect_db import db_connection
import json

class ModelPostBack:
    def __init__(self, id, param, request_id, callback_id, tax_info_id, crawler_status, retry_time, duration_process):
        self.id = id
        self.param = param
        self.request_id = request_id
        self.callback_id = callback_id
        self.tax_info_id = tax_info_id
        self.crawler_status = crawler_status
        self.retry_time = retry_time
        self.duration_process = duration_process


    @staticmethod
    def get_all():
        connection = db_connection()
        try:
            with connection.cursor(dictionary=True) as cursor:
                sql = "SELECT * FROM tax_request_log"
                cursor.execute(sql)
                return cursor.fetchall()
        finally:
            connection.close()

