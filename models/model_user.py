from flask_login import UserMixin

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
