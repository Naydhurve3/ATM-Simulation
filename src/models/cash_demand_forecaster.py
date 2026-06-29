import pandas as pd
import numpy as np
from prophet import Prophet
from prophet.diagnostics import performance_metrics
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from src.models.base_model import BaseModel
from src.utils import DB_PATH, MONTH_ORDER, month_to_num
import sqlite3

class CashDemandForecaster(BaseModel):
    def __init__(self):
        super().__init__("cash_demand_forecaster")
        self.month_map = {m: i+1 for i, m in enumerate(MONTH_ORDER)}

    def _get_data(self, bank_name=None, metric="DC_Vol_Cash_ATM"):
        conn = sqlite3.connect(str(DB_PATH))
        if bank_name:
            df = pd.read_sql("SELECT Reporting_Month, Month_Num, {} FROM atm_card_stats WHERE Bank_Name=?".format(metric),
                             conn, params=(bank_name,))
        else:
            df = pd.read_sql("SELECT Reporting_Month, Month_Num, SUM({}) as {} FROM atm_card_stats GROUP BY Reporting_Month, Month_Num ORDER BY Month_Num".format(metric, metric), conn)
        conn.close()
        df["ds"] = pd.to_datetime("2025-" + df["Month_Num"].astype(str) + "-01")
        df["y"] = df[metric].astype(float)
        return df[["ds", "y"]]

    def train(self, bank_name=None, metric="DC_Vol_Cash_ATM"):
        df = self._get_data(bank_name, metric)
        if len(df) < 3:
            return {"error": "Not enough data points"}
        self.model = Prophet(yearly_seasonality=False, weekly_seasonality=False,
                             daily_seasonality=False, seasonality_mode="multiplicative")
        self.model.add_seasonality(name="monthly", period=1, fourier_order=5)
        self.model.fit(df)
        self.is_trained = True
        future = self.model.make_future_dataframe(periods=1, freq="ME")
        forecast = self.model.predict(future)
        preds = forecast["yhat"].values[:-1]
        actuals = df["y"].values[-len(preds):]
        self.metrics = {
            "MAE": round(mean_absolute_error(actuals, preds), 2),
            "RMSE": round(np.sqrt(mean_squared_error(actuals, preds)), 2),
            "MAPE": round(np.mean(np.abs((actuals - preds) / (actuals + 1e-8))) * 100, 2),
        }
        self.save()
        return self.metrics

    def predict(self, bank_name=None, metric="DC_Vol_Cash_ATM"):
        if not self.is_trained and not self.load():
            return {"error": "Model not trained. Train first."}
        df = self._get_data(bank_name, metric)
        future = self.model.make_future_dataframe(periods=1, freq="ME")
        forecast = self.model.predict(future)
        last = forecast.iloc[-1]
        return {
            "predicted_value": round(last["yhat"], 2),
            "lower_bound": round(last["yhat_lower"], 2),
            "upper_bound": round(last["yhat_upper"]),
            "next_month": "Next Month",
        }

    def backtest(self, bank_name=None, metric="DC_Vol_Cash_ATM", expand_by=1):
        df = self._get_data(bank_name, metric)
        if len(df) < 4:
            return {"error": "Need at least 4 data points for backtest"}
        results = []
        for i in range(expand_by, len(df)):
            train_df = df.iloc[:i]
            test_df = df.iloc[i:i+1]
            if len(train_df) < 2:
                continue
            m = Prophet(yearly_seasonality=False, weekly_seasonality=False,
                        daily_seasonality=False, seasonality_mode="multiplicative")
            m.add_seasonality(name="monthly", period=1, fourier_order=5)
            m.fit(train_df)
            future = m.make_future_dataframe(periods=1, freq="ME")
            forecast = m.predict(future)
            pred = forecast["yhat"].iloc[-1]
            actual = test_df["y"].values[0]
            results.append({"actual": float(actual), "predicted": float(pred),
                            "train_months": i, "test_month": i})
        if not results:
            return {"error": "Not enough data for any backtest window"}
        actuals = [r["actual"] for r in results]
        preds = [r["predicted"] for r in results]
        mae = np.mean(np.abs(np.array(actuals) - np.array(preds)))
        rmse = np.sqrt(np.mean((np.array(actuals) - np.array(preds))**2))
        mape = np.mean(np.abs((np.array(actuals) - np.array(preds)) / (np.array(actuals) + 1e-8))) * 100
        return {"results": results, "avg_MAE": round(mae, 2), "avg_RMSE": round(rmse, 2),
                "avg_MAPE": round(mape, 2), "windows": len(results)}

    def get_components(self, bank_name=None, metric="DC_Vol_Cash_ATM"):
        if not self.is_trained and not self.load():
            return None
        df = self._get_data(bank_name, metric)
        future = self.model.make_future_dataframe(periods=1, freq="ME")
        forecast = self.model.predict(future)
        return forecast[["ds", "trend", "seasonal", "yhat_lower", "yhat_upper", "yhat"]]
