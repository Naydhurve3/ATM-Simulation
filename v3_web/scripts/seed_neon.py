"""Seed Neon PostgreSQL with industry (RBI) data + demo user.

Idempotent: safe to run repeatedly. Requires DATABASE_URL in the environment.
Usage: python scripts/seed_neon.py
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "v1_banking_core"))

from banking_core.data.postgres_adapter import is_enabled, get_pg_connection, init_db


def _industry_from_sqlite(conn, table):
    import sqlite3
    from banking_core.utils import DB_PATH
    if not DB_PATH.exists():
        return None
    sconn = sqlite3.connect(str(DB_PATH))
    df = __import__("pandas").read_sql(f"SELECT * FROM {table}", sconn)
    sconn.close()
    return df


def main():
    if not is_enabled():
        print("DATABASE_URL not set — nothing to do.")
        return
    init_db()

    import pandas as pd
    from banking_core.data.postgres_adapter import write_dataframe
    from banking_core.data_ingestion import DataIngestion

    # 1) Industry tables: prefer local sqlite snapshot, else build from raw CSV
    sources = {t: _industry_from_sqlite(None, t) for t in ("atm_card_stats", "bank_summary", "monthly_aggregate")}
    missing = [t for t, df in sources.items() if df is None]
    if missing:
        print(f"Rebuilding from raw CSV (missing locally: {missing})...")
        di = DataIngestion()
        di.run_pipeline()
        for t in ("atm_card_stats", "bank_summary", "monthly_aggregate"):
            df = _industry_from_sqlite(None, t)
            if df is not None:
                sources[t] = df

    for t, df in sources.items():
        if df is not None and len(df):
            write_dataframe(df, t)
            print(f"seeded {t}: {len(df)} rows")

    # 2) Demo user (init_db creates it if absent)
    conn = get_pg_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users WHERE email = 'demo@atm.com'")
    print("demo users:", cur.fetchone()[0])

    # 3) Sample transactions for the demo user (idempotent)
    cur.execute("SELECT user_id FROM users WHERE email = 'demo@atm.com'")
    row = cur.fetchone()
    if row:
        uid = row[0]
        cur.execute("SELECT COUNT(*) FROM transactions WHERE user_id = %s", (uid,))
        if cur.fetchone()[0] == 0:
            import random
            random.seed(7)
            bal = 50000.0
            kinds = [("deposit", 2000, 20000), ("withdraw", 500, 10000), ("transfer", 100, 5000)]
            for i in range(24):
                kind, lo, hi = random.choice(kinds)
                amt = round(random.uniform(lo, hi), 2)
                bal_before = bal
                bal = round(bal + amt if kind == "deposit" else bal - amt, 2)
                ch = random.choice(["atm", "atm", "online", "pos", "branch"])
                cur.execute(
                    "INSERT INTO transactions (user_id, type, amount, fee, balance_before, balance_after,"
                    " channel, bank, notes_given, timestamp) VALUES (%s,%s,%s,0,%s,%s,%s,%s,'seed',"
                    "CURRENT_TIMESTAMP - (%s || ' days')::interval)",
                    (uid, kind, amt, bal_before, bal, ch, "HDFC BANK LTD", i * 3 + 1),
                )
            conn.commit()
            print("seeded 24 demo transactions")
        else:
            print("demo transactions already present")
    conn.close()
    print("done.")


if __name__ == "__main__":
    main()
