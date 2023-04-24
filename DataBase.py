# @rebootstr

import sqlite3


class DataBase:
    def __init__(self, name):
        self.conn = sqlite3.connect(name)

    def _save(self):
        self.conn.commit()

    def create(self, table):
        cursor = self.conn.cursor()
        cursor.execute(f"create table if not exists {table}")
        cursor.close()

    def append(self, table, *values):
        cursor = self.conn.cursor()
        cursor.execute("insert into {} values ({})".format(table, ("?," * len(values))[:-1]), values)
        cursor.close()
        self._save()

    def get_one_where(self, table, column, search):
        cursor = self.conn.cursor()
        data = cursor.execute("SELECT {} FROM {} where {}".format(column, table, search)).fetchone()
        if data is not None:
            data = data[0]
        cursor.close()
        return data

    def get_all(self, table, column):
        cursor = self.conn.cursor()
        data = cursor.execute("SELECT {} FROM {}".format(column, table)).fetchall()
        cursor.close()
        return data

    def edit(self, table, column, value, search):
        cursor = self.conn.cursor()
        cursor.execute("update {} set {}=? where {}".format(table, column, search), [value])
        cursor.close()
        self._save()

    def remove(self, table, column, search):
        cursor = self.conn.cursor()
        cursor.execute("delete from {} where {}=?".format(table, column), [search])
        cursor.close()
        self._save()

