import pandas as pd
import numpy as np
import sqlite3
from sklearn.ensemble import IsolationForest
from sklearn.model_selection import GridSearchCV
from src.models.base_model import BaseModel
from src.utils import DB_PATH

class AnomalyDetector(BaseModel):
    def __init__(self):
        super().__init__("anomaly_detector")
        self.anomalies = None

    def _get_data(self):
        conn = sqlite3.connect(str(DB_PATH))
        df = pd.read_sql("SELECT Bank_Name, Reporting_Month, CC_Vol_PoS, CC_Vol_Online, "
                         "CC_Vol_Cash_ATM, DC_Vol_PoS, DC_Vol_Online, DC_Vol_Cash_ATM, "
                         "CC_Val_PoS, CC_Val_Online, DC_Val_PoS, DC_Val_Online, "
                         "DC_Vol_Cash_PoS, DC_Val_Cash_ATM, Total_Txn_Vol, Total_Txn_Val, "
                         "Digital_Share, Cash_Share FROM atm_card_stats", conn)
        conn.close()
        self.meta_cols = ["Bank_Name", "Reporting_Month"]
        self.feature_cols = [c for c in df.columns if c not in self.meta_cols]
        return df

    def train(self, contamination=0.05):
        df = self._get_data()
        X = df[self.feature_cols].fillna(0)
        param_grid = {"contamination": [0.01, 0.03, 0.05, 0.1], "n_estimators": [50, 100]}
        gs = GridSearchCV(IsolationForest(random_state=42), param_grid, cv=3,
                          scoring= lambda estimator, X: -np.mean(estimator.decision_function(X)), n_jobs=-1)
        gs.fit(X)
        self.model = gs.best_estimator_
        preds = self.model.predict(X)
        scores = self.model.decision_function(X)
        df["Is_Anomaly"] = preds == -1
        df["Anomaly_Score"] = -scores
        self.anomalies = df[df["Is_Anomaly"]].copy()
        self.metrics = {
            "total_anomalies": int(self.anomalies.shape[0]),
            "anomaly_rate": round(self.anomalies.shape[0] / len(df) * 100, 2),
            "samples_checked": len(df),
        }
        self.is_trained = True
        self.save()
        return self.anomalies

    def predict(self, data=None):
        if not self.is_trained and not self.load():
            return None
        return self.anomalies

    def get_flagged_banks(self, top_n=10):
        if self.anomalies is None or self.anomalies.empty:
            return []
        flagged = (self.anomalies.groupby("Bank_Name")
                   .agg({"Anomaly_Score": "mean", "Reporting_Month": "count"})
                   .rename(columns={"Reporting_Month": "Flagged_Months"})
                   .sort_values("Anomaly_Score", ascending=False)
                   .head(top_n))
        return flagged.reset_index().to_dict(orient="records")

    def get_monthly_anomalies(self):
        if self.anomalies is None or self.anomalies.empty:
            return []
        monthly = (self.anomalies.groupby("Reporting_Month")
                   .size().reset_index(name="Anomaly_Count"))
        return monthly.to_dict(orient="records")
