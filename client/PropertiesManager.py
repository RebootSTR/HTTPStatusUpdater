# @rebootstr
from Repository import Repository
from client.dictionary import *

class PropertiesManager:

    def __init__(self, repository: Repository):
        self.repository = repository

    def get(self, propertyName: str):
        return self.repository.getProperty(propertyName)

    def getOrInput(self, propertyName: str):
        value = self.repository.getProperty(propertyName)
        if value is None:
            value = self.create_new_property(propertyName)
        return value

    def addOrEdit(self, propertyName: str, value: str):
        prop = self.repository.getProperty(propertyName)
        if prop is None:
            self.repository.addProperty(propertyName, value)
        else:
            self.repository.editProperty(propertyName, value)

    def create_new_property(self, propertyName):
        value = input(ENTER_PROPERTY.format(propertyName))
        self.repository.addProperty(propertyName, value)
        return value
