# @rebootstr
from DataBase import DataBase


class Repository:

    def __init__(self, database: DataBase):
        self.database = database
        self.initDataBase()

    def initDataBase(self):
        self.database.create("_values(property TEXT, value TEXT)")
        self.database.create("ids(user_id INTEGER)")

    def getProperty(self, propertyName: str):
        return self.database.get_one_where("_values", "value", f"property='{propertyName}'")

    def addProperty(self, propertyName: str, value):
        self.database.append("_values", f"{propertyName}", value)

    def addUser(self, userId: int):
        self.database.append("ids", userId)

    def getAllUsers(self):
        return self.database.get_all("ids", "user_id")

    def removeUser(self, userId: int):
        self.database.remove("ids", "user_id", userId)




