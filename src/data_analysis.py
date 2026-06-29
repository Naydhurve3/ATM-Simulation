import pandas as pd
import numpy as np
from src.utils import *
from src.data_ingestion import DataIngestion

class DataAnalysis:
    def __init__(self):
        self.di = DataIngestion()
        self.conn = self.di.get_connection()
        self._load_data()

    def _load_data(self):
        if not DB_PATH.exists():
            self.di.run_pipeline()
            self.conn = self.di.get_connection()
        self.df = pd.read_sql("SELECT * FROM atm_card_stats", self.conn)
        self.summary = pd.read_sql("SELECT * FROM bank_summary", self.conn)
        self.monthly = pd.read_sql("SELECT * FROM monthly_aggregate", self.conn)

    def get_banks(self):
        return sorted(self.df["Bank_Name"].unique())

    def get_months(self):
        return sorted(self.df["Reporting_Month"].unique(), key=lambda m: month_to_num(m))

    def bank_overview(self, bank_name):
        data = self.df[self.df["Bank_Name"] == bank_name].iloc[0]
        return {
            "Bank": bank_name,
            "Type": data["Bank_Type"],
            "ATMs On-Site": safe_int(data["ATMs_On_Site"]),
            "ATMs Off-Site": safe_int(data["ATMs_Off_Site"]),
            "Total ATMs": safe_int(data["Total_ATMs"]),
            "PoS Terminals": safe_int(data["PoS"]),
            "Micro ATMs": safe_int(data["Micro_ATMs"]),
            "Bharat QR": safe_int(data["Bharat_QR_Codes"]),
            "UPI QR": safe_int(data["UPI_QR_Codes"]),
            "Credit Cards": safe_int(data["Credit_Cards_Outstanding"]),
            "Debit Cards": safe_int(data["Debit_Cards_Outstanding"]),
            "Total Cards": safe_int(data["Total_Cards"]),
            "CC Txn Volume": safe_int(data["CC_Total_Vol"]),
            "CC Txn Value": safe_float(data["CC_Total_Val"]),
            "DC Txn Volume": safe_int(data["DC_Total_Vol"]),
            "DC Txn Value": safe_float(data["DC_Total_Val"]),
            "Total Txn Volume": safe_int(data["Total_Txn_Vol"]),
            "Total Txn Value": safe_float(data["Total_Txn_Val"]),
            "Digital Share (%)": round(safe_float(data["Digital_Share"]), 2),
            "Cash Share (%)": round(safe_float(data["Cash_Share"]), 2),
        }

    def compare_banks(self, banks):
        subset = self.df[self.df["Bank_Name"].isin(banks)]
        return subset.groupby("Bank_Name").agg({
            "Total_ATMs": "mean", "Total_Cards": "mean", "Total_Txn_Vol": "sum",
            "Total_Txn_Val": "sum", "Digital_Share": "mean", "Cash_Share": "mean",
            "ATMs_On_Site": "mean", "ATMs_Off_Site": "mean", "PoS": "mean",
            "Micro_ATMs": "mean", "Credit_Cards_Outstanding": "mean",
            "Debit_Cards_Outstanding": "mean"
        }).round(2).reset_index()

    def monthly_trend(self, bank_name=None, metric="Total_Txn_Vol"):
        if bank_name:
            subset = self.df[self.df["Bank_Name"] == bank_name]
        else:
            subset = self.df
        trend = subset.groupby(["Reporting_Month", "Month_Num"])[metric].sum().reset_index()
        trend = trend.sort_values("Month_Num")
        return trend

    def channel_breakdown(self, bank_name=None):
        if bank_name:
            data = self.df[self.df["Bank_Name"] == bank_name].iloc[0]
        else:
            data = self.df.sum()
        return {
            "CC PoS": {"Vol": safe_int(data["CC_Vol_PoS"]), "Val": safe_float(data["CC_Val_PoS"])},
            "CC Online": {"Vol": safe_int(data["CC_Vol_Online"]), "Val": safe_float(data["CC_Val_Online"])},
            "CC Cash ATM": {"Vol": safe_int(data["CC_Vol_Cash_ATM"]), "Val": safe_float(data["CC_Val_Cash_ATM"])},
            "DC PoS": {"Vol": safe_int(data["DC_Vol_PoS"]), "Val": safe_float(data["DC_Val_PoS"])},
            "DC Online": {"Vol": safe_int(data["DC_Vol_Online"]), "Val": safe_float(data["DC_Val_Online"])},
            "DC Cash ATM": {"Vol": safe_int(data["DC_Vol_Cash_ATM"]), "Val": safe_float(data["DC_Val_Cash_ATM"])},
        }

    def market_share(self, metric="Total_Txn_Vol"):
        total = self.df.groupby("Bank_Name")[metric].sum().reset_index()
        total["Share_%"] = (total[metric] / total[metric].sum() * 100).round(2)
        total = total.sort_values("Share_%", ascending=False)
        return total

    def growth_rate(self, bank_name=None, metric="Total_Txn_Vol"):
        if bank_name:
            data = self.df[self.df["Bank_Name"] == bank_name].copy()
        else:
            data = self.df.groupby(["Reporting_Month", "Month_Num"])[metric].sum().reset_index()
        data = data.sort_values("Month_Num")
        data["MoM_Growth_%"] = data[metric].pct_change() * 100
        return data

    def correlation_matrix(self):
        numeric = self.df.select_dtypes(include=[np.number])
        return numeric.corr()

    def top_banks(self, metric="Total_Txn_Vol", n=5):
        ranked = self.df.groupby("Bank_Name")[metric].sum().sort_values(ascending=False).head(n)
        return ranked

    def get_statistics(self, metric="Total_Txn_Vol"):
        values = self.df.groupby("Bank_Name")[metric].sum()
        return {
            "mean": values.mean(), "median": values.median(), "std": values.std(),
            "min": values.min(), "max": values.max(), "total": values.sum()
        }

    def user_vs_industry(self, user_data):
        bank = user_data.get("bank", "")
        bank_data = self.df[self.df["Bank_Name"] == bank]
        industry_avg = self.df.groupby("Bank_Name")[["Digital_Share", "Total_ATMs", "Total_Txn_Vol"]].mean().mean()
        if bank_data.empty:
            return {"error": "Bank not found in RBI data"}
        bank_avg = bank_data[["Digital_Share", "Total_ATMs"]].mean()
        result = {
            "bank": bank,
            "user_balance": user_data.get("balance", 0),
            "bank_digital_share": round(float(bank_avg.get("Digital_Share", 0)), 1),
            "industry_avg_digital": round(float(industry_avg.get("Digital_Share", 0)), 1),
            "digital_gap": round(float(bank_avg.get("Digital_Share", 0) - industry_avg.get("Digital_Share", 0)), 1),
        }
        result["above_industry"] = result["digital_gap"] > 0
        return result

    def bank_comparison_with_user(self, user_data, other_banks=None):
        user_bank = user_data.get("bank", "")
        banks_to_compare = [user_bank] + (other_banks or [])
        return self.compare_banks(banks_to_compare)

if __name__ == "__main__":
    from rich import print
    da = DataAnalysis()
    print(da.top_banks("Total_Txn_Vol"))
