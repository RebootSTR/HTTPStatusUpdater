# @rebootstr
from DataBase import DataBase

USERS = "users"
PROPERTIES = "props"


class Repository:

    def __init__(self, databaseName: str):
        self.databaseName = databaseName
        self.initDataBase()

    def _getDatabase(self):
        return DataBase(self.databaseName)

    def initDataBase(self):
        db = self._getDatabase()
        db.create(f"{PROPERTIES}(property TEXT, value TEXT)")
        db.create(f"{USERS}(user_id INTEGER, adminCode TEXT)")

    def getProperty(self, propertyName: str):
        return self._getDatabase().get_one_where(PROPERTIES, "value", f"property='{propertyName}'")

    def addProperty(self, propertyName: str, value):
        self._getDatabase().append(PROPERTIES, f"{propertyName}", value)

    def editProperty(self, propertyName: str, value):
        self._getDatabase().edit(PROPERTIES, "value", value, f"property='{propertyName}'")

    def addUser(self, userId: int):
        self._getDatabase().append(USERS, userId, None)

    def getAllUsers(self):
        return self._getDatabase().get_all(USERS, "user_id")

    def removeUser(self, userId: int):
        self._getDatabase().remove(USERS, "user_id", userId)

    def setAdminCode(self, userId: int, code: str or None):
        self._getDatabase().edit(USERS, "adminCode", code, f"user_id='{userId}'")

    def getAdminCode(self, userId: int):
        return self._getDatabase().get_one_where(USERS, "adminCode", f"user_id='{userId}'")


