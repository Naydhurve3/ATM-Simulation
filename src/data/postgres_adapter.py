import os
import re
import hashlib
import urllib.parse

_DATABASE_URL = os.environ.get("DATABASE_URL")
_ENABLED = _DATABASE_URL is not None

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS users (
    user_id SERIAL PRIMARY KEY,
    name TEXT NOT NULL, phone TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL, age INTEGER NOT NULL,
    age_group TEXT, is_minor BOOLEAN DEFAULT FALSE,
    guardian_name TEXT, guardian_phone TEXT,
    guardian_relation TEXT, guardian_aadhaar_last4 TEXT,
    child_aadhaar_last4 TEXT, kyc_address_match BOOLEAN,
    kyc_surname_match BOOLEAN, income_status TEXT,
    income_bracket TEXT, account_no TEXT UNIQUE NOT NULL,
    card_no TEXT UNIQUE NOT NULL, bank TEXT NOT NULL,
    account_type TEXT, pin_hash TEXT NOT NULL,
    balance DOUBLE PRECISION DEFAULT 5000,
    atm_daily_limit DOUBLE PRECISION DEFAULT 50000,
    atm_used_today DOUBLE PRECISION DEFAULT 0,
    credit_score INTEGER DEFAULT 600,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP, is_active BOOLEAN DEFAULT TRUE,
    preferences TEXT DEFAULT '{}'
);
CREATE TABLE IF NOT EXISTS transactions (
    txn_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id),
    type TEXT NOT NULL, amount DOUBLE PRECISION,
    fee DOUBLE PRECISION DEFAULT 0,
    balance_before DOUBLE PRECISION, balance_after DOUBLE PRECISION,
    channel TEXT DEFAULT 'atm', target_account TEXT,
    target_bank TEXT, bank TEXT, notes_given TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_fraud BOOLEAN DEFAULT FALSE, fraud_score DOUBLE PRECISION
);
CREATE TABLE IF NOT EXISTS fraud_flags (
    flag_id SERIAL PRIMARY KEY,
    txn_id INTEGER REFERENCES transactions(txn_id),
    user_id INTEGER REFERENCES users(user_id),
    anomaly_score DOUBLE PRECISION, flagged_by TEXT,
    is_confirmed BOOLEAN DEFAULT FALSE,
    scenario_exported BOOLEAN DEFAULT FALSE,
    flagged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS credit_history (
    entry_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id),
    event_type TEXT, amount DOUBLE PRECISION,
    score_impact DOUBLE PRECISION,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS loan_applications (
    loan_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id),
    loan_type TEXT, amount_requested DOUBLE PRECISION,
    amount_approved DOUBLE PRECISION, interest_rate DOUBLE PRECISION,
    tenure_months INTEGER, status TEXT,
    risk_score DOUBLE PRECISION, predicted_default DOUBLE PRECISION,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    decision_at TIMESTAMP
);
CREATE TABLE IF NOT EXISTS user_sessions (
    session_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id),
    login_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    logout_at TIMESTAMP, actions_count INTEGER DEFAULT 0,
    scenario_exported BOOLEAN DEFAULT FALSE
);
CREATE TABLE IF NOT EXISTS savings_goals (
    goal_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id),
    goal_name TEXT, target_amount DOUBLE PRECISION,
    current_amount DOUBLE PRECISION DEFAULT 0, deadline TEXT,
    is_completed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS feedback (
    feedback_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id),
    rating INTEGER, comments TEXT, category TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


def is_enabled():
    return _ENABLED


def _parse_db_url(url):
    parsed = urllib.parse.urlparse(url)
    return {
        "user": parsed.username,
        "password": parsed.password,
        "host": parsed.hostname,
        "port": parsed.port or 5432,
        "database": parsed.path.lstrip("/"),
    }


def _get_raw_conn():
    import psycopg2
    params = _parse_db_url(_DATABASE_URL)
    return psycopg2.connect(
        user=params["user"],
        password=params["password"],
        host=params["host"],
        port=params["port"],
        dbname=params["database"],
        sslmode="require",
    )


def init_db():
    if not _ENABLED:
        return
    conn = _get_raw_conn()
    cur = conn.cursor()
    for stmt in _SCHEMA_SQL.split(";"):
        s = stmt.strip()
        if s:
            try:
                cur.execute(s + ";")
            except Exception:
                pass
    conn.commit()
    cur.execute("SELECT COUNT(*) FROM users WHERE email = 'demo@atm.com'")
    if cur.fetchone()[0] == 0:
        pin_hash = hashlib.sha256(b"1234").hexdigest()
        cur.execute("""
            INSERT INTO users (name, phone, email, age, age_group, is_minor,
                account_no, card_no, bank, account_type, pin_hash, balance,
                atm_daily_limit, atm_used_today, credit_score)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, ("Demo User", "9876543210", "demo@atm.com", 30, "adult", False,
              "123456789012", "1234-5678-9012-3456", "SBI", "savings",
              pin_hash, 50000.0, 100000.0, 0, 700))
        conn.commit()
    conn.close()


# ── sqlite3-compatible wrappers ─────────────────────────────

def _qmark_to_psycopg2(sql: str) -> str:
    """Convert ? to %s, but leave %%s and string literals intact."""
    result = []
    in_single = False
    for ch in sql:
        if ch == "'":
            in_single = not in_single
        if ch == "?" and not in_single:
            result.append("%s")
        else:
            result.append(ch)
    return "".join(result)


class _PGCursor:
    def __init__(self, cur):
        self._cur = cur
        self.description = None
        self.lastrowid = None

    def execute(self, sql, params=None):
        psycopg2_sql = _qmark_to_psycopg2(sql)
        self._cur.execute(psycopg2_sql, params or ())
        self.description = self._cur.description
        if self._cur.description and "RETURNING" in sql.upper():
            row = self._cur.fetchone()
            if row:
                self.lastrowid = row[0]
        return self

    def executemany(self, sql, params_list):
        for p in params_list:
            self.execute(sql, p)
        return self

    def fetchone(self):
        return self._cur.fetchone()

    def fetchall(self):
        return self._cur.fetchall()

    def __iter__(self):
        return iter(self.fetchall())


class _PGConnection:
    def __init__(self):
        self._conn = None

    def _ensure(self):
        if self._conn is None or self._conn.closed:
            self._conn = _get_raw_conn()
        return self._conn

    def cursor(self):
        return _PGCursor(self._ensure().cursor())

    def execute(self, sql, params=None):
        return self.cursor().execute(sql, params)

    def commit(self):
        if self._conn and not self._conn.closed:
            self._conn.commit()

    def rollback(self):
        if self._conn and not self._conn.closed:
            self._conn.rollback()

    def close(self):
        if self._conn and not self._conn.closed:
            self._conn.close()
        self._conn = None

    def executescript(self, script):
        for stmt in script.split(";"):
            s = stmt.strip()
            if s:
                self.execute(s)


_pg_conn = None


def get_pg_connection():
    global _pg_conn
    if _pg_conn is None:
        _pg_conn = _PGConnection()
    return _pg_conn