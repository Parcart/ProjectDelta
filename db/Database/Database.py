
from .DatabaseUser import DatabaseUser


class Database:
    def __init__(self, instance):
        self.User = DatabaseUser(instance)
        # self.UserSession = DatabaseUserSession(instance)
        # self.UserProfile = DatabaseUserProfile(instance)
