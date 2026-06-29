import pandas as pd
import numpy as np
import sqlite3
from sklearn.linear_model import LinearRegression
from src.models.base_model import BaseModel
from src.utils import DB_PATH

class WhatIfSimulator(BaseModel):
    def __init__(self):
        super().__init__("what_if_simulator")
        self.model = LinearRegression()
        self.coefficients = {}
        self.feature_cols = []

    def _get_data(self, target="DC_Vol_Cash_ATM"):
        conn = sqlite3.connect(str(DB_PATH))
        df = pd.read_sql("SELECT * FROM atm_card_stats", conn)
        conn.close()
        self.feature_cols = ["ATMs_On_Site", "ATMs_Off_Site", "PoS", "Micro_ATMs",
                              "Bharat_QR_Codes", "UPI_QR_Codes",
                              "Credit_Cards_Outstanding", "Debit_Cards_Outstanding"]
        self.target = target
        X = df[self.feature_cols].fillna(0)
        y = df[target].fillna(0)
        return X, y

    def train(self, target="DC_Vol_Cash_ATM"):
        X, y = self._get_data(target)
        self.model.fit(X, y)
        self.coefficients = dict(zip(self.feature_cols, self.model.coef_))
        self.metrics = {
            "R2": round(self.model.score(X, y), 4),
            "intercept": round(self.model.intercept_, 2),
        }
        self.is_trained = True
        self.save()
        return self.metrics

    def simulate(self, changes):
        if not self.is_trained and not self.load():
            return {"error": "Model not trained"}
        conn = sqlite3.connect(str(DB_PATH))
        baseline = pd.read_sql(
            "SELECT {} FROM atm_card_stats GROUP BY Bank_Name HAVING AVG({})".format(
                ", ".join(self.feature_cols), "1"
            ), conn
        )
        conn.close()
        baseline = pd.DataFrame([{c: 0 for c in self.feature_cols}])
        for col, delta in changes.items():
            if col in baseline.columns:
                baseline[col] = delta
        impact = self.model.predict(baseline.fillna(0))[0]
        return {
            "changes": changes,
            "predicted_impact_on": self.target,
            "estimated_change": round(float(impact), 2),
        }
