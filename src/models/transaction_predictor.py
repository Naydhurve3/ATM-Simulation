import pandas as pd
import numpy as np
import sqlite3
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from src.models.base_model import BaseModel
from src.utils import DB_PATH

class TransactionPredictor(BaseModel):
    def __init__(self):
        super().__init__("transaction_predictor")
        self.feature_cols = []
        self.target_col = ""

    def _get_data(self, target="DC_Vol_Cash_ATM"):
        conn = sqlite3.connect(str(DB_PATH))
        df = pd.read_sql("SELECT * FROM atm_card_stats", conn)
        conn.close()
        exclude = ["Bank_Name", "Reporting_Month", "Month_Num", "Bank_Type",
                   "CC_Total_Vol", "CC_Total_Val", "DC_Total_Vol", "DC_Total_Val",
                   "Total_Txn_Vol", "Total_Txn_Val", "Digital_Share", "Cash_Share",
                   "Total_ATMs", "Total_Cards", "Digital_Vol", "Cash_Vol",
                   "Digital_QR_Codes"]
        self.feature_cols = [c for c in df.select_dtypes(include=[np.number]).columns
                            if c not in exclude and c != target]
        self.feature_cols = self.feature_cols[:20]
        self.target_col = target
        X = df[self.feature_cols].fillna(0)
        y = df[target].fillna(0).astype(float)
        return X, y

    def train(self, target="DC_Vol_Cash_ATM"):
        X, y = self._get_data(target)
        if len(X) < 10:
            return {"error": "Not enough samples"}
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        param_grid = {"n_estimators": [100, 200], "max_depth": [4, 6, 8], "learning_rate": [0.05, 0.1]}
        gs = GridSearchCV(XGBRegressor(random_state=42, verbosity=0), param_grid, cv=3, scoring="neg_mean_squared_error", n_jobs=-1)
        gs.fit(X_train, y_train)
        self.model = gs.best_estimator_
        y_pred = self.model.predict(X_test)
        self.metrics = {
            "MAE": round(mean_absolute_error(y_test, y_pred), 2),
            "RMSE": round(np.sqrt(mean_squared_error(y_test, y_pred)), 2),
            "R2": round(r2_score(y_test, y_pred), 4),
        }
        self.is_trained = True
        self.save()
        return self.metrics

    def predict(self, features=None):
        if not self.is_trained and not self.load():
            return {"error": "Model not trained"}
        if features is not None:
            pred = self.model.predict(features)[0]
            return {"prediction": round(pred, 2)}
        return {"error": "Provide features"}

    def get_feature_importance(self):
        if not self.is_trained and not self.load():
            return {}
        importances = self.model.feature_importances_
        return dict(sorted(zip(self.feature_cols, importances),
                          key=lambda x: x[1], reverse=True)[:10])
