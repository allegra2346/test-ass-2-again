from db_connection import DB


class BaseRepo:
    def __init__(self, db_connection=None):
        self._db = db_connection or DB.conn()

    def _execute_query(self, query, params=None):
        cursor = self._db.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        return cursor

    def _commit(self):
        self._db.commit()

    def _fetch_one(self, query, params=None):
        cursor = self._execute_query(query, params)
        return cursor.fetchone()

    def _fetch_all(self, query, params=None):
        cursor = self._execute_query(query, params)
        return cursor.fetchall()
