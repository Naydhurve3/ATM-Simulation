import pandas as pd
import numpy as np
import sqlite3
from statsmodels.tsa.seasonal import seasonal_decompose
from banking_core.models.base_model import BaseModel
from banking_core.utils import DB_PATH
from banking_core.data.postgres_adapter import get_industry_conn

class TrendAnalyzer(BaseModel):
    def __init__(self):
        super().__init__("trend_analyzer")

    def _connect(self):
        return get_industry_conn() or sqlite3.connect(str(DB_PATH))

    def decompose(self, bank_name=None, metric="Total_Txn_Vol"):
        conn = self._connect()
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
        df = df.groupby("Month_Num", as_index=False)[metric].sum()
        month_dates = pd.to_datetime(df["Month_Num"], format="%m", errors="coerce")
        ts = df.set_index(month_dates)[metric].sort_index()
        ts = ts.resample("ME").ffill().fillna(0)
        if len(ts) >= 4:
            result = seasonal_decompose(ts, model="additive", period=min(len(ts)//2, 3))
            return result
        return None

    def growth_rates(self, bank_name=None, metric="Total_Txn_Vol"):
        conn = self._connect()
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
        conn = self._connect()
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
