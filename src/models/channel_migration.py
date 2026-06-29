import pandas as pd
import numpy as np
import sqlite3
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.preprocessing import StandardScaler
from src.models.base_model import BaseModel
from src.utils import DB_PATH

class ChannelMigrationPredictor(BaseModel):
    def __init__(self):
        super().__init__("channel_migration")
        self.scaler = StandardScaler()

    def _get_channel_data(self, bank_name=None):
        conn = sqlite3.connect(str(DB_PATH))
        if bank_name:
            df = pd.read_sql(
                "SELECT Reporting_Month, Month_Num, CC_Vol_Online, DC_Vol_Online, "
                "CC_Vol_PoS, DC_Vol_PoS, DC_Vol_Cash_ATM, CC_Vol_Cash_ATM, "
                "DC_Vol_Cash_PoS, Total_Txn_Vol FROM atm_card_stats WHERE Bank_Name=? "
                "ORDER BY Month_Num",
                conn, params=(bank_name,)
            )
        else:
            df = pd.read_sql(
                "SELECT Reporting_Month, Month_Num, "
                "SUM(CC_Vol_Online) as CC_Vol_Online, SUM(DC_Vol_Online) as DC_Vol_Online, "
                "SUM(CC_Vol_PoS) as CC_Vol_PoS, SUM(DC_Vol_PoS) as DC_Vol_PoS, "
                "SUM(DC_Vol_Cash_ATM) as DC_Vol_Cash_ATM, SUM(CC_Vol_Cash_ATM) as CC_Vol_Cash_ATM, "
                "SUM(DC_Vol_Cash_PoS) as DC_Vol_Cash_PoS, SUM(Total_Txn_Vol) as Total_Txn_Vol "
                "FROM atm_card_stats GROUP BY Reporting_Month, Month_Num ORDER BY Month_Num",
                conn
            )
        conn.close()
        df["Digital_Vol"] = df["CC_Vol_Online"] + df["DC_Vol_Online"] + df["CC_Vol_PoS"] + df["DC_Vol_PoS"]
        df["Cash_Vol"] = df["DC_Vol_Cash_ATM"] + df["CC_Vol_Cash_ATM"] + df["DC_Vol_Cash_PoS"]
        df["Digital_Share"] = df.apply(
            lambda r: (r["Digital_Vol"] / r["Total_Txn_Vol"] * 100) if r["Total_Txn_Vol"] > 0 else 0, axis=1
        )
        df["Cash_Share"] = df.apply(
            lambda r: (r["Cash_Vol"] / r["Total_Txn_Vol"] * 100) if r["Total_Txn_Vol"] > 0 else 0, axis=1
        )
        df["Month_Index"] = range(len(df))
        return df

    def train(self, bank_name=None):
        df = self._get_channel_data(bank_name)
        if len(df) < 4:
            return {"error": "Not enough data"}
        X = df[["Month_Index"]].values
        y_digital = df["Digital_Share"].values / 100.0
        y_digital = np.clip(y_digital, 0.001, 0.999)
        self.model = LogisticRegression(C=1.0, solver="lbfgs", max_iter=1000)
        self.model.fit(X, y_digital > np.median(y_digital))
        self.lin_reg = LinearRegression()
        self.lin_reg.fit(X, y_digital)
        self.metrics = {
            "samples": len(df),
            "coef": round(float(self.lin_reg.coef_[0]), 6),
            "intercept": round(float(self.lin_reg.intercept_), 4),
        }
        self.is_trained = True
        self.save()
        return self.metrics

    def predict(self, bank_name=None, months_ahead=3):
        if not self.is_trained and not self.load():
            return {"error": "Model not trained"}
        last_idx = 0
        if bank_name:
            df = self._get_channel_data(bank_name)
            last_idx = len(df) - 1
        future_idx = last_idx + months_ahead
        current_pred = self.lin_reg.predict([[last_idx]])[0]
        future_pred = self.lin_reg.predict([[future_idx]])[0]
        return {
            "current_digital_share": round(float(current_pred) * 100, 2),
            "predicted_digital_share": round(float(future_pred) * 100, 2),
            "shift_pct": round(float((future_pred - current_pred) * 100), 2),
            "months_ahead": months_ahead,
        }
