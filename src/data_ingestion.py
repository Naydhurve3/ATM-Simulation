import pandas as pd
import numpy as np
from pathlib import Path
from src.utils import *
from src.data.db_manager import db

class DataIngestion:
    def __init__(self):
        self.df = None
        self.conn = None
        self.db_path = DB_PATH
        self.csv_path = DATA_RAW / "RBI_ATM_Card_Statistics.csv"

    def load_csv(self):
        if not self.csv_path.exists():
            files = list(DATA_RAW.glob("*.csv"))
            if files:
                self.csv_path = files[0]
            else:
                raise FileNotFoundError("No CSV found in data/raw/")
        self.df = pd.read_csv(self.csv_path)
        self.df = self.df.replace([np.inf, -np.inf], np.nan)
        self.df = self.df.fillna(0)
        return self.df

    def clean_data(self):
        df = self.df.copy()
        df["Bank_Name"] = df["Bank_Name"].str.strip().str.upper()
        df["Reporting_Month"] = df["Reporting_Month"].str.strip()
        numeric_cols = [c for c in df.columns if c not in ["Bank_Name", "Reporting_Month"]]
        for c in numeric_cols:
            df[c] = df[c].apply(safe_float)
        df["Month_Num"] = df["Reporting_Month"].apply(month_to_num)
        df["Bank_Type"] = df["Bank_Name"].apply(get_bank_type)
        df["Total_ATMs"] = df["ATMs_On_Site"] + df["ATMs_Off_Site"]
        df["Total_Cards"] = df["Credit_Cards_Outstanding"] + df["Debit_Cards_Outstanding"]
        df["CC_Total_Vol"] = df["CC_Vol_PoS"] + df["CC_Vol_Online"] + df["CC_Vol_Others"] + df["CC_Vol_Cash_ATM"]
        df["CC_Total_Val"] = df["CC_Val_PoS"] + df["CC_Val_Online"] + df["CC_Val_Others"] + df["CC_Val_Cash_ATM"]
        df["DC_Total_Vol"] = df["DC_Vol_PoS"] + df["DC_Vol_Online"] + df["DC_Vol_Others"] + df["DC_Vol_Cash_ATM"] + df["DC_Vol_Cash_PoS"]
        df["DC_Total_Val"] = df["DC_Val_PoS"] + df["DC_Val_Online"] + df["DC_Val_Others"] + df["DC_Val_Cash_ATM"] + df["DC_Val_Cash_PoS"]
        df["Total_Txn_Vol"] = df["CC_Total_Vol"] + df["DC_Total_Vol"]
        df["Total_Txn_Val"] = df["CC_Total_Val"] + df["DC_Total_Val"]
        df["Digital_QR_Codes"] = df["Bharat_QR_Codes"] + df["UPI_QR_Codes"]
        df["Digital_Vol"] = df["CC_Vol_Online"] + df["DC_Vol_Online"] + df["CC_Vol_PoS"] + df["DC_Vol_PoS"]
        df["Cash_Vol"] = df["CC_Vol_Cash_ATM"] + df["DC_Vol_Cash_ATM"] + df["DC_Vol_Cash_PoS"]
        df["Digital_Share"] = df.apply(
            lambda r: (r["Digital_Vol"] / r["Total_Txn_Vol"] * 100) if r["Total_Txn_Vol"] > 0 else 0, axis=1
        )
        df["Cash_Share"] = df.apply(
            lambda r: (r["Cash_Vol"] / r["Total_Txn_Vol"] * 100) if r["Total_Txn_Vol"] > 0 else 0, axis=1
        )
        self.df = df
        return df

    def save_to_sqlite(self):
        self.conn = db.get_connection("atm_data")
        self.df.to_sql("atm_card_stats", self.conn, if_exists="replace", index=False)
        summary = self.df.groupby("Bank_Name").agg({
            "Total_ATMs": "mean", "Total_Cards": "mean", "Total_Txn_Vol": "sum",
            "Total_Txn_Val": "sum", "Digital_Share": "mean"
        }).reset_index()
        summary.to_sql("bank_summary", self.conn, if_exists="replace", index=False)
        monthly = self.df.groupby(["Reporting_Month", "Month_Num"]).agg({
            "Total_ATMs": "sum", "Total_Cards": "sum", "Total_Txn_Vol": "sum",
            "Total_Txn_Val": "sum", "Digital_Share": "mean"
        }).reset_index().sort_values("Month_Num")
        monthly.to_sql("monthly_aggregate", self.conn, if_exists="replace", index=False)
        return True

    def get_connection(self):
        if self.conn is None:
            self.conn = db.get_connection("atm_data")
        return self.conn

    def run_pipeline(self):
        print("[bold yellow]Loading CSV data...[/bold yellow]")
        self.load_csv()
        print(f"[green]Loaded {len(self.df)} rows, {len(self.df.columns)} columns[/green]")
        print("[bold yellow]Cleaning and engineering features...[/bold yellow]")
        self.clean_data()
        print(f"[green]Data cleaned. Shape: {self.df.shape}[/green]")
        print("[bold yellow]Saving to SQLite database...[/bold yellow]")
        self.save_to_sqlite()
        print(f"[green]Database saved to {self.db_path}[/green]")
        return self.df

if __name__ == "__main__":
    from rich import print
    di = DataIngestion()
    di.run_pipeline()
