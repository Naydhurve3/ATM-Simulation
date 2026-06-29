import numpy as np
import sqlite3
from datetime import datetime, timedelta
from sklearn.ensemble import IsolationForest


class RealTimeFraudDetector:
    def __init__(self):
        self.model = None
        self.user_baselines = {}
        self.is_trained = False

    def _extract_features(self, txns):
        features = []
        for t in txns:
            dt = datetime.strptime(t.get("timestamp", ""), "%Y-%m-%d %H:%M:%S") if t.get("timestamp") else datetime.now()
            hour = t.get("hour", dt.hour)
            day_of_week = t.get("day_of_week", dt.weekday())
            features.append([
                t.get("amount", 0),
                hour,
                day_of_week,
                1 if day_of_week >= 5 else 0,
                t.get("amount_to_balance_ratio", t.get("amount", 0) / max(t.get("balance", 1), 1))
            ])
        return np.array(features)

    def train(self, user_transactions):
        if not user_transactions:
            return self
        X = self._extract_features(user_transactions)
        self.model = IsolationForest(contamination=0.1, random_state=42)
        self.model.fit(X)
        amounts = [t["amount"] for t in user_transactions]
        hours = [t.get("hour", 0) for t in user_transactions]
        self.user_baselines = {
            "avg_amount": float(np.mean(amounts)),
            "std_amount": float(np.std(amounts)) if len(amounts) > 1 else 0.0,
            "hourly_distribution": np.bincount(hours, minlength=24).tolist() if hours else [0] * 24
        }
        self.is_trained = True
        return self

    def score(self, transaction, user_data):
        amount = transaction.get("amount", 0)
        hour = transaction.get("hour", 0)
        balance = user_data.get("balance", 0)
        recent_txns = user_data.get("recent_txns", [])
        reasons = []
        rule_score = 0.0

        avg_amount = self.user_baselines.get("avg_amount", 0)
        std_amount = self.user_baselines.get("std_amount", 0)

        if avg_amount > 0 and amount > 3 * avg_amount:
            rule_score += 0.3
            reasons.append("amount_3x_above_avg")

        if balance > 0 and amount > balance * 0.8:
            rule_score += 0.2
            reasons.append("amount_above_80pct_balance")

        if 0 <= hour <= 5:
            rule_score += 0.15
            reasons.append("unusual_hour")

        recent_timestamps = [t.get("timestamp", "") for t in recent_txns if t.get("timestamp")]
        recent_count = 0
        if recent_timestamps:
            now = datetime.strptime(transaction.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S")), "%Y-%m-%d %H:%M:%S")
            five_min_ago = now - timedelta(minutes=5)
            for ts in recent_timestamps:
                try:
                    t_dt = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
                    if t_dt >= five_min_ago:
                        recent_count += 1
                except ValueError:
                    pass
        if recent_count > 2:
            rule_score += 0.25
            reasons.append("high_frequency_5min")

        if std_amount > 0 and avg_amount > 0 and amount > avg_amount + 2 * std_amount:
            rule_score += 0.2
            reasons.append("amount_2std_above_avg")

        rule_score = min(rule_score, 1.0)

        ml_score = 0.0
        if self.is_trained and self.model is not None:
            features = np.array([[
                amount,
                hour,
                transaction.get("day_of_week", 0),
                1 if transaction.get("day_of_week", 0) >= 5 else 0,
                amount / max(balance, 1)
            ]])
            raw = self.model.decision_function(features)[0]
            ml_score = 1.0 - (raw + 0.5)
            ml_score = max(0.0, min(1.0, ml_score))
            final_score = 0.4 * rule_score + 0.6 * ml_score
            method = "hybrid"
        else:
            final_score = rule_score
            method = "rule_only"

        return {
            "fraud_score": round(final_score, 4),
            "is_suspicious": final_score > 0.6,
            "reasons": reasons,
            "method": method
        }

    def get_fraud_alerts(self, user_id, ecosystem_db_path):
        conn = sqlite3.connect(str(ecosystem_db_path))
        c = conn.cursor()
        c.execute("""
            SELECT flag_id, txn_id, user_id, anomaly_score, flagged_by,
                   is_confirmed, flagged_at
            FROM fraud_flags
            WHERE user_id = ?
            ORDER BY flagged_at DESC
        """, (user_id,))
        cols = [d[0] for d in c.description]
        rows = c.fetchall()
        conn.close()
        return [dict(zip(cols, row)) for row in rows]

    def log_alert(self, user_id, transaction, score, reasons, user_manager):
        c = user_manager.conn.cursor()
        c.execute("""
            INSERT INTO fraud_flags (user_id, anomaly_score, flagged_by)
            VALUES (?, ?, ?)
        """, (user_id, score, "RealTimeFraudDetector"))
        user_manager.conn.commit()
        return c.lastrowid
