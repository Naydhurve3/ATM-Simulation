import numpy as np
import sqlite3
from src.data.db_manager import db

class SpendingForecaster:
    def __init__(self):
        self.metrics = {}

    def train(self, data=None):
        self.metrics = {"status": "Simple moving-average forecaster"}
        return self.metrics

    def predict(self, user_id=None, user_data=None):
        if user_id:
            try:
                conn = db.get_connection("ecosystem")
                txns = conn.execute("""
                    SELECT amount, type, timestamp FROM transactions
                    WHERE user_id = ? ORDER BY timestamp DESC LIMIT 20
                """, (user_id,)).fetchall()
                if not txns:
                    return self._default_prediction()
                withdraws = [t[0] for t in txns if t[1] == "withdraw" and t[0] > 0]
                deposits = [t[0] for t in txns if t[1] == "deposit" and t[0] > 0]
                avg_withdraw = np.mean(withdraws) if withdraws else 5000
                avg_deposit = np.mean(deposits) if deposits else 10000
                freq = len(txns)
                return {
                    "predicted_monthly_spend": int(avg_withdraw * max(freq // 2, 1)),
                    "predicted_monthly_deposit": int(avg_deposit * max(freq // 4, 1)),
                    "avg_transaction": int(np.mean([t[0] for t in txns])) if txns else 5000,
                    "confidence": "HIGH" if len(txns) > 10 else "MEDIUM" if len(txns) > 4 else "LOW",
                    "trend": "INCREASING" if avg_withdraw > avg_deposit else "DECREASING" if avg_deposit > avg_withdraw * 1.5 else "STABLE",
                }
            except:
                pass
        return self._default_prediction()

    def _default_prediction(self):
        return {
            "predicted_monthly_spend": 15000,
            "predicted_monthly_deposit": 20000,
            "avg_transaction": 5000,
            "confidence": "LOW",
            "trend": "STABLE",
        }

    def load(self):
        return True

    def save(self):
        pass
