import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import GridSearchCV
import joblib
from pathlib import Path
from src.utils import DATA_MODELS
from src.data.db_manager import db

MODEL_PATH = DATA_MODELS / "credit_scorer.pkl"

class CreditScorer:
    def __init__(self):
        self.model = None
        self.is_trained = False
        self.metrics = {}

    def _compute_base_score(self, row):
        score = 600
        age = row.get("age", 30)
        is_minor = row.get("is_minor", 0)
        if is_minor:
            score = 650
            score += min(row.get("balance", 0) / 1000, 50)
            return min(score, 750)
        income = row.get("income_bracket", "not_earning_student")
        income_map = {"earning_25L_plus": 80, "earning_10L_25L": 60,
                      "earning_5L_10L": 40, "earning_2.5L_5L": 20,
                      "not_earning_retired": 10}
        for k, v in income_map.items():
            if k in income:
                score += v
        score += min(row.get("balance", 0) / 10000, 50)
        txn_count = row.get("txn_count", 0)
        if txn_count > 50:
            score += 30
        elif txn_count > 20:
            score += 15
        elif txn_count > 5:
            score += 5
        score -= row.get("fraud_count", 0) * 30
        return max(300, min(900, score))

    def train(self, data=None):
        if data is None:
            try:
                data = pd.read_sql("""
                    SELECT u.*, COUNT(t.txn_id) as txn_count,
                           COALESCE(SUM(CASE WHEN t.is_fraud=1 THEN 1 ELSE 0 END),0) as fraud_count
                    FROM users u LEFT JOIN transactions t ON u.user_id = t.user_id
                    GROUP BY u.user_id
                """, db.get_connection("ecosystem"))
            except:
                self.metrics = {"status": "No training data available"}
                return self.metrics
        if data.empty or len(data) < 3:
            self.metrics = {"status": "Insufficient data (need 3+ samples)"}
            return self.metrics
        data["base_score"] = data.apply(self._compute_base_score, axis=1)
        features = ["age", "balance", "txn_count", "fraud_count"]
        X = data[features].fillna(0)
        y = data["base_score"].values
        if len(X) < 5:
            self.metrics = {"samples": len(X), "method": "rule-based only",
                            "status": "using rule-based scoring"}
            self.is_trained = False
            return self.metrics
        param_grid = {"n_estimators": [50, 100, 200], "max_depth": [3, 5], "learning_rate": [0.05, 0.1]}
        gs = GridSearchCV(GradientBoostingRegressor(random_state=42), param_grid, cv=3, scoring="neg_mean_absolute_error", n_jobs=-1)
        gs.fit(X, y)
        self.model = gs.best_estimator_
        self.is_trained = True
        preds = self.model.predict(X)
        mae = np.mean(np.abs(preds - y))
        self.metrics = {"MAE": round(mae, 2), "samples": len(X), "R2": round(self.model.score(X, y), 4), "best_params": str(gs.best_params_)}
        joblib.dump({"model": self.model, "metrics": self.metrics}, MODEL_PATH)
        return self.metrics

    def predict(self, user_data):
        score = self._compute_base_score(user_data)
        if self.model and self.is_trained:
            features = np.array([[user_data.get("age", 30),
                                  user_data.get("balance", 0),
                                  user_data.get("txn_count", 0),
                                  user_data.get("fraud_count", 0)]])
            ml_score = self.model.predict(features)[0]
            score = int(0.3 * score + 0.7 * ml_score)
        return max(300, min(900, score))

    def load(self):
        if MODEL_PATH.exists():
            try:
                data = joblib.load(MODEL_PATH)
                self.model = data["model"]
                self.metrics = data["metrics"]
                self.is_trained = True
                return True
            except:
                pass
        return False

    def save(self):
        if self.model and self.is_trained:
            joblib.dump({"model": self.model, "metrics": self.metrics}, MODEL_PATH)
