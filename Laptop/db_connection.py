import os
import sqlite3

DB_PATH = "Laptop/classroom_management.db"
SCHEMA_FILE = "Laptop/database.sql"


class DB:
    _conn = None

    @classmethod
    def conn(cls):
        if cls._conn is None:
            need_init = not os.path.exists(DB_PATH)
            cls._conn = sqlite3.connect(DB_PATH, check_same_thread=False)

            if need_init:
                cls._initialize()
        return cls._conn

    @classmethod
    def _initialize(cls):
        with open(SCHEMA_FILE, "r") as f:
            sql_script = f.read()
        cls._conn.executescript(sql_script)
        cls._conn.commit()
