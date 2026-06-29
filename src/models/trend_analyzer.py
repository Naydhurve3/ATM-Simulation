import pandas as pd
import numpy as np
import sqlite3
from statsmodels.tsa.seasonal import seasonal_decompose
from src.models.base_model import BaseModel
from src.utils import DB_PATH

class TrendAnalyzer(BaseModel):
    def __init__(self):
        super().__init__("trend_analyzer")

    def decompose(self, bank_name=None, metric="Total_Txn_Vol"):
        conn = sqlite3.connect(str(DB_PATH))
        if bank_name:
            df = pd.read_sql(
                "SELECT Reporting_Month, Month_Num, {} FROM atm_card_stats WHERE Bank_Name=?".format(metric),
                conn, params=(bank_name,)
            )
        else:
            df = pd.read_sql(
                "SELECT Reporting_Month, Month_Num, SUM({}) as {} FROM atm_card_stats GROUP BY Reporting_Month, Month_Num ORDER BY Month_Num".format(metric, metric),
                conn
            )
        conn.close()
        if len(df) < 4:
            return None
        ts = df.set_index("Month_Num")[metric]
        ts = ts.asfreq("ME").fillna(method="ffill")
        if len(ts) >= 4:
            result = seasonal_decompose(ts, model="additive", period=min(len(ts)//2, 3))
            return result
        return None

    def growth_rates(self, bank_name=None, metric="Total_Txn_Vol"):
        conn = sqlite3.connect(str(DB_PATH))
        if bank_name:
            df = pd.read_sql(
                "SELECT Reporting_Month, Month_Num, {} FROM atm_card_stats WHERE Bank_Name=? ORDER BY Month_Num".format(metric),
                conn, params=(bank_name,)
            )
        else:
            df = pd.read_sql(
                "SELECT Reporting_Month, Month_Num, SUM({}) as {} FROM atm_card_stats GROUP BY Reporting_Month, Month_Num ORDER BY Month_Num".format(metric, metric),
                conn
            )
        conn.close()
        df["MoM_Growth"] = df[metric].pct_change() * 100
        df["QoQ_Growth"] = df[metric].pct_change(periods=3) * 100
        return df

    def moving_average(self, bank_name=None, metric="Total_Txn_Vol", window=3):
        conn = sqlite3.connect(str(DB_PATH))
        if bank_name:
            df = pd.read_sql(
                "SELECT Reporting_Month, Month_Num, {} FROM atm_card_stats WHERE Bank_Name=? ORDER BY Month_Num".format(metric),
                conn, params=(bank_name,)
            )
        else:
            df = pd.read_sql(
                "SELECT Reporting_Month, Month_Num, SUM({}) as {} FROM atm_card_stats GROUP BY Reporting_Month, Month_Num ORDER BY Month_Num".format(metric, metric),
                conn
            )
        conn.close()
        df[f"MA_{window}"] = df[metric].rolling(window=window).mean()
        return df
