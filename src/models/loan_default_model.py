import numpy as np
import pandas as pd
import sqlite3
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GridSearchCV
import joblib
from src.utils import DATA_MODELS
from src.data.db_manager import db

MODEL_PATH = DATA_MODELS / "loan_default_model.pkl"

class LoanDefaultModel:
    def __init__(self):
        self.model = None
        self.is_trained = False
        self.metrics = {}

    def train(self, data=None):
        if data is None:
            try:
                data = pd.read_sql("""
                    SELECT l.*, u.age, u.income_bracket, u.balance,
                           u.credit_score, u.is_minor, u.bank
                    FROM loan_applications l
                    JOIN users u ON l.user_id = u.user_id
                """, db.get_connection("ecosystem"))
            except:
                self.metrics = {"status": "No loan data available"}
                return self.metrics
        if data.empty or len(data) < 5:
            self.metrics = {"status": "Insufficient loan data", "samples": len(data) if not data.empty else 0}
            return self.metrics
        data["is_minor"] = data["is_minor"].astype(int)
        data["defaulted"] = (data["status"] == "defaulted").astype(int)
        features = ["age", "credit_score", "balance", "amount_requested",
                     "interest_rate", "tenure_months", "is_minor"]
        X = data[features].fillna(0)
        y = data["defaulted"]
        if y.sum() < 1:
            y.iloc[0] = 1
        param_grid = {"C": [0.1, 1.0, 10.0], "penalty": ["l2"], "solver": ["lbfgs", "liblinear"]}
        gs = GridSearchCV(LogisticRegression(random_state=42, max_iter=500, class_weight="balanced"), param_grid, cv=3, scoring="accuracy", n_jobs=-1)
        gs.fit(X, y)
        self.model = gs.best_estimator_
        self.is_trained = True
        acc = self.model.score(X, y)
        coef_dict = dict(zip(features, self.model.coef_[0]))
        self.metrics = {"Accuracy": round(acc, 4), "samples": len(X),
                        "top_factor": max(coef_dict, key=coef_dict.get),
                        "best_params": str(gs.best_params_)}
        joblib.dump({"model": self.model, "metrics": self.metrics}, MODEL_PATH)
        return self.metrics

    def predict(self, user_data, loan_amount, loan_rate, tenure):
        if user_data.get("is_minor", False):
            return {"risk_score": 0.0, "eligible": False,
                    "reason": "Minors not eligible for loans"}
        base_risk = 0.3
        cs = user_data.get("credit_score", 600)
        if cs < 500:
            base_risk += 0.3
        elif cs < 650:
            base_risk += 0.15
        elif cs > 750:
            base_risk -= 0.15
        bal = user_data.get("balance", 0)
        if loan_amount > bal * 10:
            base_risk += 0.2
        if self.model and self.is_trained:
            features = np.array([[user_data.get("age", 30), cs, bal,
                                   loan_amount, loan_rate, tenure, 0]])
            prob = self.model.predict_proba(features)[0][1]
            base_risk = float(0.3 * base_risk + 0.7 * prob)
        risk = max(0.01, min(0.99, base_risk))
        return {
            "risk_score": round(risk, 3),
            "eligible": risk < 0.7,
            "risk_level": "LOW" if risk < 0.3 else "MEDIUM" if risk < 0.6 else "HIGH",
            "recommended_max": int(bal * 5),
        }

    def generate_amortization_schedule(self, loan_amount, annual_rate, tenure_months):
        monthly_rate = annual_rate / 1200
        emi = loan_amount * monthly_rate * (1 + monthly_rate)**tenure_months / ((1 + monthly_rate)**tenure_months - 1)
        schedule = []
        balance = loan_amount
        for month in range(1, tenure_months + 1):
            interest = balance * monthly_rate
            principal = emi - interest
            balance -= principal
            schedule.append({
                "month": month,
                "payment": round(emi, 2),
                "interest": round(interest, 2),
                "principal": round(principal, 2),
                "balance": round(max(balance, 0), 2),
            })
        return schedule

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
