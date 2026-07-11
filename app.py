import os
import sys
import shutil
import hashlib
import sqlite3
from pathlib import Path

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
    """)

    pin_hash = hashlib.sha256(b"1234").hexdigest()
    c.execute("""
        INSERT INTO users (name, phone, email, age, age_group, is_minor,
            account_no, card_no, bank, account_type, pin_hash, balance,
            atm_daily_limit, atm_used_today, credit_score)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        "Demo User", "9876543210", "demo@atm.com", 30, "adult", 0,
        "123456789012", "1234-5678-9012-3456", "SBI", "savings",
        pin_hash, 50000.0, 100000.0, 0, 700
    ))
    conn.commit()
    conn.close()


# On Vercel, redirect writable paths to /tmp
if os.environ.get("VERCEL") == "1":
    tmp_dir = Path("/tmp/atm_data")
    processed_dir = tmp_dir / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    ecosystem_db = processed_dir / "ecosystem.db"
    atm_data_db = processed_dir / "atm_data.db"

    _init_database(ecosystem_db)

    import src.utils
    src.utils.PROJECT_ROOT = tmp_dir
    src.utils.DB_PATH = atm_data_db
    src.utils.ECOSYSTEM_DB = ecosystem_db
    src.utils.DATA_RAW = tmp_dir / "data" / "raw"
    src.utils.DATA_PROCESSED = processed_dir
    src.utils.DATA_MODELS = tmp_dir / "data" / "models"
    src.utils.OUTPUTS_REPORTS = tmp_dir / "outputs" / "reports"
    src.utils.OUTPUTS_CHARTS = tmp_dir / "outputs" / "charts"
    src.utils.DATA_TRAINING = tmp_dir / "data" / "training"
    src.utils.ensure_dirs()

    # Run v2 schema migration (needs db_manager import, which uses src.utils paths)
    try:
        from scripts.migrate_database import run_migration
        run_migration()
    except Exception:
        pass

from src.interfaces.web import create_app

app = create_app()


@app.errorhandler(500)
def handle_500(e):
    from flask import render_template
    original = getattr(e, "original_exception", None) or e
    return render_template("error.html", message=str(original)), 500
