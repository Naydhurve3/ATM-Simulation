import numpy as np
import pandas as pd
import sqlite3
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GridSearchCV
import joblib
from src.utils import DATA_MODELS
from src.data.db_manager import db

MODEL_PATH = DATA_MODELS / "churn_predictor.pkl"

class ChurnPredictor:
    def __init__(self):
        self.model = None
        self.is_trained = False
        self.metrics = {}

    def train(self, data=None):
        if data is None:
            try:
                data = pd.read_sql("""
                    SELECT u.user_id, u.age, u.age_group, u.is_minor,
                           u.income_bracket, u.balance, u.credit_score,
                           COUNT(t.txn_id) as txn_count,
                           COALESCE(SUM(t.amount),0) as total_volume,
                           COALESCE(AVG(t.amount),0) as avg_txn,
                           COALESCE(CAST(julianday('now') - julianday(MAX(t.timestamp)) AS INTEGER),365) as days_since_last
                    FROM users u
                    LEFT JOIN transactions t ON u.user_id = t.user_id
                    GROUP BY u.user_id
                """, db.get_connection("ecosystem"))
            except:
                self.metrics = {"status": "No data"}
                return self.metrics
        if data.empty or len(data) < 5:
            self.metrics = {"status": "Insufficient data", "samples": len(data) if not data.empty else 0}
            return self.metrics
        data["churned"] = (data["days_since_last"] > 60).astype(int)
        features = ["age", "balance", "credit_score", "txn_count",
                     "total_volume", "avg_txn", "days_since_last"]
        X = data[features].fillna(0)
        y = data["churned"]
        if y.sum() < 2 or (len(y) - y.sum()) < 2:
            self.metrics = {"status": "Imbalanced data (need both churned and active)"}
            return self.metrics
        param_grid = {"n_estimators": [50, 100, 200], "max_depth": [3, 5, 7], "min_samples_split": [2, 5]}
        gs = GridSearchCV(RandomForestClassifier(random_state=42), param_grid, cv=3, scoring="accuracy", n_jobs=-1)
        gs.fit(X, y)
        self.model = gs.best_estimator_
        self.is_trained = True
        acc = self.model.score(X, y)
        self.metrics = {
            "Accuracy": round(acc, 4),
            "Churn_Rate": f"{y.mean()*100:.1f}%",
            "samples": len(X),
            "top_feature": features[np.argmax(self.model.feature_importances_)],
            "best_params": str(gs.best_params_)
        }
        joblib.dump({"model": self.model, "metrics": self.metrics}, MODEL_PATH)
        return self.metrics

    def predict(self, user_data):
        if not self.model or not self.is_trained:
            days = user_data.get("days_since_last_txn", 0)
            base_risk = min(days / 90, 1.0) if days > 30 else 0.05
            return {"risk_score": round(base_risk, 3), "risk_level": "HIGH" if base_risk > 0.5 else "LOW",
                    "method": "rule-based"}
        features = np.array([[user_data.get("age", 30),
                               user_data.get("balance", 0),
                               user_data.get("credit_score", 600),
                               user_data.get("txn_count", 0),
                               user_data.get("total_volume", 0),
                               user_data.get("avg_txn", 0),
                               user_data.get("days_since_last_txn", 0)]])
        prob = self.model.predict_proba(features)[0][1]
        level = "HIGH" if prob > 0.5 else "MEDIUM" if prob > 0.25 else "LOW"
        return {"risk_score": round(float(prob), 3), "risk_level": level, "method": "ml"}

    def load(self):
        if MODEL_PATH.exists():
            try:
                d = joblib.load(MODEL_PATH)
                self.model = d["model"]
                self.metrics = d["metrics"]
                self.is_trained = True
                return True
            except:
                pass
        return False

    def save(self):
        if self.model:
            joblib.dump({"model": self.model, "metrics": self.metrics}, MODEL_PATH)
