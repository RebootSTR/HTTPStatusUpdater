# @rebootstr

import sqlite3

BASE_NAME = "properties.db"


def get(property: str):
    base = DataBase(BASE_NAME)
    base.create("_values(property TEXT, value TEXT)")
    value = base.get_one_where("_values", "value", f"property='{property}'")
    if value is None:
        value = create_new_property(base, property)
    return value


def create_new_property(base, property):
    value = input(f"Enter value for {property} >> ")
    base.append("_values", f"{property}", value)
    return value


def set(propery, value):
    raise Exception("Not enable yet")


class DataBase:
    def __init__(self, name):
        self.conn = sqlite3.connect(name)

    def create(self, table):
        cursor = self.conn.cursor()
        cursor.execute(f"create table if not exists {table}")
        cursor.close()

    def append(self, table, *values):
        cursor = self.conn.cursor()
        cursor.execute("insert into {} values ({})".format(table, ("?," * len(values))[:-1]), values)
        cursor.close()
        self.save()

    def get_one_where(self, table, column, search):
        cursor = self.conn.cursor()
        data = cursor.execute("SELECT {} FROM {} where {}".format(column, table, search)).fetchone()
        if data is not None:
            data = data[0]
        cursor.close()
        return data

    def edit(self, table, column, value, search):
        cursor = self.conn.cursor()
        cursor.execute("update {} set {}=? where {}".format(table, column, search), [value])
        cursor.close()
        self.save()

    def save(self):
        self.conn.commit()