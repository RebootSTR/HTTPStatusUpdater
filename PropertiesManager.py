# @rebootstr
from Repository import Repository


class PropertiesManager:

    def __init__(self, repository: Repository):
        self.repository = repository

    def get(self, propertyName: str):
        value = self.repository.getProperty(propertyName)
        if value is None:
            value = self.create_new_property(propertyName)
        return value

    def create_new_property(self, propertyName):
        value = input(f"Enter value for {propertyName} >> ")
        self.repository.addProperty(propertyName, value)
        return value
