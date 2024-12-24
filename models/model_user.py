from flask_login import UserMixin

from models.connect_db import db_connection


class User(UserMixin):
    def __init__(self, id, username, email):
        self.id = id
        self.username = username
        self.email = email

    @staticmethod
    def from_dict(user_dict):
        """
        Chuyển đổi từ dictionary (dữ liệu database) thành đối tượng User.
        """
        return User(
            id=user_dict["id"],
            username=user_dict["username"],
            email=user_dict["email"]
        )

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @staticmethod
    def get_all_users():
        connection = db_connection()
        try:
            with connection.cursor() as cursor:
                sql = "SELECT id, username, email FROM users"
                cursor.execute(sql)
                result = cursor.fetchall()  # Trả về danh sách dict
                columns = [col[0] for col in cursor.description]
                result_as_dict = [dict(zip(columns, row)) for row in result]
                return [User.from_dict(row) for row in result_as_dict]
        finally:
            connection.close()
