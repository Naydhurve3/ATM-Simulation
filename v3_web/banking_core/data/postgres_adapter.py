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
    scenario_exported BOOLEAN DEFAULT FALSE,
    token TEXT
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
CREATE TABLE IF NOT EXISTS user_activity (
    activity_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id),
    activity TEXT NOT NULL,
    amount DOUBLE PRECISION DEFAULT 0,
    channel TEXT DEFAULT 'web',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS atm_card_stats (
    "Bank_Name" TEXT, "ATMs_On_Site" DOUBLE PRECISION, "ATMs_Off_Site" DOUBLE PRECISION,
    "PoS" DOUBLE PRECISION, "Micro_ATMs" DOUBLE PRECISION,
    "Bharat_QR_Codes" DOUBLE PRECISION, "UPI_QR_Codes" DOUBLE PRECISION,
    "Credit_Cards_Outstanding" DOUBLE PRECISION, "Debit_Cards_Outstanding" DOUBLE PRECISION,
    "CC_Vol_PoS" DOUBLE PRECISION, "CC_Val_PoS" DOUBLE PRECISION,
    "CC_Vol_Online" DOUBLE PRECISION, "CC_Val_Online" DOUBLE PRECISION,
    "CC_Vol_Others" DOUBLE PRECISION, "CC_Val_Others" DOUBLE PRECISION,
    "CC_Vol_Cash_ATM" DOUBLE PRECISION, "CC_Val_Cash_ATM" DOUBLE PRECISION,
    "DC_Vol_PoS" DOUBLE PRECISION, "DC_Val_PoS" DOUBLE PRECISION,
    "DC_Vol_Online" DOUBLE PRECISION, "DC_Val_Online" DOUBLE PRECISION,
    "DC_Vol_Others" DOUBLE PRECISION, "DC_Val_Others" DOUBLE PRECISION,
    "DC_Vol_Cash_ATM" DOUBLE PRECISION, "DC_Val_Cash_ATM" DOUBLE PRECISION,
    "DC_Vol_Cash_PoS" DOUBLE PRECISION, "DC_Val_Cash_PoS" DOUBLE PRECISION,
    "Reporting_Month" TEXT, "Month_Num" INTEGER, "Bank_Type" TEXT,
    "Total_ATMs" DOUBLE PRECISION, "Total_Cards" DOUBLE PRECISION,
    "CC_Total_Vol" DOUBLE PRECISION, "CC_Total_Val" DOUBLE PRECISION,
    "DC_Total_Vol" DOUBLE PRECISION, "DC_Total_Val" DOUBLE PRECISION,
    "Total_Txn_Vol" DOUBLE PRECISION, "Total_Txn_Val" DOUBLE PRECISION,
    "Digital_QR_Codes" DOUBLE PRECISION, "Digital_Vol" DOUBLE PRECISION,
    "Cash_Vol" DOUBLE PRECISION, "Digital_Share" DOUBLE PRECISION,
    "Cash_Share" DOUBLE PRECISION
);
CREATE TABLE IF NOT EXISTS bank_summary (
    "Bank_Name" TEXT, "Total_ATMs" DOUBLE PRECISION, "Total_Cards" DOUBLE PRECISION,
    "Total_Txn_Vol" DOUBLE PRECISION, "Total_Txn_Val" DOUBLE PRECISION,
    "Digital_Share" DOUBLE PRECISION
);
CREATE TABLE IF NOT EXISTS monthly_aggregate (
    "Reporting_Month" TEXT, "Month_Num" INTEGER,
    "Total_ATMs" DOUBLE PRECISION, "Total_Cards" DOUBLE PRECISION,
    "Total_Txn_Vol" DOUBLE PRECISION, "Total_Txn_Val" DOUBLE PRECISION,
    "Digital_Share" DOUBLE PRECISION
);
CREATE TABLE IF NOT EXISTS ml_snapshots (
    snapshot_id SERIAL PRIMARY KEY,
    name TEXT NOT NULL, bank TEXT, metric TEXT, kind TEXT,
    payload JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (name, bank, metric, kind)
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
    try:
        cur.execute("ALTER TABLE user_sessions ADD COLUMN IF NOT EXISTS token TEXT")
    except Exception:
        pass
    conn.commit()
    cur.execute("SELECT COUNT(*) FROM users WHERE email = 'demo@atm.com'")
    if cur.fetchone()[0] == 0:
        from banking_core.utils import hash_pin
        pin_hash = hash_pin("1234")
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


_IDENT_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")

# Mixed-case columns stored quoted in PG (mirrors the sqlite schema exactly).
# Ecosystem tables (users, transactions, ...) are all lowercase and need no quoting.
_QUOTED_IDENTS = {
    "Bank_Name", "ATMs_On_Site", "ATMs_Off_Site", "PoS", "Micro_ATMs",
    "Bharat_QR_Codes", "UPI_QR_Codes", "Credit_Cards_Outstanding",
    "Debit_Cards_Outstanding", "CC_Vol_PoS", "CC_Val_PoS", "CC_Vol_Online",
    "CC_Val_Online", "CC_Vol_Others", "CC_Val_Others", "CC_Vol_Cash_ATM",
    "CC_Val_Cash_ATM", "DC_Vol_PoS", "DC_Val_PoS", "DC_Vol_Online",
    "DC_Val_Online", "DC_Vol_Others", "DC_Val_Others", "DC_Vol_Cash_ATM",
    "DC_Val_Cash_ATM", "DC_Vol_Cash_PoS", "DC_Val_Cash_PoS",
    "Reporting_Month", "Month_Num", "Bank_Type", "Total_ATMs", "Total_Cards",
    "CC_Total_Vol", "CC_Total_Val", "DC_Total_Vol", "DC_Total_Val",
    "Total_Txn_Vol", "Total_Txn_Val", "Digital_QR_Codes", "Digital_Vol",
    "Cash_Vol", "Digital_Share", "Cash_Share", "DC_Vol_Card_Txn", "CBS_Vol",
    "DD_Vol", "PO_Vol", "CC_Vol_Cash_ATM", "CC_Val_Cash_ATM",
    "CC_Total_Vol", "CC_Total_Val", "DC_Total_Vol", "DC_Total_Val",
}


def _quote_mixed_identifiers(sql: str) -> str:
    """Quote known mixed-case column names so Postgres keeps them exact.
    Skips string literals and already-quoted identifiers; keywords and
    lowercase tokens are untouched."""
    out = []
    i = 0
    n = len(sql)
    in_single = False
    in_double = False
    while i < n:
        ch = sql[i]
        if ch == "'" and not in_double:
            in_single = not in_single
            out.append(ch)
            i += 1
        elif ch == '"' and not in_single:
            in_double = not in_double
            out.append(ch)
            i += 1
        elif not in_single and not in_double and (ch.isalpha() or ch == "_"):
            m = _IDENT_RE.match(sql, i)
            tok = m.group(0)
            if tok in _QUOTED_IDENTS:
                out.append(f'"{tok}"')
            else:
                out.append(tok)
            i = m.end()
        else:
            out.append(ch)
            i += 1
    return "".join(out)


class _PGCursor:
    def __init__(self, cur):
        self._cur = cur
        self.description = None
        self.lastrowid = None

    @property
    def rowcount(self):
        return self._cur.rowcount

    def close(self):
        try:
            self._cur.close()
        except Exception:
            pass

    def execute(self, sql, params=None):
        psycopg2_sql = _qmark_to_psycopg2(_quote_mixed_identifiers(sql))
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

    def _convert(self, row):
        if row is None:
            return None
        from datetime import datetime as _dt
        return tuple(v.isoformat() if isinstance(v, _dt) else v for v in row)

    def fetchone(self):
        return self._convert(self._cur.fetchone())

    def fetchall(self):
        rows = self._cur.fetchall()
        return [self._convert(r) for r in rows]

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
        conn = self._ensure()
        try:
            conn.rollback()
        except Exception:
            pass
        return _PGCursor(conn.cursor())

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


def get_ecosystem_conn():
    """SQLite-compatible connection for ecosystem data (PG when enabled)."""
    if _ENABLED:
        return get_pg_connection()
    from banking_core.data.db_manager import db
    return db.get_connection("ecosystem")


def get_industry_conn():
    """SQLite-compatible connection for industry/RBI data (PG when enabled, else None)."""
    if _ENABLED:
        return get_pg_connection()
    return None


def write_dataframe(df, table, if_exists="replace"):
    """Write a pandas DataFrame to a PG table without SQLAlchemy."""
    if not _ENABLED or df is None or len(df) == 0:
        return
    import pandas as pd
    conn = get_pg_connection()
    cols = [c for c in df.columns if c != "index"]
    col_sql = ", ".join(f'"{c}"' for c in cols)
    ph = ", ".join(["%s"] * len(cols))
    insert_sql = f'INSERT INTO "{table}" ({col_sql}) VALUES ({ph})'
    if if_exists == "replace":
        try:
            conn.execute(f'DELETE FROM "{table}"')
        except Exception:
            pass
    cur = conn.cursor()
    for row in df[cols].itertuples(index=False, name=None):
        cur.execute(insert_sql, tuple(None if pd.isna(v) and not isinstance(v, str) else v for v in row))
    conn.commit()


def set_ml_snapshot(name, payload, bank=None, metric=None, kind="json"):
    """Upsert a precomputed ML result snapshot (for serverless deployments)."""
    if not _ENABLED:
        return False
    import json
    conn = get_pg_connection()
    conn.execute(
        "INSERT INTO ml_snapshots (name, bank, metric, kind, payload) "
        "VALUES (%s, %s, %s, %s, %s) "
        "ON CONFLICT (name, bank, metric, kind) DO UPDATE SET payload = EXCLUDED.payload, "
        "created_at = CURRENT_TIMESTAMP",
        (name, bank, metric, kind, json.dumps(payload)),
    )
    conn.commit()
    return True


def get_ml_snapshot(name, bank=None, metric=None, kind="json"):
    if not _ENABLED:
        return None
    import json
    conn = get_pg_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT payload FROM ml_snapshots WHERE name=%s AND "
        "((%s::text IS NULL AND bank IS NULL) OR bank=%s) AND "
        "((%s::text IS NULL AND metric IS NULL) OR metric=%s) AND kind=%s "
        "ORDER BY snapshot_id DESC LIMIT 1",
        (name, bank, bank, metric, metric, kind),
    )
    row = cur.fetchone()
    if not row:
        return None
    try:
        return json.loads(row[0]) if isinstance(row[0], str) else row[0]
    except Exception:
        return row[0]