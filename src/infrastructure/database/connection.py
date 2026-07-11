import os
from typing import Optional


class DatabaseFactory:
    _instances = {}

    @classmethod
    def reset(cls):
        cls._instances = {}

    @classmethod
    def get_connection(cls, db_name: str = "ecosystem"):
        if db_name in cls._instances:
            return cls._instances[db_name]
        from src.data.db_manager import db
        conn = db.get_connection(db_name)
        cls._instances[db_name] = conn
        return conn

    @classmethod
    def close_all(cls):
        for name, conn in cls._instances.items():
            try:
                conn.close()
            except Exception:
                pass
        cls._instances = {}
