"""Normalized schema definitions for v4."""
from enum import Enum

SCHEMA_VERSION = 2

ACCOUNTS_TABLE = """
CREATE TABLE IF NOT EXISTS accounts_v2 (
    account_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(user_id),
    bank TEXT NOT NULL DEFAULT '',
    account_number TEXT UNIQUE NOT NULL,
    card_number TEXT UNIQUE NOT NULL DEFAULT '',
    account_type TEXT DEFAULT 'savings',
    balance_paise INTEGER DEFAULT 500000,
    daily_limit_paise INTEGER DEFAULT 5000000,
    used_today_paise INTEGER DEFAULT 0,
    credit_score INTEGER DEFAULT 600,
    is_minor BOOLEAN DEFAULT 0,
    account_status TEXT DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP
);
"""

TRANSACTIONS_TABLE = """
CREATE TABLE IF NOT EXISTS transactions_v2 (
    txn_id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER NOT NULL REFERENCES accounts_v2(account_id),
    user_id INTEGER NOT NULL REFERENCES users(user_id),
    type TEXT NOT NULL,
    amount_paise INTEGER DEFAULT 0,
    fee_paise INTEGER DEFAULT 0,
    balance_before_paise INTEGER DEFAULT 0,
    balance_after_paise INTEGER DEFAULT 0,
    channel TEXT DEFAULT 'atm',
    target_account TEXT DEFAULT '',
    notes TEXT DEFAULT '',
    is_fraud BOOLEAN DEFAULT 0,
    fraud_score REAL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

SCHEMA_REGISTRY = """
CREATE TABLE IF NOT EXISTS schema_registry (
    version INTEGER PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);
"""

ALL_TABLES = [ACCOUNTS_TABLE, TRANSACTIONS_TABLE, SCHEMA_REGISTRY]
