import pandas as pd
import json
from datetime import datetime
from src.data.db_manager import db


class FeatureStore:
    def __init__(self):
        self._register_default_features()

    @property
    def conn(self):
        return db.get_connection("feature_store")

    @property
    def eco_conn(self):
        return db.get_connection("ecosystem")

    def _register_default_features(self):
        defaults = [
            ("user_age", "user", "User age", "u.age", "INTEGER"),
            ("user_age_group", "user", "Age group label", "u.age_group", "TEXT"),
            ("user_is_minor", "user", "Minor flag", "u.is_minor", "BOOLEAN"),
            ("user_income_bracket", "user", "Income bracket code", "u.income_bracket", "TEXT"),
            ("user_balance", "user", "Current account balance", "u.balance", "REAL"),
            ("user_credit_score", "user", "Current credit score", "u.credit_score", "INTEGER"),
            ("user_account_age_days", "user", "Days since account creation",
             "CAST(CAST(strftime('%s','now') AS INTEGER) - CAST(strftime('%s',u.created_at) AS INTEGER) AS REAL) / 86400.0", "REAL"),
            ("user_days_since_active", "user", "Days since last activity",
             "CAST(CAST(strftime('%s','now') AS INTEGER) - CAST(COALESCE(CAST(strftime('%s',u.last_active) AS INTEGER),0) AS INTEGER) AS REAL) / 86400.0", "REAL"),
            ("txn_count_30d", "user", "Transaction count in last 30 days",
             "COUNT(CASE WHEN t.timestamp >= datetime('now','-30 days') THEN 1 END)", "INTEGER"),
            ("txn_total_30d", "user", "Total transaction amount in last 30 days",
             "COALESCE(SUM(CASE WHEN t.timestamp >= datetime('now','-30 days') THEN t.amount ELSE 0 END),0)", "REAL"),
            ("txn_avg_amount", "user", "Average transaction amount",
             "COALESCE(AVG(t.amount),0)", "REAL"),
            ("txn_total_fees", "user", "Total fees paid",
             "COALESCE(SUM(t.fee),0)", "REAL"),
            ("txn_fraud_count", "user", "Number of flagged fraud transactions",
             "COALESCE(SUM(CASE WHEN t.is_fraud=1 THEN 1 ELSE 0 END),0)", "INTEGER"),
            ("deposit_total", "user", "Total deposits",
             "COALESCE(SUM(CASE WHEN t.type='deposit' THEN t.amount ELSE 0 END),0)", "REAL"),
            ("withdraw_total", "user", "Total withdrawals",
             "COALESCE(SUM(CASE WHEN t.type='withdraw' THEN t.amount ELSE 0 END),0)", "REAL"),
            ("bank_digital_share", "bank", "Bank's digital transaction share", None, "REAL"),
            ("bank_atm_density", "bank", "Total ATMs per bank", None, "REAL"),
            ("bank_total_volume", "bank", "Bank's total transaction volume", None, "REAL"),
            ("bank_type", "bank", "Bank type (PSU/PVT/FOREIGN/SFB)", None, "TEXT"),
            ("loan_amount", "loan", "Loan amount requested",
             "l.amount_requested", "REAL"),
            ("loan_interest_rate", "loan", "Loan interest rate",
             "l.interest_rate", "REAL"),
            ("loan_tenure", "loan", "Loan tenure in months",
             "l.tenure_months", "INTEGER"),
            ("loan_risk_score", "loan", "Loan risk score",
             "l.risk_score", "REAL"),
        ]
        for name, fset, desc, sql, dtype in defaults:
            try:
                self.conn.execute(
                    "INSERT OR IGNORE INTO feature_definitions (feature_name, feature_set, description, sql_expression, data_type) VALUES (?, ?, ?, ?, ?)",
                    (name, fset, desc, sql, dtype)
                )
            except Exception:
                pass
        self.conn.commit()

    def compute_user_features(self, user_ids=None):
        base = """
            SELECT u.user_id, {features}
            FROM users u
            LEFT JOIN transactions t ON u.user_id = t.user_id
        """
        feature_cols = [
            "u.age as user_age",
            "u.age_group as user_age_group",
            "u.is_minor as user_is_minor",
            "u.income_bracket as user_income_bracket",
            "u.balance as user_balance",
            "u.credit_score as user_credit_score",
            "CAST(CAST(strftime('%s','now') AS INTEGER) - CAST(strftime('%s',u.created_at) AS INTEGER) AS REAL) / 86400.0 as user_account_age_days",
            "CAST(CAST(strftime('%s','now') AS INTEGER) - CAST(COALESCE(CAST(strftime('%s',u.last_active) AS INTEGER),0) AS INTEGER) AS REAL) / 86400.0 as user_days_since_active",
            "COUNT(CASE WHEN t.timestamp >= datetime('now','-30 days') THEN 1 END) as txn_count_30d",
            "COALESCE(SUM(CASE WHEN t.timestamp >= datetime('now','-30 days') THEN t.amount ELSE 0 END),0) as txn_total_30d",
            "COALESCE(AVG(t.amount),0) as txn_avg_amount",
            "COALESCE(SUM(t.fee),0) as txn_total_fees",
            "COALESCE(SUM(CASE WHEN t.is_fraud=1 THEN 1 ELSE 0 END),0) as txn_fraud_count",
            "COALESCE(SUM(CASE WHEN t.type='deposit' THEN t.amount ELSE 0 END),0) as deposit_total",
            "COALESCE(SUM(CASE WHEN t.type='withdraw' THEN t.amount ELSE 0 END),0) as withdraw_total",
        ]
        sql = base.format(features=", ".join(feature_cols))
        if user_ids:
            placeholders = ",".join(["?" for _ in user_ids])
            sql += f" WHERE u.user_id IN ({placeholders})"
        sql += " GROUP BY u.user_id"
        params = user_ids if user_ids else None
        df = pd.read_sql(sql, self.eco_conn, params=params)
        return df

    def compute_bank_features(self):
        from src.data.db_manager import db as dbm
        atm_conn = dbm.get_connection("atm_data")
        try:
            df = pd.read_sql("""
                SELECT Bank_Name as bank_name,
                       Bank_Type as bank_type,
                       Digital_Share as bank_digital_share,
                       Total_ATMs as bank_atm_density,
                       Total_Txn_Vol as bank_total_volume,
                       Total_Txn_Val as bank_total_value
                FROM bank_summary
            """, atm_conn)
        except Exception:
            df = pd.read_sql("""
                SELECT DISTINCT Bank_Name as bank_name,
                       Bank_Type as bank_type,
                       AVG(Digital_Share) as bank_digital_share,
                       AVG(Total_ATMs) as bank_atm_density,
                       SUM(Total_Txn_Vol) as bank_total_volume,
                       SUM(Total_Txn_Val) as bank_total_value
                FROM atm_card_stats
                GROUP BY Bank_Name
            """, atm_conn)
        return df

    def compute_loan_features(self, user_id=None):
        where = ""
        params = None
        if user_id:
            where = " WHERE l.user_id = ?"
            params = (user_id,)
        df = pd.read_sql(f"""
            SELECT l.*, u.age as user_age, u.age_group as user_age_group,
                   u.income_bracket as user_income_bracket,
                   u.bank as user_bank, u.credit_score as user_credit_score,
                   u.balance as user_balance
            FROM loan_applications l
            JOIN users u ON l.user_id = u.user_id
            {where}
        """, self.eco_conn, params=params)
        return df

    def save_snapshot(self, df, feature_set, label=None):
        cursor = self.conn.execute(
            "INSERT INTO feature_snapshots (feature_set, snapshot_label, row_count) VALUES (?, ?, ?)",
            (feature_set, label or f"snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}", len(df))
        )
        snapshot_id = cursor.lastrowid
        self.conn.commit()
        return snapshot_id

    def get_snapshot(self, snapshot_id):
        row = db.fetch_one("feature_store",
            "SELECT * FROM feature_snapshots WHERE snapshot_id = ?", (snapshot_id,))
        return row

    def register_feature(self, name, feature_set, description, sql_expr, data_type):
        self.conn.execute(
            "INSERT OR IGNORE INTO feature_definitions (feature_name, feature_set, description, sql_expression, data_type) VALUES (?, ?, ?, ?, ?)",
            (name, feature_set, description, sql_expr, data_type)
        )
        self.conn.commit()

    def get_features_by_set(self, feature_set):
        rows = db.fetch_all("feature_store",
            "SELECT * FROM feature_definitions WHERE feature_set = ? ORDER BY feature_id", (feature_set,))
        return rows

    def list_feature_sets(self):
        rows = db.fetch_all("feature_store",
            "SELECT DISTINCT feature_set FROM feature_definitions ORDER BY feature_set")
        return [r["feature_set"] for r in rows]
