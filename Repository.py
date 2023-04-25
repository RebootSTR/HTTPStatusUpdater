# @rebootstr
from DataBase import DataBase

# tables
from entity.User import User

USERS = "users"
PROPERTIES = "props"

# "users" columns
USER_ID = "user_id"
STATE = "state"

# "property" columns
PROPERTY = "property"
VALUE = "value"


class Repository:

    def __init__(self, databaseName: str):
        self.databaseName = databaseName
        self.initDataBase()

    def _getDatabase(self):
        return DataBase(self.databaseName)

    def initDataBase(self):
        db = self._getDatabase()
        db.create(f"{PROPERTIES}({PROPERTY} TEXT PRIMARY KEY, {VALUE} TEXT)")
        db.create(f"{USERS}({USER_ID} INTEGER PRIMARY KEY, {STATE} TEXT)")

    def getProperty(self, propertyName: str):
        return self._getDatabase().get_one_where(PROPERTIES, VALUE, f"{PROPERTY}='{propertyName}'")

    def addProperty(self, propertyName: str, value):
        self._getDatabase().append(PROPERTIES, propertyName, value)

    def editProperty(self, propertyName: str, value):
        self._getDatabase().edit(PROPERTIES, VALUE, value, f"{PROPERTY}='{propertyName}'")

    def addUser(self, user: User):
        self._getDatabase().append(USERS, user.userId, user.state)

    def getAllUsers(self) -> list[User]:
        return [User(row[0], row[1]) for row in self._getDatabase().get_all(USERS)]

    def removeUser(self, userId: int):
        self._getDatabase().remove(USERS, USER_ID, userId)

    def setUserState(self, userId: int, state: str):
        self._getDatabase().edit(USERS, STATE, state, f"{USER_ID}='{userId}'")

    def getUserState(self, userId: int):
        return self._getDatabase().get_one_where(USERS, STATE, f"{USER_ID}='{userId}'")


