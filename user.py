from flask_login import UserMixin


class User(UserMixin):

    def __init__(self, netid):
        self.id = netid
        self.display_name = "Administrator"

    @staticmethod
    def get(netid):
        user = User(netid=netid)
        return user
