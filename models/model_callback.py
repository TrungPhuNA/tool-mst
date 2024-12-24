from models.connect_db import db_connection
import json

class CallbackInfo:
    def __init__(self, id, url, method, auth_key, user_id, additional_info=None, headers=None):
        self.id = id
        self.url = url
        self.method = method
        self.auth_key = auth_key
        self.user_id = user_id
        self.additional_info = additional_info
        # self.headers = json.loads(headers) if headers else {}
        if isinstance(headers, str):
            try:
                self.headers = json.loads(headers)  # Chuyển từ JSON string sang dictionary
            except json.JSONDecodeError:
                self.headers = {}  # Nếu lỗi, gán giá trị mặc định
        elif isinstance(headers, dict):
            self.headers = headers  # Nếu đã là dictionary, giữ nguyên
        else:
            self.headers = {}  # Gán giá trị mặc định nếu NULL hoặc kiểu khác

    @staticmethod
    def create(url, method, auth_key, user_id, additional_info=None, headers=None):
        connection = db_connection()
        try:
            with connection.cursor() as cursor:
                sql = """
                    INSERT INTO callback_info (url, method, auth_key, user_id, additional_info, headers)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """
                cursor.execute(sql, (url, method, auth_key, user_id, additional_info, json.dumps(headers)))
                connection.commit()
                return cursor.lastrowid
        finally:
            connection.close()

    @staticmethod
    def update(callback_id, url, method, auth_key, user_id, additional_info=None, headers=None):
        connection = db_connection()
        try:
            with connection.cursor() as cursor:
                sql = """
                    UPDATE callback_info
                    SET url = %s, method = %s, auth_key = %s, user_id = %s,
                        additional_info = %s, headers = %s
                    WHERE id = %s
                    """
                cursor.execute(sql, (url, method, auth_key, user_id, additional_info, json.dumps(headers), callback_id))
                connection.commit()
        finally:
            connection.close()

    @staticmethod
    def get_all():
        connection = db_connection()
        try:
            with connection.cursor(dictionary=True) as cursor:
                sql = "SELECT * FROM callback_info"
                cursor.execute(sql)
                return cursor.fetchall()
        finally:
            connection.close()

    @staticmethod
    def get_by_id(callback_id):
        connection = db_connection()
        try:
            with connection.cursor(dictionary=True) as cursor:
                sql = "SELECT * FROM callback_info WHERE id = %s"
                cursor.execute(sql, (callback_id,))
                result = cursor.fetchone()
                if result:
                    headers = result.get('headers')
                    if isinstance(headers, str):  # Nếu là JSON string, cố gắng chuyển sang dict
                        try:
                            result['headers'] = json.loads(headers)
                        except json.JSONDecodeError:
                            result['headers'] = {}  # Gán giá trị mặc định nếu không decode được
                    elif headers is None:  # Nếu headers là NULL, gán dict rỗng
                        result['headers'] = {}
                    # Nếu headers đã là dict thì giữ nguyên
                    print("==== header: ", headers)
                    # Lọc các cột không phù hợp
                    allowed_keys = {'id', 'url', 'method', 'auth_key', 'user_id', 'additional_info', 'headers'}
                    filtered_result = {key: result[key] for key in allowed_keys if key in result}
                    return CallbackInfo(**filtered_result)
            return None
        finally:
            connection.close()

    @staticmethod
    def delete(callback_id):
        connection = db_connection()
        try:
            with connection.cursor() as cursor:
                sql = "DELETE FROM callback_info WHERE id = %s"
                cursor.execute(sql, (callback_id,))
                connection.commit()
        finally:
            connection.close()
