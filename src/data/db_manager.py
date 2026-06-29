import sqlite3
import time
from datetime import datetime
from pathlib import Path
from contextlib import contextmanager
from src.utils import DB_PATH, ECOSYSTEM_DB, DATA_PROCESSED, ensure_dirs


class DatabaseManager:
    _instances = {}

    def __new__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__new__(cls)
        return cls._instances[cls]

    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        ensure_dirs()
        self._connections = {}
        self._databases = {
            "atm_data": (DB_PATH, False),
            "ecosystem": (ECOSYSTEM_DB, False),
        }
        self._analytics_dir = DATA_PROCESSED / "analytics"
        self._analytics_dir.mkdir(parents=True, exist_ok=True)
        self._feature_store_path = self._analytics_dir / "feature_store.db"
        self._databases["feature_store"] = (self._feature_store_path, False)
        self._ensure_analytics_tables()
        self._query_log = []

    def _ensure_analytics_tables(self):
        conn = self.get_connection("feature_store")
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS feature_definitions (
                feature_id INTEGER PRIMARY KEY AUTOINCREMENT,
                feature_name TEXT UNIQUE NOT NULL,
                feature_set TEXT NOT NULL,
                description TEXT,
                sql_expression TEXT,
                data_type TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS feature_snapshots (
                snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
                feature_set TEXT NOT NULL,
                snapshot_label TEXT,
                row_count INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS training_datasets (
                dataset_id INTEGER PRIMARY KEY AUTOINCREMENT,
                scenario TEXT NOT NULL,
                export_timestamp TEXT,
                tables_exported TEXT,
                row_counts TEXT,
                file_paths TEXT,
                schema_snapshot TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS model_registry (
                model_id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_name TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS model_versions (
                version_id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_id INTEGER REFERENCES model_registry(model_id),
                version INTEGER NOT NULL,
                hyperparameters TEXT,
                metrics TEXT,
                training_dataset_id INTEGER,
                feature_snapshot_id INTEGER,
                model_path TEXT,
                training_duration_ms REAL,
                is_production BOOLEAN DEFAULT 0,
                trained_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS production_log (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_name TEXT,
                version INTEGER,
                promoted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notes TEXT
            );
            CREATE TABLE IF NOT EXISTS query_log (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                db_name TEXT,
                query_hash TEXT,
                duration_ms REAL,
                queried_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS data_catalog (
                catalog_id INTEGER PRIMARY KEY AUTOINCREMENT,
                db_name TEXT NOT NULL,
                table_name TEXT NOT NULL,
                schema_json TEXT,
                row_count INTEGER,
                recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS export_log (
                export_id INTEGER PRIMARY KEY AUTOINCREMENT,
                scenario TEXT NOT NULL,
                dataset_type TEXT,
                file_path TEXT,
                row_count INTEGER,
                checksum TEXT,
                schema_snapshot TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()

    def register_database(self, name, path, read_only=False):
        self._databases[name] = (Path(path), read_only)

    def get_connection(self, db_name="ecosystem"):
        if db_name in self._connections and self._connections[db_name] is not None:
            conn = self._connections[db_name][0]
            try:
                conn.execute("SELECT 1")
                return conn
            except sqlite3.ProgrammingError:
                pass
        path, read_only = self._databases.get(db_name, (ECOSYSTEM_DB, False))
        path = Path(path) if isinstance(path, str) else path
        path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(path))
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.row_factory = sqlite3.Row
        self._connections[db_name] = (conn, read_only)
        return conn

    @contextmanager
    def connection(self, db_name="ecosystem"):
        conn = self.get_connection(db_name)
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise

    def close_all(self):
        for name, (conn, _) in self._connections.items():
            if conn:
                conn.close()
        self._connections = {}

    def execute(self, db_name, sql, params=None):
        conn = self.get_connection(db_name)
        start = time.perf_counter()
        try:
            if params:
                result = conn.execute(sql, params)
            else:
                result = conn.execute(sql)
            conn.commit()
            duration = (time.perf_counter() - start) * 1000
            self._log_query(db_name, sql, duration)
            return result
        except Exception as e:
            duration = (time.perf_counter() - start) * 1000
            self._log_query(db_name, sql, duration)
            raise e

    def fetch_all(self, db_name, sql, params=None):
        conn = self.get_connection(db_name)
        start = time.perf_counter()
        if params:
            cur = conn.execute(sql, params)
        else:
            cur = conn.execute(sql)
        rows = cur.fetchall()
        duration = (time.perf_counter() - start) * 1000
        self._log_query(db_name, sql, duration)
        return [dict(r) for r in rows]

    def fetch_one(self, db_name, sql, params=None):
        rows = self.fetch_all(db_name, sql, params)
        return rows[0] if rows else None

    def _log_query(self, db_name, sql, duration_ms):
        if duration_ms > 1000:
            try:
                conn = self.get_connection("feature_store")
                conn.execute(
                    "INSERT INTO query_log (db_name, query_hash, duration_ms) VALUES (?, ?, ?)",
                    (db_name, str(hash(sql[:100])), round(duration_ms, 2))
                )
                conn.commit()
            except Exception:
                pass

    def get_slow_queries(self, min_duration_ms=1000, limit=20):
        rows = self.fetch_all(
            "feature_store",
            "SELECT * FROM query_log WHERE duration_ms >= ? ORDER BY duration_ms DESC LIMIT ?",
            (min_duration_ms, limit)
        )
        return rows

    @property
    def atm_data(self):
        return self.get_connection("atm_data")

    @property
    def ecosystem(self):
        return self.get_connection("ecosystem")

    @property
    def feature_store(self):
        return self.get_connection("feature_store")


db = DatabaseManager()
