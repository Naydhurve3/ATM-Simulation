import pandas as pd
import sqlite3
from datetime import datetime
from pathlib import Path
from src.utils import ECOSYSTEM_DB, DATA_TRAINING, get_scenario_timestamp, ensure_dirs
from src.data.db_manager import db
from src.data.data_catalog import DataCatalog

ensure_dirs()

class DataGenerator:
    def __init__(self):
        self.training_dir = DATA_TRAINING
        self.catalog = DataCatalog()

    @property
    def conn(self):
        return db.get_connection("ecosystem")

    def export_scenario(self, scenario_name):
        timestamp = get_scenario_timestamp()
        exporters = {
            "NEW_USER_MILESTONE": self._export_user_profiles,
            "FRAUD_ALERT": self._export_fraud_training,
            "LOAN_EVENT": self._export_loan_risk,
            "AGE_CONVERSION": self._export_user_milestones,
            "THRESHOLD_REACHED": self._export_transactions,
            "SESSION_END": self._export_engagement,
            "MANUAL_EXPORT": self._export_all,
            "MODEL_RETRAIN": self._export_all,
        }
        func = exporters.get(scenario_name, self._export_all)
        func(timestamp, scenario_name)

    def export_all(self, timestamp=None, scenario="MANUAL_EXPORT"):
        ts = timestamp or get_scenario_timestamp()
        self._export_user_profiles(ts, scenario)
        self._export_fraud_training(ts, scenario)
        self._export_loan_risk(ts, scenario)
        self._export_user_milestones(ts, scenario)
        self._export_transactions(ts, scenario)
        self._export_engagement(ts, scenario)
        self._export_credit_scoring(ts, scenario)
        self._export_churn_analysis(ts, scenario)
        self._export_spending_patterns(ts, scenario)
        self._export_bank_preferences(ts, scenario)
        try:
            self.catalog.record_schema("ecosystem")
        except Exception:
            pass

    def _export_with_catalog(self, df, dataset_type, scenario, ts):
        if df.empty:
            return None
        path = self.training_dir / f"{dataset_type}_{scenario}_{ts}.csv"
        df.to_csv(path, index=False)
        try:
            self.catalog.log_export(scenario, dataset_type, path, df)
        except Exception:
            pass
        return path

    def _export_user_profiles(self, ts, scenario):
        try:
            df = pd.read_sql("""
                SELECT user_id, name, age, age_group, is_minor,
                       income_status, income_bracket, bank, account_type,
                       balance, credit_score, is_active,
                       CAST(strftime('%s',last_active) - strftime('%s',created_at) AS REAL) as account_age_seconds
                FROM users WHERE is_active = 1
            """, self.conn)
            self._export_with_catalog(df, "user_profiles", scenario, ts)
        except Exception as e:
            pass

    def _export_transactions(self, ts, scenario):
        try:
            df = pd.read_sql("""
                SELECT t.txn_id, t.user_id, t.type, t.amount, t.fee,
                       t.balance_before, t.balance_after, t.channel,
                       t.bank, t.is_fraud, t.fraud_score, t.timestamp,
                       u.age_group, u.is_minor, u.bank as user_bank
                FROM transactions t
                JOIN users u ON t.user_id = u.user_id
                ORDER BY t.timestamp DESC LIMIT 5000
            """, self.conn)
            self._export_with_catalog(df, "transaction_history", scenario, ts)
        except Exception as e:
            pass

    def _export_fraud_training(self, ts, scenario):
        try:
            df = pd.read_sql("""
                SELECT f.*, t.type, t.amount, t.fee, t.balance_before,
                       t.channel, u.age_group, u.is_minor, u.bank
                FROM fraud_flags f
                JOIN transactions t ON f.txn_id = t.txn_id
                JOIN users u ON f.user_id = u.user_id
                ORDER BY f.flagged_at DESC
            """, self.conn)
            self._export_with_catalog(df, "fraud_training", scenario, ts)
        except Exception as e:
            pass

    def _export_credit_scoring(self, ts, scenario):
        try:
            df = pd.read_sql("""
                SELECT u.user_id, u.age, u.age_group, u.is_minor,
                       u.income_status, u.income_bracket, u.bank,
                       u.account_type, u.balance, u.credit_score,
                       COUNT(t.txn_id) as txn_count,
                       COALESCE(SUM(CASE WHEN t.type='deposit' THEN t.amount ELSE 0 END),0) as total_deposits,
                       COALESCE(SUM(CASE WHEN t.type='withdraw' THEN t.amount ELSE 0 END),0) as total_withdrawals,
                       COALESCE(SUM(t.fee),0) as total_fees,
                       COALESCE(AVG(t.amount),0) as avg_txn_amount,
                       CAST(COALESCE(SUM(CASE WHEN t.is_fraud=1 THEN 1 ELSE 0 END),0) AS INTEGER) as fraud_count
                FROM users u
                LEFT JOIN transactions t ON u.user_id = t.user_id
                GROUP BY u.user_id
            """, self.conn)
            self._export_with_catalog(df, "credit_scoring", scenario, ts)
        except:
            pass

    def _export_loan_risk(self, ts, scenario):
        try:
            df = pd.read_sql("""
                SELECT l.*, u.age, u.age_group, u.income_bracket,
                       u.bank, u.credit_score, u.balance
                FROM loan_applications l
                JOIN users u ON l.user_id = u.user_id
                ORDER BY l.applied_at DESC
            """, self.conn)
            self._export_with_catalog(df, "loan_risk_data", scenario, ts)
        except:
            pass

    def _export_churn_analysis(self, ts, scenario):
        try:
            df = pd.read_sql("""
                SELECT u.user_id, u.age, u.age_group, u.is_minor,
                       u.income_bracket, u.bank, u.account_type,
                       u.balance, u.credit_score,
                       COUNT(t.txn_id) as total_txns,
                       COALESCE(SUM(t.amount),0) as total_volume,
                       CAST(COALESCE(MAX(CAST(strftime('%s',t.timestamp) AS INTEGER)),0) AS REAL) as last_txn_ts,
                       CAST(strftime('%s','now') AS REAL) - CAST(COALESCE(MAX(CAST(strftime('%s',t.timestamp) AS INTEGER)),0) AS REAL) as days_since_last_txn
                FROM users u
                LEFT JOIN transactions t ON u.user_id = t.user_id
                GROUP BY u.user_id
            """, self.conn)
            self._export_with_catalog(df, "churn_analysis", scenario, ts)
        except:
            pass

    def _export_spending_patterns(self, ts, scenario):
        try:
            df = pd.read_sql("""
                SELECT u.user_id, u.age_group, u.is_minor, u.bank,
                       t.type, COUNT(*) as count,
                       SUM(t.amount) as total,
                       AVG(t.amount) as avg_amount,
                       u.balance
                FROM transactions t
                JOIN users u ON t.user_id = u.user_id
                GROUP BY u.user_id, t.type
            """, self.conn)
            self._export_with_catalog(df, "spending_patterns", scenario, ts)
        except:
            pass

    def _export_bank_preferences(self, ts, scenario):
        try:
            df = pd.read_sql("""
                SELECT bank, account_type,
                       COUNT(*) as user_count,
                       AVG(balance) as avg_balance,
                       AVG(credit_score) as avg_credit_score,
                       SUM(CASE WHEN is_minor=1 THEN 1 ELSE 0 END) as minor_count
                FROM users
                GROUP BY bank, account_type
            """, self.conn)
            self._export_with_catalog(df, "bank_preferences", scenario, ts)
        except:
            pass

    def _export_user_milestones(self, ts, scenario):
        try:
            df = pd.read_sql("""
                SELECT user_id, name, age, age_group, is_minor,
                       guardian_name, bank, account_type, balance,
                       created_at, last_active
                FROM users
                ORDER BY created_at DESC LIMIT 100
            """, self.conn)
            self._export_with_catalog(df, "user_milestones", scenario, ts)
        except:
            pass

    def _export_engagement(self, ts, scenario):
        try:
            df = pd.read_sql("""
                SELECT s.*, u.name, u.age_group, u.bank
                FROM user_sessions s
                JOIN users u ON s.user_id = u.user_id
                ORDER BY s.login_at DESC LIMIT 500
            """, self.conn)
            if not df.empty:
                path = self.training_dir / f"engagement_metrics_{scenario}_{ts}.csv"
                df.to_csv(path, index=False)
        except:
            pass

    def close(self):
        pass
