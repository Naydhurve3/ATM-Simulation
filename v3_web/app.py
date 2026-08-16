import os
import sys
import shutil
import hashlib
import sqlite3
from pathlib import Path

_USE_PG = os.environ.get("DATABASE_URL") is not None

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def _init_database(db_path: Path):
    """Create the ecosystem database schema and seed a demo user."""
    if db_path.exists():
        return

    conn = sqlite3.connect(str(db_path))
    c = conn.cursor()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL, phone TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL, age INTEGER NOT NULL,
            age_group TEXT, is_minor BOOLEAN DEFAULT 0,
            guardian_name TEXT, guardian_phone TEXT,
            guardian_relation TEXT, guardian_aadhaar_last4 TEXT,
            child_aadhaar_last4 TEXT, kyc_address_match BOOLEAN,
            kyc_surname_match BOOLEAN, income_status TEXT,
            income_bracket TEXT, account_no TEXT UNIQUE NOT NULL,
            card_no TEXT UNIQUE NOT NULL, bank TEXT NOT NULL,
            account_type TEXT, pin_hash TEXT NOT NULL,
            balance REAL DEFAULT 5000, atm_daily_limit REAL DEFAULT 50000,
            atm_used_today REAL DEFAULT 0, credit_score INTEGER DEFAULT 600,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_active TIMESTAMP, is_active BOOLEAN DEFAULT 1,
            preferences TEXT DEFAULT '{}'
        );
        CREATE TABLE IF NOT EXISTS transactions (
            txn_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES users(user_id),
            type TEXT NOT NULL, amount REAL, fee REAL DEFAULT 0,
            balance_before REAL, balance_after REAL,
            channel TEXT DEFAULT 'atm', target_account TEXT,
            target_bank TEXT, bank TEXT, notes_given TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_fraud BOOLEAN DEFAULT 0, fraud_score REAL
        );
        CREATE TABLE IF NOT EXISTS fraud_flags (
            flag_id INTEGER PRIMARY KEY AUTOINCREMENT,
            txn_id INTEGER REFERENCES transactions(txn_id),
            user_id INTEGER REFERENCES users(user_id),
            anomaly_score REAL, flagged_by TEXT,
            is_confirmed BOOLEAN DEFAULT 0,
            scenario_exported BOOLEAN DEFAULT 0,
            flagged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS credit_history (
            entry_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES users(user_id),
            event_type TEXT, amount REAL,
            score_impact REAL,
            recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS loan_applications (
            loan_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES users(user_id),
            loan_type TEXT, amount_requested REAL,
            amount_approved REAL, interest_rate REAL,
            tenure_months INTEGER, status TEXT,
            risk_score REAL, predicted_default REAL,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            decision_at TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS user_sessions (
            session_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES users(user_id),
            login_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            logout_at TIMESTAMP, actions_count INTEGER DEFAULT 0,
            scenario_exported BOOLEAN DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS savings_goals (
            goal_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES users(user_id),
            goal_name TEXT, target_amount REAL,
            current_amount REAL DEFAULT 0, deadline TEXT,
            is_completed BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS feedback (
            feedback_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES users(user_id),
            rating INTEGER, comments TEXT, category TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS user_activity (
            activity_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES users(user_id),
            activity TEXT NOT NULL,
            amount REAL DEFAULT 0,
            channel TEXT DEFAULT 'web',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    from banking_core.utils import hash_pin
    pin_hash = hash_pin("1234")
    c.execute("""
        INSERT INTO users (name, phone, email, age, age_group, is_minor,
            account_no, card_no, bank, account_type, pin_hash, balance,
            atm_daily_limit, atm_used_today, credit_score)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        "Demo User", "9876543210", "demo@atm.com", 30, "adult", False,
        "123456789012", "1234-5678-9012-3456", "SBI", "savings",
        pin_hash, 50000.0, 100000.0, 0, 700
    ))
    conn.commit()
    conn.close()


# On Vercel (sqlite mode only), redirect writable paths to /tmp.
# With DATABASE_URL set we run in Neon (PG) mode and skip the /tmp shim.
if os.environ.get("VERCEL") == "1" and not _USE_PG:
    tmp_dir = Path("/tmp/atm_data")
    processed_dir = tmp_dir / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    ecosystem_db = processed_dir / "ecosystem.db"
    atm_data_db = processed_dir / "atm_data.db"

    _init_database(ecosystem_db)

    import banking_core.utils
    banking_core.utils.PROJECT_ROOT = tmp_dir
    banking_core.utils.DB_PATH = atm_data_db
    banking_core.utils.ECOSYSTEM_DB = ecosystem_db
    banking_core.utils.DATA_RAW = tmp_dir / "data" / "raw"
    banking_core.utils.DATA_PROCESSED = processed_dir
    banking_core.utils.DATA_MODELS = tmp_dir / "data" / "models"
    banking_core.utils.OUTPUTS_REPORTS = tmp_dir / "outputs" / "reports"
    banking_core.utils.OUTPUTS_CHARTS = tmp_dir / "outputs" / "charts"
    banking_core.utils.DATA_TRAINING = tmp_dir / "data" / "training"
    banking_core.utils.ensure_dirs()

    # Run v2 schema migration (needs db_manager import, which uses banking_core.utils paths)
    try:
        from scripts.migrate_database import run_migration
        run_migration()
    except Exception:
        pass

elif _USE_PG:
    # Neon mode: redirect all data/output paths to /tmp (serverless FS is read-only)
    import banking_core.utils
    pg_tmp = Path("/tmp/atm_data")
    pg_processed = pg_tmp / "processed"
    pg_processed.mkdir(parents=True, exist_ok=True)
    banking_core.utils.PROJECT_ROOT = pg_tmp
    banking_core.utils.DB_PATH = pg_processed / "atm_data.db"
    banking_core.utils.ECOSYSTEM_DB = pg_processed / "ecosystem.db"
    banking_core.utils.DATA_RAW = pg_tmp / "data" / "raw"
    banking_core.utils.DATA_PROCESSED = pg_processed
    banking_core.utils.DATA_MODELS = pg_tmp / "data" / "models"
    banking_core.utils.OUTPUTS_REPORTS = pg_tmp / "outputs" / "reports"
    banking_core.utils.OUTPUTS_CHARTS = pg_tmp / "outputs" / "charts"
    banking_core.utils.DATA_TRAINING = pg_tmp / "data" / "training"
    banking_core.utils.ensure_dirs()
    from banking_core.data.postgres_adapter import init_db as pg_init
    pg_init()

from banking_web import create_app

app = create_app()


@app.errorhandler(500)
def handle_500(e):
    from flask import render_template
    original = getattr(e, "original_exception", None) or e
    return render_template("error.html", message=str(original)), 500
