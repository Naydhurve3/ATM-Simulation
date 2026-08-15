"""
Database migration: create normalized v2 tables alongside existing flat schema.
Reads from existing `users` / `transactions` tables, creates normalized
`accounts_v2` / `transactions_v2`, then copies existing data.

Usage:
    python scripts/migrate_database.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from banking_core.data.db_manager import db
from banking_core.infrastructure.database.schema import ALL_TABLES, SCHEMA_REGISTRY, SCHEMA_VERSION


def get_current_version(conn) -> int:
    c = conn.cursor()
    try:
        c.execute("SELECT MAX(version) FROM schema_registry")
        row = c.fetchone()
        return row[0] if row and row[0] else 0
    except Exception:
        return 0


def run_migration():
    conn = db.get_connection("ecosystem")
    current = get_current_version(conn)

    if current >= SCHEMA_VERSION:
        print(f"[v4] Schema already at version {SCHEMA_VERSION}. Nothing to do.")
        return

    print(f"[v4] Migrating schema from v{current} to v{SCHEMA_VERSION}...")

    c = conn.cursor()

    for ddl in ALL_TABLES:
        c.executescript(ddl)
    conn.commit()
    print("[v4] Created v2 tables: accounts_v2, transactions_v2, schema_registry")

    c.execute("SELECT COUNT(*) FROM accounts_v2")
    existing = c.fetchone()[0]

    if existing == 0:
        c.execute("SELECT * FROM users")
        cols = [d[0] for d in c.description]
        col_map = {name: i for i, name in enumerate(cols)}
        rows = c.fetchall()
        for row in rows:
            balance_paise = int(round((row[col_map["balance"]] or 0) * 100))
            limit_paise = int(round((row[col_map["atm_daily_limit"]] or 0) * 100))
            used_paise = int(round((row[col_map["atm_used_today"]] or 0) * 100))
            c.execute("""
                INSERT INTO accounts_v2
                    (user_id, bank, account_number, card_number, account_type,
                     balance_paise, daily_limit_paise, used_today_paise,
                     credit_score, is_minor)
                VALUES (?,?,?,?,?,?,?,?,?,?)
            """, (
                row[col_map["user_id"]],
                row[col_map["bank"]],
                row[col_map["account_no"]],
                row[col_map["card_no"]],
                row[col_map["account_type"]],
                balance_paise, limit_paise, used_paise,
                row[col_map["credit_score"]],
                bool(row[col_map["is_minor"]]),
            ))
        conn.commit()
        print(f"[v4] Migrated {len(rows)} users -> accounts_v2")

        c.execute("SELECT * FROM transactions")
        txn_cols = [d[0] for d in c.description]
        txn_map = {name: i for i, name in enumerate(txn_cols)}
        txn_rows = c.fetchall()
        migrated_txns = 0
        for row in txn_rows:
            user_id = row[txn_map["user_id"]]
            c.execute("SELECT account_id FROM accounts_v2 WHERE user_id = ?", (user_id,))
            acct_row = c.fetchone()
            if not acct_row:
                continue
            account_id = acct_row[0]
            amount_paise = int(round((row[txn_map["amount"]] or 0) * 100))
            fee_paise = int(round((row[txn_map["fee"]] or 0) * 100))
            bb_paise = int(round((row[txn_map["balance_before"]] or 0) * 100))
            ba_paise = int(round((row[txn_map["balance_after"]] or 0) * 100))
            c.execute("""
                INSERT INTO transactions_v2
                    (account_id, user_id, type, amount_paise, fee_paise,
                     balance_before_paise, balance_after_paise,
                     channel, target_account, notes,
                     is_fraud, fraud_score, timestamp)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                account_id, user_id, row[txn_map["type"]],
                amount_paise, fee_paise, bb_paise, ba_paise,
                row[txn_map["channel"]] or "atm",
                row[txn_map["target_account"]] or "",
                row[txn_map["notes_given"]] or "",
                bool(row[txn_map["is_fraud"]]),
                row[txn_map["fraud_score"]],
                row[txn_map["timestamp"]],
            ))
            migrated_txns += 1
        conn.commit()
        print(f"[v4] Migrated {migrated_txns} transactions → transactions_v2")

    c.execute(
        "INSERT INTO schema_registry (version, description) VALUES (?, ?)",
        (SCHEMA_VERSION, "Normalized accounts_v2 + transactions_v2 with paise integers"),
    )
    conn.commit()
    print(f"[v4] Migration to v{SCHEMA_VERSION} complete.")


if __name__ == "__main__":
    run_migration()
