import sys
import time
import pandas as pd
import numpy as np
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt, Confirm
from rich.layout import Layout
from rich import box
from rich.text import Text
from rich.columns import Columns
from rich.markdown import Markdown
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

from src.utils import *
from src.data_ingestion import DataIngestion
from src.data_analysis import DataAnalysis
from src.data_visualization import DataVisualization
from src.atm_simulator import ATMSimulator
from src.user_manager import UserManager
from src.user_analytics import UserAnalytics
from src.demo_manager import DemoManager
from src.ui_helpers import BankSelector

from src.models import (
    CashDemandForecaster, TransactionPredictor, BankClustering,
    AnomalyDetector, TrendAnalyzer, ChannelMigrationPredictor, WhatIfSimulator,
    CreditScorer, ChurnPredictor, LoanDefaultModel, BankRecommender, SpendingForecaster
)

from src.report_generator import ReportGenerator

from src.data.db_manager import db
from src.auto_retrain import AutoRetrainScheduler
from src.models.lstm_forecaster import LSTMForecaster
from src.models.real_time_fraud_detector import RealTimeFraudDetector
from src.models.investment_recommender import InvestmentRecommender
from src.models.atm_replenishment import ATMReplenishmentOptimizer
from src.models.rfm_segmenter import RFMSegmenter
from src.models.savings_optimizer import SavingsGoalOptimizer
from src.models.sentiment_analyzer import SentimentAnalyzer
from src.models.model_monitor import ModelMonitor
import plotext as pltxt
import os
import webbrowser

console = Console()

class BankingAnalyticsSuite:
    def __init__(self):
        self.da = None
        self.viz = None
        self.reporter = None
        self.um = UserManager()
        self.user = None
        self.initialized = False
        self.monitor = ModelMonitor()
        self.scheduler = AutoRetrainScheduler()
        self.fraud_detector = RealTimeFraudDetector()

    def initialize(self):
        with console.status("[bold yellow]Initializing data pipeline...", spinner="dots"):
            try:
                self.da = DataAnalysis()
                self.viz = DataVisualization(self.da)
                self.reporter = ReportGenerator(self.da)
                self.initialized = True
                return True
            except Exception as e:
                console.print(f"[red]Error initializing: {e}[/red]")
                return False

    def show_banner(self):
        banner = """
\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90
\xe2\x95\x91     ATM & Banking Ecosystem v3.0                 \xe2\x95\x91
\xe2\x95\x91     Powered by Real RBI Data + User Analytics    \xe2\x95\x91
\xe2\x95\x9a\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x90\xe2\x95\x9d
        """
        console.print(Panel.fit(banner, border_style="yellow"))

    def login_gate(self):
        self.show_banner()
        console.print("[bold cyan]Welcome! Please login or create an account to continue.[/bold cyan]")
        self.user = self.um.login_or_register()
        if not self.user:
            console.print("[red]Exiting. Thank you![/red]")
            return False
        return True

    def _get_selector(self):
        return BankSelector(self.da.get_banks())

    def main_menu(self):
        while True:
            retrain_result = self.scheduler.retrain_if_needed(self.um, {})
            if retrain_result.get("retrained"):
                console.print(f"[green]Auto-retrained: {', '.join(retrain_result['models_retrained'])}[/green]")
            console.clear()
            self.show_banner()
            console.print(f"[bold green][Profile] {self.user['name']}[/bold green] | [cyan]{self.user['account_no']}[/cyan] | [yellow]\xe2\x82\xb9{self.user['balance']:,.0f}[/yellow] | * {self.user['credit_score']}")
            table = Table(box=box.ROUNDED, show_header=False)
            table.add_column("Option", style="cyan", width=8)
            table.add_column("Feature", style="white")
            table.add_row("1", "[ATM]  ATM Simulator (Your Account)")
            table.add_row("2", "[Data]  Data Analysis & Insights")
            table.add_row("3", "[ML]  ML/DL Predictions & Modeling")
            table.add_row("4", "[Profile]  My Profile & Portfolio")
            table.add_row("5", "[Banks]  Bank Explorer & Compare")
            table.add_row("6", "[Web]  Web Dashboard")
            table.add_row("7", "[Reports]  Reports, Exports & Training Data")
            table.add_row("8", "[Demo]  Demo / Tour")
            table.add_row("9", "[Retrain]  Model Freshness & Auto-Retrain")
            table.add_row("10", "[Settings]  Settings & Data Management")
            table.add_row("11", "[Exit]  Logout / Exit")
            console.print(table)
            choice = Prompt.ask("[yellow]Select option[/yellow]", choices=["1","2","3","4","5","6","7","8","9","10","11"])
            if choice == "1":
                self.atm_simulator_menu()
            elif choice == "2":
                self.data_analysis_menu()
            elif choice == "3":
                self.ml_menu()
            elif choice == "4":
                self.profile_menu()
            elif choice == "5":
                self.bank_explorer_menu()
            elif choice == "6":
                self._launch_dashboard()
            elif choice == "7":
                self.reports_menu()
            elif choice == "8":
                self.demo_menu()
            elif choice == "9":
                self._model_freshness()
            elif choice == "10":
                self.settings_menu()
            elif choice == "11":
                self.um.end_session(self.user["user_id"])
                console.print(f"[green]Goodbye, {self.user['name']}![/green]")
                break

    def _launch_dashboard(self):
        from src.dashboard.app import run_dashboard
        import threading
        console.print("[yellow]Launching Web Dashboard in browser...[/yellow]")
        t = threading.Thread(target=run_dashboard, kwargs={
            "data_analysis": self.da,
            "data_visualization": self.viz,
            "user_manager": self.um,
            "user_data": self.user,
        }, daemon=True)
        t.start()
        Prompt.ask("[yellow]Dashboard running at http://127.0.0.1:5000 . Press Enter to return[/yellow]", default="")

    def _model_freshness(self):
        console.clear()
        console.print("[bold yellow]Model Freshness & Health Report[/bold yellow]")
        freshness_table = self.scheduler.get_freshness_report(self.monitor)
        if freshness_table:
            console.print(freshness_table)
        statuses = self.monitor.get_all_model_status()
        if statuses:
            detail_table = Table(title="Model Metrics Summary", box=box.ROUNDED)
            detail_table.add_column("Model", style="cyan")
            detail_table.add_column("Version", style="white")
            detail_table.add_column("Metrics", style="green")
            detail_table.add_column("Last Trained", style="yellow")
            for name, info in statuses.items():
                metrics_str = ", ".join(f"{k}={v:.4f}" if isinstance(v, float) else f"{k}={v}" for k, v in info["metrics_summary"].items())
                detail_table.add_row(name, str(info["version"]), metrics_str[:60], info["last_trained"][:10] if info["last_trained"] else "N/A")
            console.print(detail_table)
        else:
            console.print("[yellow]No model metrics logged yet.[/yellow]")
        if Confirm.ask("[yellow]Run scheduled retrain now?[/yellow]", default=False):
            result = self.scheduler.retrain_if_needed(self.um, {})
            if result.get("retrained"):
                console.print(f"[green]Retrained: {', '.join(result['models_retrained'])}[/green]")
            else:
                console.print("[green]No retrain needed.[/green]")
        Prompt.ask("[yellow]Press Enter to return[/yellow]", default="")

    def atm_simulator_menu(self):
        self.user = self.um.get_user(self.user["user_id"])
        if not self.user:
            console.print("[red]User not found[/red]")
            return
        console.clear()
        console.print("[dim]Watch Demo first? Press D for demo, or any key to start ATM[/dim]")
        demo_choice = Prompt.ask("[yellow]Start ATM or Demo?[/yellow]", choices=["d", "s", ""], default="s")
        if demo_choice.lower() == "d":
            dm = DemoManager(self.user)
            dm.run_atm_demo()
            if not Confirm.ask("[yellow]Start ATM now?[/yellow]", default=True):
                return
        atm = ATMSimulator(self.user, self.um)
        atm.run()

    def data_analysis_menu(self):
        if not self.initialized:
            return
        while True:
            console.clear()
            table = Table(box=box.ROUNDED, show_header=False)
            table.add_column("Option", style="cyan", width=8)
            table.add_column("Feature", style="white")
            table.add_row("1", "Bank Overview & KPIs")
            table.add_row("2", "Compare Banks Side-by-Side")
            table.add_row("3", "Monthly Trend Analysis")
            table.add_row("4", "Market Share Analysis")
            table.add_row("5", "Channel-wise Transaction Breakdown")
            table.add_row("6", "Correlation Heatmap")
            table.add_row("7", "Growth Rate (MoM)")
            table.add_row("8", "My Personal Analytics")
            table.add_row("9", "[Demo]  Demo Walkthrough")
            table.add_row("10", "Back to Main Menu")
            console.print(table)
            choice = Prompt.ask("[yellow]Select option[/yellow]",
                                choices=[str(i) for i in range(1, 11)])
            if choice == "1":
                self._bank_overview()
            elif choice == "2":
                self._compare_banks()
            elif choice == "3":
                self._monthly_trend()
            elif choice == "4":
                self._market_share()
            elif choice == "5":
                self._channel_breakdown()
            elif choice == "6":
                self._correlation()
            elif choice == "7":
                self._growth_rate()
            elif choice == "8":
                self._personal_analytics()
            elif choice == "9":
                dm = DemoManager(self.user)
                dm.show_feature_menu("analysis")
            elif choice == "10":
                break

    def ml_menu(self):
        if not self.initialized:
            return
        while True:
            console.clear()
            table = Table(box=box.ROUNDED, show_header=False)
            table.add_column("Option", style="cyan", width=8)
            table.add_column("Feature", style="white")
            table.add_row("1",  "[Forecast]  Cash Demand Forecast (Prophet)")
            table.add_row("2",  "[XGB]  Transaction Volume Prediction (XGBoost)")
            table.add_row("3",  "[KMeans]  Bank Clustering (K-Means + PCA)")
            table.add_row("4",  "[Fraud]  Anomaly / Fraud Detection")
            table.add_row("5",  "[Trend]  Trend Decomposition")
            table.add_row("6",  "[Channel]  Channel Migration Prediction")
            table.add_row("7",  "[WhatIf]  What-If Scenario Simulator")
            table.add_row("8",  "[Credit]  Credit Score Prediction")
            table.add_row("9",  "[Data]  Churn Risk Analysis")
            table.add_row("10", "[Loan]  Loan Default Risk Assessment")
            table.add_row("11", "[Recommend]  Bank Recommendation")
            table.add_row("12", "[ML]  Retrain All Models & Compare")
            table.add_row("13", "[Replenish]  Replenishment Optimizer")
            table.add_row("14", "[LSTM]  LSTM vs Prophet Comparison")
            table.add_row("15", "[Demo]  Demo Walkthrough")
            table.add_row("16", "Back to Main Menu")
            console.print(table)
            choice = Prompt.ask("[yellow]Select option[/yellow]",
                                choices=[str(i) for i in range(1, 17)])
            if choice == "1":
                self._cash_demand_forecast()
            elif choice == "2":
                self._transaction_predict()
            elif choice == "3":
                self._bank_clustering()
            elif choice == "4":
                self._anomaly_detection()
            elif choice == "5":
                self._trend_decompose()
            elif choice == "6":
                self._channel_migration()
            elif choice == "7":
                self._what_if()
            elif choice == "8":
                self._credit_score_prediction()
            elif choice == "9":
                self._churn_analysis()
            elif choice == "10":
                self._loan_default_risk()
            elif choice == "11":
                self._bank_recommendation()
            elif choice == "12":
                self._retrain_all()
            elif choice == "13":
                self._atm_replenishment()
            elif choice == "14":
                self._lstm_comparison()
            elif choice == "15":
                dm = DemoManager(self.user)
                dm.show_feature_menu("ml")
            elif choice == "16":
                break

    def profile_menu(self):
        if not self.user:
            return
        ua = UserAnalytics(self.user)
        while True:
            console.clear()
            table = Table(box=box.ROUNDED, show_header=False)
            table.add_column("Option", style="cyan", width=8)
            table.add_column("Feature", style="white")
            table.add_row("1", "Account Dashboard")
            table.add_row("2", "Spending Analysis")
            table.add_row("3", "Credit Score Breakdown")
            table.add_row("4", "Transaction History")
            table.add_row("5", "Loan Offers [Loans]")
            table.add_row("6", "Savings Goals [Goals]")
            table.add_row("7", "Investment Suggestions")
            table.add_row("8", "RFM Analysis")
            table.add_row("9", "Savings Goal Optimizer")
            table.add_row("10", "[Passbook] Download Passbook")
            table.add_row("11", "Edit Profile")
            table.add_row("12", "Back to Main Menu")
            console.print(table)
            choice = Prompt.ask("[yellow]Select option[/yellow]",
                                choices=[str(i) for i in range(1, 13)])
            if choice == "1":
                ua.show_dashboard()
            elif choice == "2":
                ua.show_spending_analysis()
            elif choice == "3":
                ua.show_credit_score_breakdown()
            elif choice == "4":
                ua.show_transaction_history()
            elif choice == "5":
                atm = ATMSimulator(self.user, self.um)
                atm.loan_offers_menu()
            elif choice == "6":
                ua.show_savings_goals()
                if Confirm.ask("[yellow]Create a new savings goal?[/yellow]", default=False):
                    ua.create_savings_goal()
            elif choice == "7":
                self._investment_suggestions()
            elif choice == "8":
                self._rfm_analysis()
            elif choice == "9":
                self._savings_goal_optimizer()
            elif choice == "10":
                self._download_passbook()
            elif choice == "11":
                self._edit_profile()
            elif choice == "12":
                break
        ua.close()

    def bank_explorer_menu(self):
        if not self.initialized:
            return
        selector = self._get_selector()
        users_bank = self.user["bank"]
        while True:
            console.clear()
            console.print(Panel(f"[bold yellow]Bank Explorer -- Your bank: {users_bank}[/bold yellow]", border_style="yellow"))
            table = Table(box=box.ROUNDED, show_header=False)
            table.add_column("Option", style="cyan", width=8)
            table.add_column("Feature", style="white")
            table.add_row("1", "Browse All 65 Banks (with filters)")
            table.add_row("2", "Compare Banks Side-by-Side")
            table.add_row("3", "Bank Attributes Table (Rates & Fees)")
            table.add_row("4", "Best Bank For Me (Recommendation)")
            table.add_row("5", "Random Bank / Surprise Me")
            table.add_row("6", "Your Bank vs Industry")
            table.add_row("7", "Back to Main Menu")
            console.print(table)
            choice = Prompt.ask("[yellow]Select option[/yellow]",
                                choices=[str(i) for i in range(1, 8)])
            if choice == "1":
                selector.paginated_browse(title="Browse All Banks")
            elif choice == "2":
                groups = selector.quick_select_compare()
                if groups:
                    self._compare_banks(groups)
            elif choice == "3":
                self._show_bank_attributes(selector)
            elif choice == "4":
                self._recommend_bank()
            elif choice == "5":
                self._random_bank(selector)
            elif choice == "6":
                self._user_vs_industry()
            elif choice == "7":
                break

    def demo_menu(self):
        console.clear()
        console.print(Panel("[bold cyan]DEMO MODE -- What would you like to explore?[/bold cyan]", border_style="cyan"))
        table = Table(box=box.ROUNDED, show_header=False)
        table.add_column("Option", style="cyan", width=8)
        table.add_column("Feature", style="white")
        table.add_row("1", "Data Analysis Walkthrough")
        table.add_row("2", "ML Models Explained")
        table.add_row("3", "ATM Simulator Demo")
        table.add_row("4", "Profile & Portfolio Tour")
        table.add_row("5", "Bank Explorer Guide")
        table.add_row("6", "Back to Main Menu")
        console.print(table)
        choice = Prompt.ask("[yellow]Select demo[/yellow]",
                            choices=[str(i) for i in range(1, 7)])
        dm = DemoManager(self.user)
        if choice == "1":
            dm.run_analysis_demo()
        elif choice == "2":
            dm.run_ml_demo()
        elif choice == "3":
            dm.run_atm_demo()
        elif choice == "4":
            dm.run_profile_demo()
        elif choice == "5":
            dm.run_explorer_demo()

    def settings_menu(self):
        while True:
            console.clear()
            table = Table(box=box.ROUNDED, show_header=False)
            table.add_column("Option", style="cyan", width=8)
            table.add_column("Feature", style="white")
            table.add_row("1", "Refresh RBI Data (from CSV)")
            table.add_row("2", "View Database Statistics")
            table.add_row("3", "Reset ATM Daily Usage")
            table.add_row("4", "Export ML Training Datasets")
            table.add_row("5", "View Training Data Info")
            table.add_row("6", "Feedback Sentiment Analysis")
            table.add_row("7", "Back to Main Menu")
            console.print(table)
            choice = Prompt.ask("[yellow]Select option[/yellow]",
                                choices=[str(i) for i in range(1, 8)])
            if choice == "1":
                self.refresh_data()
            elif choice == "2":
                self.reporter.show_summary_table()
            elif choice == "3":
                self.um.reset_atm_usage()
                console.print("[green]ATM daily usage reset![/green]")
            elif choice == "4":
                self.reporter.export_training_data()
            elif choice == "5":
                self.reporter.show_dataset_info()
            elif choice == "6":
                self._feedback_sentiment()
            elif choice == "7":
                break

    def _bank_overview(self):
        selector = self._get_selector()
        bank = selector.select("Enter bank name for overview")
        if not bank:
            return
        try:
            overview = self.da.bank_overview(bank)
            table = Table(title=f"Bank Overview: {bank}", box=box.ROUNDED)
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")
            for k, v in overview.items():
                if isinstance(v, float):
                    table.add_row(k, f"{v:,.2f}" if v > 100 else str(v))
                else:
                    table.add_row(k, str(v))
            console.print(table)
            path = self.viz.plot_monthly_trend("Total_Txn_Vol", bank, f"Transaction Trend \xe2\x80\x94 {bank}")
            console.print(f"[dim]Chart saved to outputs/charts/[/dim]")
            if path:
                self.viz.open_chart(path)
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

    def _compare_banks(self, pre_selected=None):
        if pre_selected:
            banks = pre_selected
        else:
            selector = self._get_selector()
            banks = selector.select_multiple("Select banks to compare", max_count=5)
        if not banks:
            return
        banks = [b.strip().upper() for b in banks]
        valid = [b for b in banks if b in self.da.get_banks()]
        if not valid:
            console.print("[red]No valid banks found.[/red]")
            return
        comp = self.da.compare_banks(valid)
        table = Table(title="Bank Comparison", box=box.ROUNDED)
        for col in comp.columns:
            table.add_column(col, style="cyan" if col == "Bank_Name" else "green")
        for _, row in comp.iterrows():
            table.add_row(*[str(round(v, 2)) if isinstance(v, float) else str(v) for v in row])
        console.print(table)
        path1 = self.viz.plot_bank_comparison(valid, ["Total_Txn_Vol", "Total_ATMs", "Digital_Share"])
        path2 = self.viz.plot_radar_comparison(valid, ["Total_Txn_Vol", "Total_ATMs", "Digital_Share", "Total_Cards"])
        if path1:
            self.viz.open_chart(path1)
        if path2:
            self.viz.open_chart(path2)

    def _monthly_trend(self):
        metrics = ["Total_Txn_Vol", "Total_Txn_Val", "Digital_Share", "Total_ATMs", "Total_Cards"]
        metric_table = Table(box=box.ROUNDED)
        metric_table.add_column("#", style="cyan")
        metric_table.add_column("Metric")
        for i, m in enumerate(metrics, 1):
            metric_table.add_row(str(i), m)
        console.print(metric_table)
        choice = Prompt.ask("[yellow]Select metric number[/yellow]",
                            choices=[str(i) for i in range(1, len(metrics)+1)])
        metric = metrics[int(choice)-1]
        selector = self._get_selector()
        bank_name = selector.select("Bank name (or All)", allow_all=True)
        trend = self.da.monthly_trend(bank_name, metric)
        table = Table(title=f"Monthly Trend: {metric}", box=box.ROUNDED)
        table.add_column("Month", style="cyan")
        table.add_column(metric, style="green")
        for _, row in trend.iterrows():
            val = f"{row[metric]:,.2f}" if row[metric] > 1000 else str(round(row[metric], 2))
            table.add_row(row["Reporting_Month"], val)
        console.print(table)
        self.viz.plot_monthly_trend(metric, bank_name)

    def _market_share(self):
        metrics = ["Total_Txn_Vol", "Total_Txn_Val", "Total_ATMs", "Digital_Share",
                   "Credit_Cards_Outstanding", "Debit_Cards_Outstanding"]
        metric_table = Table(box=box.ROUNDED)
        metric_table.add_column("#", style="cyan")
        metric_table.add_column("Metric")
        for i, m in enumerate(metrics, 1):
            metric_table.add_row(str(i), m)
        console.print(metric_table)
        choice = Prompt.ask("[yellow]Select metric number[/yellow]",
                            choices=[str(i) for i in range(1, len(metrics)+1)])
        metric = metrics[int(choice)-1]
        ms = self.da.market_share(metric).head(15)
        table = Table(title=f"Market Share by {metric} (Top 15)", box=box.ROUNDED)
        table.add_column("Bank", style="cyan")
        table.add_column("Value", style="green")
        table.add_column("Share %", style="yellow")
        for _, row in ms.iterrows():
            table.add_row(row["Bank_Name"], f"{row[metric]:,.0f}", f"{row['Share_%']:.2f}%")
        console.print(table)
        path = self.viz.plot_market_share(metric)
        if path:
            self.viz.open_chart(path)

    def _channel_breakdown(self):
        selector = self._get_selector()
        bank = selector.select("Bank name (or All)", allow_all=True)
        ch = self.da.channel_breakdown(bank)
        table = Table(title=f"Channel Breakdown {f'\xe2\x80\x94 {bank}' if bank else '\xe2\x80\x94 All Banks'}", box=box.ROUNDED)
        table.add_column("Channel", style="cyan")
        table.add_column("Volume", style="green")
        table.add_column("Value", style="yellow")
        for channel, data in ch.items():
            table.add_row(channel, format_number(data["Vol"]), format_currency(data["Val"]))
        console.print(table)
        path = self.viz.plot_channel_pie(bank)
        if path:
            self.viz.open_chart(path)

    def _correlation(self):
        console.print("[yellow]Generating correlation heatmap...[/yellow]")
        path = self.viz.plot_correlation_heatmap()
        corr = self.da.correlation_matrix()
        top_cols = ["Total_ATMs", "Total_Cards", "CC_Total_Vol", "CC_Total_Val",
                     "DC_Total_Vol", "DC_Total_Val", "Digital_Share", "Cash_Share"]
        existent = [c for c in top_cols if c in corr.columns]
        sub = corr.loc[existent, existent]
        table = Table(title="Correlation Matrix (Key Metrics)", box=box.ROUNDED)
        table.add_column("", style="cyan")
        for c in existent:
            table.add_column(c[:12], style="dim")
        for r in existent:
            row_vals = [f"{sub.loc[r, c]:.2f}" for c in existent]
            table.add_row(r[:12], *row_vals)
        console.print(table)
        if path:
            console.print(f"[green]Heatmap saved: {path}[/green]")
            self.viz.open_chart(path)

    def _growth_rate(self):
        metric = Prompt.ask("[yellow]Metric[/yellow]", default="Total_Txn_Vol")
        selector = self._get_selector()
        bank = selector.select("Bank name (or All)", allow_all=True)
        gr = self.da.growth_rate(bank, metric)
        table = Table(title=f"Growth Rate {metric}", box=box.ROUNDED)
        table.add_column("Month", style="cyan")
        table.add_column(metric, style="green")
        table.add_column("MoM Growth %", style="yellow")
        for _, row in gr.iterrows():
            g = f"{row['MoM_Growth_%']:.2f}%" if pd.notna(row.get('MoM_Growth_%')) else "N/A"
            val = f"{row[metric]:,.2f}" if row[metric] > 1000 else str(round(row[metric], 2))
            table.add_row(row["Reporting_Month"], val, g)
        console.print(table)

    def _personal_analytics(self):
        ua = UserAnalytics(self.user)
        ua.show_dashboard()
        ua.show_spending_analysis()
        ua.show_transaction_history()
        sf = SpendingForecaster()
        pred = sf.predict(user_id=self.user["user_id"])
        if pred:
            pred_table = Table(title="Spending Forecast", box=box.ROUNDED)
            pred_table.add_column("Metric", style="cyan")
            pred_table.add_column("Value", style="green")
            pred_table.add_row("Predicted Monthly Spend", f"\xe2\x82\xb9{pred.get('predicted_monthly_spend', 0):,}")
            pred_table.add_row("Predicted Monthly Deposit", f"\xe2\x82\xb9{pred.get('predicted_monthly_deposit', 0):,}")
            pred_table.add_row("Avg Transaction", f"\xe2\x82\xb9{pred.get('avg_transaction', 0):,}")
            pred_table.add_row("Confidence", pred.get("confidence", "N/A"))
            pred_table.add_row("Trend", pred.get("trend", "N/A"))
            console.print(pred_table)
        path = self.viz.plot_monthly_spending_trend(
            months=["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
            spent=[pred.get("predicted_monthly_spend", 15000) * (0.9 + 0.1*i) for i in range(6)],
            deposited=[pred.get("predicted_monthly_deposit", 20000) * (1.0 + 0.05*i) for i in range(6)]
        )
        if path:
            self.viz.open_chart(path)
        ua.close()
        Prompt.ask("[yellow]Press Enter to continue[/yellow]", default="")

    def _cash_demand_forecast(self):
        forecaster = CashDemandForecaster()
        selector = self._get_selector()
        bank = selector.select("Bank name (or All)", allow_all=True)
        metric = Prompt.ask("[yellow]Metric[/yellow]", default="DC_Vol_Cash_ATM")
        with console.status("[bold yellow]Loading pre-trained model...", spinner="dots"):
            preloaded = forecaster.load()
        if preloaded and Confirm.ask("[yellow]Use pre-trained model?[/yellow]", default=True):
            forecaster.is_trained = True
        else:
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
                         BarColumn(), console=console) as progress:
                task = progress.add_task("[yellow]Training Prophet model...", total=100)
                result = forecaster.train(bank, metric)
                progress.update(task, completed=100)
        result = forecaster.predict(bank, metric)
        if "error" in result:
            console.print(f"[red]{result['error']}[/red]")
            return
        if preloaded and not forecaster.is_trained:
            result_new = CashDemandForecaster()
            result_new.train(bank, metric)
            pred_new = result_new.predict(bank, metric)
            comp_table = Table(title="Model Comparison", box=box.ROUNDED)
            comp_table.add_column("Metric", style="cyan")
            comp_table.add_column("Pre-trained", style="green")
            comp_table.add_column("Retrained", style="yellow")
            comp_table.add_row("Prediction",
                             f"{result.get('predicted_value', 'N/A'):,.0f}",
                             f"{pred_new.get('predicted_value', 'N/A'):,.0f}")
            for k in ["MAE", "RMSE", "MAPE"]:
                old_v = forecaster.metrics.get(k, "N/A")
                new_v = result_new.metrics.get(k, "N/A")
                old_str = f"{old_v:,.2f}" if isinstance(old_v, (int, float)) else str(old_v)
                new_str = f"{new_v:,.2f}" if isinstance(new_v, (int, float)) else str(new_v)
                comp_table.add_row(k, old_str, new_str)
            console.print(comp_table)
        else:
            table = Table(title="Cash Demand Forecast", box=box.ROUNDED)
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")
            table.add_row("Predicted Value", f"{result.get('predicted_value', 0):,.2f}")
            table.add_row("Lower Bound", f"{result.get('lower_bound', 0):,.2f}")
            table.add_row("Upper Bound", f"{result.get('upper_bound', 0):,.0f}")
            table.add_row("MAE", str(forecaster.metrics.get("MAE", "N/A")))
            table.add_row("RMSE", str(forecaster.metrics.get("RMSE", "N/A")))
            table.add_row("MAPE", f"{forecaster.metrics.get('MAPE', 'N/A')}%")
            console.print(table)
        if Confirm.ask("[yellow]Compare with LSTM?[/yellow]", default=False):
            lstm = LSTMForecaster()
            with console.status("[bold yellow]Loading LSTM model...", spinner="dots"):
                lstm_loaded = lstm.load()
            if not lstm_loaded:
                with console.status("[bold yellow]Training LSTM model...", spinner="dots"):
                    lstm.train(bank, metric)
            lstm_result = lstm.predict(bank, metric)
            if "error" not in lstm_result:
                side_table = Table(title="Prophet vs LSTM", box=box.ROUNDED)
                side_table.add_column("Metric", style="cyan")
                side_table.add_column("Prophet", style="green")
                side_table.add_column("LSTM", style="yellow")
                side_table.add_row("Prediction",
                                  f"{result.get('predicted_value', 0):,.2f}",
                                  f"{lstm_result.get('predicted_value', 0):,.2f}")
                side_table.add_row("Lower Bound",
                                  f"{result.get('lower_bound', 0):,.2f}",
                                  f"{lstm_result.get('lower_bound', 0):,.2f}")
                side_table.add_row("Upper Bound",
                                  f"{result.get('upper_bound', 0):,.2f}",
                                  f"{lstm_result.get('upper_bound', 0):,.2f}")
                console.print(side_table)
        if Confirm.ask("[yellow]Run walk-forward backtest?[/yellow]", default=False):
            lstm_bt = LSTMForecaster()
            bt_result = lstm_bt.backtest(bank, metric)
            if bt_result and len(bt_result) > 0:
                if isinstance(bt_result[-1], dict):
                    bt_table = Table(title="Walk-Forward Backtest Results", box=box.ROUNDED)
                    bt_table.add_column("Metric", style="cyan")
                    bt_table.add_column("Value", style="green")
                    for k, v in bt_result[-1].items():
                        bt_table.add_row(k, str(v))
                    console.print(bt_table)
                    actuals = [r[0] for r in bt_result[:-1]]
                    preds = [r[1] for r in bt_result[:-1]]
                    for i, (a, p) in enumerate(zip(actuals, preds)):
                        console.print(f"  Step {i+1}: Actual={a:,.2f} Predicted={p:,.2f}")
        pltxt.clear_data()
        pltxt.plot(result.get("predicted_value", 0), label="Prediction")
        pltxt.title("Cash Demand Forecast")
        console.print(pltxt.build())

    def _transaction_predict(self):
        predictor = TransactionPredictor()
        target = Prompt.ask("[yellow]Target metric[/yellow]", default="DC_Vol_Cash_ATM")
        with console.status("[bold yellow]Loading pre-trained model...", spinner="dots"):
            preloaded = predictor.load()
        if preloaded and Confirm.ask("[yellow]Use pre-trained model?[/yellow]", default=True):
            predictor.is_trained = True
        else:
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
                         BarColumn(), console=console) as progress:
                task = progress.add_task("[yellow]Training XGBoost...", total=100)
                result = predictor.train(target)
                progress.update(task, completed=100)
        if preloaded and not predictor.is_trained:
            new_predictor = TransactionPredictor()
            new_predictor.train(target)
            comp_table = Table(title="Model Comparison", box=box.ROUNDED)
            comp_table.add_column("Metric", style="cyan")
            comp_table.add_column("Pre-trained", style="green")
            comp_table.add_column("Retrained", style="yellow")
            for k in ["MAE", "RMSE", "R2"]:
                old_v = predictor.metrics.get(k, "N/A")
                new_v = new_predictor.metrics.get(k, "N/A")
                comp_table.add_row(k,
                                  f"{old_v:,.4f}" if isinstance(old_v, (int, float)) else str(old_v),
                                  f"{new_v:,.4f}" if isinstance(new_v, (int, float)) else str(new_v))
            console.print(comp_table)
        else:
            table = Table(title="XGBoost Performance", box=box.ROUNDED)
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")
            for k, v in predictor.metrics.items():
                table.add_row(k, f"{v:,.4f}" if isinstance(v, (int, float)) else str(v))
            console.print(table)
        importance = predictor.get_feature_importance()
        if importance:
            imp_table = Table(title="Top 10 Feature Importances", box=box.ROUNDED)
            imp_table.add_column("Feature", style="cyan")
            imp_table.add_column("Importance", style="green")
            for feat, imp in importance.items():
                imp_table.add_row(feat, f"{imp:.4f}")
            console.print(imp_table)
            pltxt.clear_data()
            top_feats = list(importance.keys())[:5]
            top_vals = list(importance.values())[:5]
            pltxt.simple_bar(top_feats, top_vals, width=60, title="Top 5 Features")
            console.print(pltxt.build())

    def _bank_clustering(self):
        clusterer = BankClustering()
        with console.status("[bold yellow]Computing optimal K...", spinner="dots"):
            opt_k, opt_score = clusterer.get_optimal_k(8)
        console.print(f"[green]Optimal clusters: {opt_k} (silhouette: {opt_score:.4f})[/green]")
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
                     BarColumn(), console=console) as progress:
            task = progress.add_task("[yellow]Running K-Means clustering...", total=100)
            results = clusterer.train(k=opt_k)
            progress.update(task, completed=100)
        table = Table(title="Bank Clusters", box=box.ROUNDED)
        table.add_column("Bank", style="cyan")
        table.add_column("Cluster", style="green")
        for _, row in results.iterrows():
            table.add_row(row["Bank"], str(row["Cluster"]))
        console.print(table)
        profiles = clusterer.get_cluster_profiles()
        if profiles:
            prof_table = Table(title="Cluster Profiles", box=box.ROUNDED)
            prof_table.add_column("Cluster", style="cyan")
            prof_table.add_column("Count", style="green")
            prof_table.add_column("Avg ATMs", style="yellow")
            prof_table.add_column("Avg Digital Share", style="magenta")
            for cid, prof in profiles.items():
                prof_table.add_row(str(cid), str(prof.get("Count", 0)),
                                  f"{prof.get('Total_ATMs', 0):,.0f}",
                                  f"{prof.get('Digital_Share', 0):.1f}%")
            console.print(prof_table)
        path = self.viz.plot_clusters(clusterer.X_pca, clusterer.labels)
        if path:
            console.print(f"[green]Cluster plot saved: {path}[/green]")
            self.viz.open_chart(path)

    def _anomaly_detection(self):
        detector = AnomalyDetector()
        with console.status("[bold yellow]Loading pre-trained model...", spinner="dots"):
            preloaded = detector.load()
        contamination = float(Prompt.ask("[yellow]Contamination rate[/yellow]", default="0.05"))
        if preloaded and Confirm.ask("[yellow]Use pre-trained model?[/yellow]", default=True):
            detector.is_trained = True
        else:
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
                         BarColumn(), console=console) as progress:
                task = progress.add_task("[yellow]Running Isolation Forest...", total=100)
                detector.train(contamination)
                progress.update(task, completed=100)
        table = Table(title="Anomaly Detection Results", box=box.ROUNDED)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        for k, v in detector.metrics.items():
            table.add_row(k.replace("_", " ").title(), str(v))
        console.print(table)
        flagged = detector.get_flagged_banks(10)
        if flagged:
            flag_table = Table(title="Top Flagged Banks", box=box.ROUNDED)
            flag_table.add_column("Bank", style="cyan")
            flag_table.add_column("Avg Anomaly Score", style="red")
            flag_table.add_column("Flagged Months", style="yellow")
            for f in flagged:
                flag_table.add_row(f["Bank_Name"], f"{f['Anomaly_Score']:.4f}", str(f["Flagged_Months"]))
            console.print(flag_table)

    def _trend_decompose(self):
        analyzer = TrendAnalyzer()
        selector = self._get_selector()
        bank = selector.select("Bank name (or All)", allow_all=True)
        metric = Prompt.ask("[yellow]Metric[/yellow]", default="Total_Txn_Vol")
        result = analyzer.decompose(bank, metric)
        if result is None:
            console.print("[red]Not enough data points for decomposition (need 4+).[/red]")
            return
        table = Table(title="Trend Decomposition \xe2\x80\x94 Latest Values", box=box.ROUNDED)
        table.add_column("Component", style="cyan")
        table.add_column("Latest Value", style="green")
        obs = 0; tr = 0; sea = 0; res = 0
        try:
            if hasattr(result, 'observed'): obs = result.observed.iloc[-1] if not pd.isna(result.observed.iloc[-1]) else 0
            if hasattr(result, 'trend'): tr = result.trend.iloc[-1] if not pd.isna(result.trend.iloc[-1]) else 0
            if hasattr(result, 'seasonal'): sea = result.seasonal.iloc[-1] if not pd.isna(result.seasonal.iloc[-1]) else 0
            if hasattr(result, 'resid'): res = result.resid.iloc[-1] if not pd.isna(result.resid.iloc[-1]) else 0
        except: pass
        table.add_row("Observed", f"{obs:,.2f}")
        table.add_row("Trend", f"{tr:,.2f}")
        table.add_row("Seasonal", f"{sea:,.2f}")
        table.add_row("Residual", f"{res:,.2f}")
        console.print(table)

    def _channel_migration(self):
        migrator = ChannelMigrationPredictor()
        selector = self._get_selector()
        bank = selector.select("Bank name (or All)", allow_all=True)
        months = IntPrompt.ask("[yellow]Months ahead to predict[/yellow]", default=3)
        with console.status("[bold yellow]Training migration model...", spinner="dots"):
            result = migrator.train(bank)
        if "error" in result:
            console.print(f"[red]{result['error']}[/red]")
            return
        pred = migrator.predict(bank, months)
        table = Table(title="Channel Migration Prediction", box=box.ROUNDED)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        table.add_row("Current Digital Share", f"{pred['current_digital_share']:.2f}%")
        table.add_row(f"Predicted ({months}m)", f"{pred['predicted_digital_share']:.2f}%")
        table.add_row("Shift", f"{pred['shift_pct']:+.2f}%")
        console.print(table)
        migrator.save()

    def _what_if(self):
        simulator = WhatIfSimulator()
        target = Prompt.ask("[yellow]Target metric[/yellow]", default="DC_Vol_Cash_ATM")
        with console.status("[bold yellow]Training scenario model...", spinner="dots"):
            result = simulator.train(target)
        console.print(f"[green]Model R\xc2\xb2: {result.get('R2', 'N/A')}[/green]")
        console.print("[yellow]Define changes (feature=delta, comma separated)[/yellow]")
        console.print("[dim]Available: ATMs_On_Site, ATMs_Off_Site, PoS, Micro_ATMs, Bharat_QR_Codes, UPI_QR_Codes, Credit_Cards_Outstanding, Debit_Cards_Outstanding[/dim]")
        changes_str = Prompt.ask("[yellow]Changes[/yellow]", default="ATMs_On_Site=1000, PoS=500")
        changes = {}
        for pair in changes_str.split(","):
            pair = pair.strip()
            if "=" in pair:
                k, v = pair.split("=", 1)
                changes[k.strip()] = float(v.strip())
        result = simulator.simulate(changes)
        if "error" in result:
            console.print(f"[red]{result['error']}[/red]")
            return
        table = Table(title="What-If Scenario Results", box=box.ROUNDED)
        table.add_column("Input Changes", style="cyan")
        table.add_column("Value", style="green")
        for k, v in result["changes"].items():
            table.add_row(k, f"{v:,.0f}")
        table.add_row("Predicted Impact", f"{result['estimated_change']:,.2f}")
        console.print(table)

    def _credit_score_prediction(self):
        scorer = CreditScorer()
        with console.status("[bold yellow]Loading credit scorer...", spinner="dots"):
            loaded = scorer.load()
        if not loaded:
            with console.status("[bold yellow]Training credit scorer...", spinner="dots"):
                scorer.train()
        user_data = {
            "age": self.user["age"], "is_minor": self.user.get("is_minor", False),
            "income_bracket": self.user.get("income_bracket", "not_earning_student"),
            "balance": self.user["balance"], "txn_count": 0, "fraud_count": 0,
        }
        txns = self.um.get_transactions(self.user["user_id"], 200)
        user_data["txn_count"] = len(txns)
        user_data["fraud_count"] = sum(1 for t in txns if t.get("is_fraud", 0))
        my_score = scorer.predict(user_data)
        table = Table(title="Credit Score Prediction", box=box.ROUNDED)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        table.add_row("Current Score", f"{self.user['credit_score']} / 900")
        table.add_row("ML Predicted", f"{my_score} / 900")
        table.add_row("Rating", self._credit_rating(my_score))
        if my_score > 750:
            table.add_row("Eligible For", "Premium loans, Platinum CC, Lower rates")
        elif my_score > 650:
            table.add_row("Eligible For", "Standard loans, Gold CC, Moderate rates")
        elif my_score > 500:
            table.add_row("Eligible For", "Basic loans, Secured CC, Higher rates")
        else:
            table.add_row("", "[!] Focus on building credit history")
        console.print(table)
        if scorer.metrics:
            console.print(f"[dim]Model: Gradient Boosting | MAE: {scorer.metrics.get('MAE', 'N/A')}[/dim]")
        pltxt.clear_data()
        pltxt.simple_bar(["Your Score", "Max"], [my_score, 900], width=30, title="Credit Score")
        console.print(pltxt.build())
        path = self.viz.plot_gauge(my_score)
        if path:
            self.viz.open_chart(path)

    def _credit_rating(self, score):
        if score >= 800: return "Excellent"
        if score >= 750: return "Very Good"
        if score >= 650: return "Good"
        if score >= 550: return "Fair"
        return "Poor"

    def _churn_analysis(self):
        predictor = ChurnPredictor()
        with console.status("[bold yellow]Loading churn predictor...", spinner="dots"):
            loaded = predictor.load()
        if not loaded:
            with console.status("[bold yellow]Training churn model...", spinner="dots"):
                predictor.train()
        txns = self.um.get_transactions(self.user["user_id"], 200)
        last_txn = txns[0]["timestamp"] if txns else "Never"
        days_since = 0
        if txns and txns[0].get("timestamp"):
            try:
                from datetime import datetime
                last = datetime.strptime(txns[0]["timestamp"][:10], "%Y-%m-%d")
                days_since = (datetime.now() - last).days
            except: pass
        user_features = {
            "age": self.user["age"], "balance": self.user["balance"],
            "credit_score": self.user["credit_score"],
            "txn_count": len(txns),
            "total_volume": sum(t.get("amount", 0) for t in txns),
            "avg_txn": np.mean([t.get("amount", 0) for t in txns]) if txns else 0,
            "days_since_last_txn": days_since,
        }
        result = predictor.predict(user_features)
        table = Table(title="Churn Risk Analysis", box=box.ROUNDED)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        table.add_row("Risk Score", f"{result['risk_score']*100:.1f}%")
        table.add_row("Risk Level", result["risk_level"])
        table.add_row("Last Transaction", str(last_txn)[:16] if last_txn != "Never" else "Never")
        table.add_row("Days Inactive", str(days_since))
        if result["risk_level"] == "HIGH":
            table.add_row("Suggestion", "Make a transaction soon to keep account active!")
        elif result["risk_level"] == "MEDIUM":
            table.add_row("Suggestion", "Consider setting up recurring deposits")
        else:
            table.add_row("Status", "Account is healthy and active")
        console.print(table)
        risk_val = result['risk_score']
        pltxt.clear_data()
        pltxt.simple_bar(["Risk"], [risk_val * 100], width=30, title="Churn Risk Meter")
        console.print(pltxt.build())
        path = self.viz.plot_churn_gauge(risk_val)
        if path:
            self.viz.open_chart(path)

    def _loan_default_risk(self):
        model = LoanDefaultModel()
        with console.status("[bold yellow]Loading loan risk model...", spinner="dots"):
            loaded = model.load()
        if not loaded:
            with console.status("[bold yellow]Training loan risk model...", spinner="dots"):
                model.train()
        amount = IntPrompt.ask("[yellow]Desired loan amount (\xe2\x82\xb9)[/yellow]", default=100000)
        rate = float(Prompt.ask("[yellow]Expected interest rate (%)[/yellow]", default="10.5"))
        tenure = IntPrompt.ask("[yellow]Tenure in months[/yellow]", default=36)
        user_data = {
            "age": self.user["age"], "is_minor": self.user.get("is_minor", False),
            "credit_score": self.user["credit_score"],
            "balance": self.user["balance"],
            "income_bracket": self.user.get("income_bracket", "earning_5L_10L"),
        }
        result = model.predict(user_data, amount, rate, tenure)
        if not result["eligible"]:
            console.print(f"[red]Not eligible: {result.get('reason', 'Risk too high')}[/red]")
            return
        table = Table(title="Loan Default Risk Assessment", box=box.ROUNDED)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        table.add_row("Requested Amount", f"\xe2\x82\xb9{amount:,}")
        table.add_row("Risk Score", f"{result['risk_score']*100:.1f}%")
        table.add_row("Risk Level", result["risk_level"])
        emi = int(amount * (rate/1200) * (1+rate/1200)**tenure / ((1+rate/1200)**tenure - 1))
        total_pay = emi * tenure
        table.add_row("Estimated EMI", f"\xe2\x82\xb9{emi:,}/mo")
        table.add_row("Total Payment", f"\xe2\x82\xb9{total_pay:,}")
        table.add_row("Total Interest", f"\xe2\x82\xb9{total_pay - amount:,}")
        table.add_row("Recommended Max", f"\xe2\x82\xb9{result.get('recommended_max', 0):,}")
        console.print(table)
        if result["risk_level"] == "LOW":
            console.print("[green]Low risk -- good candidate for loan approval![/green]")
        elif result["risk_level"] == "MEDIUM":
            console.print("[yellow]Medium risk -- consider smaller amount or better terms[/yellow]")
        else:
            console.print("[red]High risk -- not recommended at this time[/red]")
        schedule = []
        balance = amount
        monthly_rate = rate / 1200
        for m in range(1, tenure + 1):
            interest = balance * monthly_rate
            principal = emi - interest
            balance -= principal
            schedule.append({"month": m, "payment": round(emi, 2), "principal": round(principal, 2), "interest": round(interest, 2), "balance": round(max(balance, 0), 2)})
        am_table = Table(title="Amortization Schedule (First 12 Months)", box=box.ROUNDED)
        am_table.add_column("Month", style="cyan")
        am_table.add_column("Payment", style="green")
        am_table.add_column("Principal", style="yellow")
        am_table.add_column("Interest", style="red")
        am_table.add_column("Balance", style="magenta")
        for s in schedule[:12]:
            am_table.add_row(str(s["month"]), f"\xe2\x82\xb9{s['payment']:,.0f}", f"\xe2\x82\xb9{s['principal']:,.0f}", f"\xe2\x82\xb9{s['interest']:,.0f}", f"\xe2\x82\xb9{s['balance']:,.0f}")
        console.print(am_table)
        if tenure > 12:
            console.print(f"[dim]... and {tenure - 12} more months[/dim]")
        am_path = self.viz.plot_amortization_schedule(schedule)
        if am_path:
            self.viz.open_chart(am_path)
        pltxt.clear_data()
        pltxt.plot([s["balance"] for s in schedule], label="Balance")
        pltxt.title("Amortization Schedule")
        console.print(pltxt.build())

    def _bank_recommendation(self):
        recommender = BankRecommender()
        user_prefs = {
            "age": self.user["age"], "is_minor": self.user.get("is_minor", False),
            "income_bracket": self.user.get("income_bracket", "not_earning_student"),
            "preferences": {"prefer_network": True, "prefer_low_fees": True, "prefer_high_limits": False},
        }
        recommendations = recommender.recommend(user_prefs, top_n=5)
        current_bank = self.user["bank"]
        table = Table(title=f"Top 5 Banks For You (Current: {current_bank})", box=box.ROUNDED)
        table.add_column("Rank", style="cyan")
        table.add_column("Bank", style="green")
        table.add_column("Match Score", style="yellow")
        table.add_column("Why?", style="dim")
        for i, (bank, score) in enumerate(recommendations, 1):
            reasons = recommender.get_explanation(bank, user_prefs)
            why = "; ".join(reasons[:2]) if reasons else ""
            marker = " *" if bank == current_bank else ""
            table.add_row(f"#{i}", f"{bank}{marker}", f"{score:.0f}", why[:60])
        console.print(table)
        if current_bank != recommendations[0][0] if recommendations else False:
            console.print(f"[yellow]Did you know? Based on your profile, {recommendations[0][0]} might suit you better than {current_bank}![/yellow]")

    def _retrain_all(self):
        console.print("[bold yellow]Retraining ALL models for comparison...[/bold yellow]")
        models = [
            ("Cash Demand Forecaster", CashDemandForecaster()),
            ("Transaction Predictor", TransactionPredictor()),
            ("Bank Clustering", BankClustering()),
            ("Anomaly Detector", AnomalyDetector()),
            ("Channel Migration", ChannelMigrationPredictor()),
            ("What-If Simulator", WhatIfSimulator()),
            ("Credit Scorer", CreditScorer()),
            ("Churn Predictor", ChurnPredictor()),
            ("Loan Default", LoanDefaultModel()),
        ]
        results = []
        for name, model in models:
            with Progress(SpinnerColumn(), TextColumn(f"[progress.description]Training {name}..."),
                         console=console) as progress:
                task = progress.add_task("", total=1)
                try:
                    if isinstance(model, CashDemandForecaster): m = model.train()
                    elif isinstance(model, TransactionPredictor): m = model.train()
                    elif isinstance(model, BankClustering): m = model.train()
                    elif isinstance(model, AnomalyDetector): m = model.train()
                    elif isinstance(model, ChannelMigrationPredictor): m = model.train()
                    elif isinstance(model, WhatIfSimulator): m = model.train()
                    elif isinstance(model, CreditScorer): m = model.train()
                    elif isinstance(model, ChurnPredictor): m = model.train()
                    elif isinstance(model, LoanDefaultModel): m = model.train()
                    key_metric = str(model.metrics.get(next(iter(model.metrics)), ""))
                    results.append((name, "\u2713 Trained", key_metric[:50]))
                except Exception as e:
                    results.append((name, "\u2717 Failed", str(e)[:40]))
                progress.update(task, completed=1)
        table = Table(title="Model Training Results", box=box.ROUNDED)
        table.add_column("Model", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Key Metric", style="yellow")
        for name, status, metric in results:
            table.add_row(name, status, metric)
        console.print(table)
        from src.data_generator import DataGenerator
        dg = DataGenerator()
        dg.export_all(scenario="MODEL_RETRAIN")
        dg.close()

    def _atm_replenishment(self):
        forecaster = CashDemandForecaster()
        selector = self._get_selector()
        bank = selector.select("Bank name (or All)", allow_all=True)
        metric = Prompt.ask("[yellow]Metric[/yellow]", default="DC_Vol_Cash_ATM")
        with console.status("[bold yellow]Getting Prophet forecast...", spinner="dots"):
            forecaster.load()
            if not forecaster.is_trained:
                forecaster.train(bank, metric)
            pred_result = forecaster.predict(bank, metric)
        if "error" in pred_result:
            console.print(f"[red]{pred_result['error']}[/red]")
            return
        predicted_demand = pred_result.get("predicted_value", 1000000)
        optimizer = ATMReplenishmentOptimizer()
        result = optimizer.optimize(predicted_demand)
        table = Table(title="ATM Replenishment Optimization", box=box.ROUNDED)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        table.add_row("Predicted Monthly Demand", f"\xe2\x82\xb9{predicted_demand:,.0f}")
        table.add_row("Optimal Refill Amount", f"\xe2\x82\xb9{result['optimal_refill_amount']:,.0f}")
        table.add_row("Optimal Refills/Month", str(result['optimal_refills_per_month']))
        table.add_row("Replenishment Cost", f"\xe2\x82\xb9{result['total_replenishment_cost']:,.0f}")
        table.add_row("Holding Cost", f"\xe2\x82\xb9{result['total_holding_cost']:,.0f}")
        table.add_row("Total Cost", f"\xe2\x82\xb9{result['total_cost']:,.0f}")
        console.print(table)
        if Confirm.ask("[yellow]Compare with fixed-strategy approaches?[/yellow]", default=False):
            comp = optimizer.compare_strategies(predicted_demand)
            comp_table = Table(title="Replenishment Strategy Comparison", box=box.ROUNDED)
            comp_table.add_column("Strategy", style="cyan")
            comp_table.add_column("Refills", style="white")
            comp_table.add_column("Cost", style="green")
            comp_table.add_column("Holding Cost", style="yellow")
            comp_table.add_column("Total", style="red")
            for s in comp["strategies"]:
                comp_table.add_row(s["strategy_name"], str(s["refills"]),
                                  f"\xe2\x82\xb9{s['cost']:,.0f}", f"\xe2\x82\xb9{s['holding_cost']:,.0f}", f"\xe2\x82\xb9{s['total_cost']:,.0f}")
            console.print(comp_table)
            console.print(f"[green]Best: {comp['best_strategy']}[/green]")

    def _lstm_comparison(self):
        selector = self._get_selector()
        bank = selector.select("Bank name (or All)", allow_all=True)
        metric = Prompt.ask("[yellow]Metric[/yellow]", default="DC_Vol_Cash_ATM")
        prophet = CashDemandForecaster()
        lstm = LSTMForecaster()
        with console.status("[bold yellow]Training Prophet...", spinner="dots"):
            prophet.train(bank, metric)
        with console.status("[bold yellow]Training LSTM...", spinner="dots"):
            lstm.train(bank, metric)
        p_result = prophet.predict(bank, metric)
        l_result = lstm.predict(bank, metric)
        if "error" in p_result:
            console.print(f"[red]Prophet error: {p_result['error']}[/red]")
            return
        if "error" in l_result:
            console.print(f"[red]LSTM error: {l_result['error']}[/red]")
            return
        table = Table(title="LSTM vs Prophet Comparison", box=box.ROUNDED)
        table.add_column("Metric", style="cyan")
        table.add_column("Prophet", style="green")
        table.add_column("LSTM", style="yellow")
        table.add_row("Predicted Value",
                     f"{p_result.get('predicted_value', 0):,.2f}",
                     f"{l_result.get('predicted_value', 0):,.2f}")
        table.add_row("Lower Bound",
                     f"{p_result.get('lower_bound', 0):,.2f}",
                     f"{l_result.get('lower_bound', 0):,.2f}")
        table.add_row("Upper Bound",
                     f"{p_result.get('upper_bound', 0):,.2f}",
                     f"{l_result.get('upper_bound', 0):,.2f}")
        table.add_row("MAE",
                     str(prophet.metrics.get("MAE", "N/A")),
                     str(lstm.metrics.get("MAE", "N/A")))
        table.add_row("RMSE",
                     str(prophet.metrics.get("RMSE", "N/A")),
                     str(lstm.metrics.get("RMSE", "N/A")))
        table.add_row("MAPE",
                     str(prophet.metrics.get("MAPE", "N/A")),
                     str(lstm.metrics.get("MAPE", "N/A")))
        console.print(table)

    def _download_passbook(self):
        console.print(Panel("[bold yellow]Download Passbook & Account Assets[/bold yellow]", border_style="yellow"))
        txns = None
        try:
            conn = db.get_connection("ecosystem")
            cur = conn.execute(
                "SELECT * FROM transactions WHERE user_id = ? ORDER BY timestamp",
                (self.user["user_id"],)
            )
            cols = [d[0] for d in cur.description]
            txns = [dict(zip(cols, row)) for row in cur.fetchall()]
        except Exception:
            pass
        console.print("[dim]Generating combined passbook (will auto-detect all your accounts)...[/dim]")
        try:
            rg = ReportGenerator(self.da)
            rg.generate_passbook(self.user, txns, prompt_open=True)
            if Confirm.ask("[yellow]Also generate Account Summary Card?[/yellow]", default=True):
                rg.generate_account_summary_card(self.user, auto_open=True)
            if Confirm.ask("[yellow]Also export Account Data (JSON)?[/yellow]", default=False):
                rg.export_account_data_json(self.user, auto_open=False)
            console.print("[green]All passbook assets generated successfully![/green]")
        except Exception as e:
            console.print(f"[red]Error generating passbook: {e}[/red]")

    def _edit_profile(self):
        console.print("[yellow]Edit Profile (leave blank to keep current)[/yellow]")
        name = Prompt.ask(f"[yellow]Name[/yellow]", default=self.user["name"])
        phone = Prompt.ask(f"[yellow]Phone[/yellow]", default=self.user["phone"])
        email = Prompt.ask(f"[yellow]Email[/yellow]", default=self.user["email"])
        if name != self.user["name"]:
            ok, result = validate_name(name)
            if ok:
                self.um.update_user(self.user["user_id"], name=result)
                self.user["name"] = result
                console.print("[green][OK] Name updated[/green]")
        if phone != self.user["phone"]:
            ok, result = validate_phone(phone)
            if ok:
                self.um.update_user(self.user["user_id"], phone=result)
                self.user["phone"] = result
                console.print("[green][OK] Phone updated[/green]")
        if email != self.user["email"]:
            ok, result = validate_email(email)
            if ok:
                self.um.update_user(self.user["user_id"], email=result)
                self.user["email"] = result
                console.print("[green][OK] Email updated[/green]")

    def reports_menu(self):
        if not self.initialized:
            return
        while True:
            console.clear()
            table = Table(box=box.ROUNDED, show_header=False)
            table.add_column("Option", style="cyan", width=8)
            table.add_column("Feature", style="white")
            table.add_row("1", "Generate PDF Report (Global)")
            table.add_row("2", "Generate Portfolio Report (Personal)")
            table.add_row("3", "Export Data to CSV")
            table.add_row("4", "Export to Excel")
            table.add_row("5", "Save All Charts")
            table.add_row("6", "View Dataset Summary")
            table.add_row("7", "Export ML Training Datasets")
            table.add_row("8", "View Training Data Info")
            table.add_row("9", "Back to Main Menu")
            console.print(table)
            choice = Prompt.ask("[yellow]Select option[/yellow]",
                                choices=[str(i) for i in range(1, 10)])
            if choice == "1":
                self.reporter.generate_pdf_report()
            elif choice == "2":
                txns = self.um.get_transactions(self.user["user_id"], 10)
                self.reporter.generate_portfolio_report(self.user, txns)
            elif choice == "3":
                self._export_csv()
            elif choice == "4":
                self._export_excel()
            elif choice == "5":
                self._save_charts()
            elif choice == "6":
                self.reporter.show_summary_table()
            elif choice == "7":
                self.reporter.export_training_data()
            elif choice == "8":
                self.reporter.show_dataset_info()
            elif choice == "9":
                break

    def _export_csv(self):
        data_type = Prompt.ask("[yellow]Export what? (summary/raw/analysis)[/yellow]", default="summary")
        if data_type == "summary":
            self.reporter.export_csv(self.da.summary, "bank_summary")
        elif data_type == "raw":
            self.reporter.export_csv(self.da.df, "raw_data")
        elif data_type == "analysis":
            ms = self.da.market_share("Total_Txn_Vol")
            self.reporter.export_csv(ms, "market_share")

    def _export_excel(self):
        sheets = {
            "Bank Summary": self.da.summary,
            "Top Banks": self.da.top_banks("Total_Txn_Vol").reset_index(),
            "Monthly": self.da.monthly,
        }
        self.reporter.export_excel(sheets, "full_export")

    def _save_charts(self):
        with console.status("[bold yellow]Generating all charts...", spinner="dots"):
            self.viz.plot_correlation_heatmap()
            self.viz.plot_market_share("Total_Txn_Vol")
            self.viz.plot_monthly_trend("Total_Txn_Vol")
            self.viz.plot_monthly_trend("Digital_Share")
            self.viz.plot_channel_pie()
        console.print("[green]All charts saved to outputs/charts/[/green]")

    def refresh_data(self):
        if Confirm.ask("[yellow]Re-ingest data from CSV?[/yellow]", default=False):
            with console.status("[bold yellow]Re-ingesting data...", spinner="dots"):
                di = DataIngestion()
                di.run_pipeline()
                self.da = DataAnalysis()
                self.viz = DataVisualization(self.da)
                self.reporter = ReportGenerator(self.da)
                self.initialized = True
            console.print("[green]Data refreshed![/green]")

    def _investment_suggestions(self):
        recommender = InvestmentRecommender()
        result = recommender.recommend(
            age=self.user["age"],
            income_bracket=self.user.get("income_bracket", "not_earning_student"),
            balance=self.user["balance"],
            risk_tolerance=Prompt.ask("[yellow]Risk tolerance[/yellow]", choices=["conservative", "moderate", "aggressive"], default="moderate")
        )
        table = Table(title="Investment Suggestions", box=box.ROUNDED)
        table.add_column("Product", style="cyan")
        table.add_column("Allocation %", style="green")
        table.add_column("Amount", style="yellow")
        table.add_column("Expected Return", style="magenta")
        table.add_column("Yearly Return", style="white")
        for p in result["products"]:
            table.add_row(p["name"], f"{p['allocation_pct']}%",
                         f"\xe2\x82\xb9{p['amount']:,.0f}",
                         f"{p['expected_return_pct']}%",
                         f"\xe2\x82\xb9{p['expected_yearly_return']:,.0f}")
        console.print(table)
        console.print(f"[green]Total Expected Yearly Return: \xe2\x82\xb9{result['total_expected_return_yearly']:,.2f}[/green]")
        Prompt.ask("[yellow]Press Enter to continue[/yellow]", default="")

    def _rfm_analysis(self):
        segmenter = RFMSegmenter()
        txns = self.um.get_transactions(self.user["user_id"], 200)
        processed_txns = []
        for t in txns:
            try:
                ts = t.get("timestamp")
                if isinstance(ts, str):
                    from datetime import datetime
                    ts = datetime.strptime(ts[:19], "%Y-%m-%d %H:%M:%S") if ":" in ts else datetime.strptime(ts[:10], "%Y-%m-%d")
                processed_txns.append({"timestamp": ts, "amount": t.get("amount", 0)})
            except:
                processed_txns.append({"timestamp": None, "amount": t.get("amount", 0)})
        result = segmenter.segment(processed_txns)
        table = Table(title="RFM Analysis", box=box.ROUNDED)
        table.add_column("Metric", style="cyan")
        table.add_column("Score", style="green")
        table.add_row("Recency (R)", str(result["rfm_score"]["R"]))
        table.add_row("Frequency (F)", str(result["rfm_score"]["F"]))
        table.add_row("Monetary (M)", str(result["rfm_score"]["M"]))
        table.add_row("Total RFM Score", str(result["total_score"]))
        table.add_row("Segment", result["segment"])
        table.add_row("Recommendation", result["recommendation"][:80])
        console.print(table)
        Prompt.ask("[yellow]Press Enter to continue[/yellow]", default="")

    def _savings_goal_optimizer(self):
        target = IntPrompt.ask("[yellow]Target savings amount (\xe2\x82\xb9)[/yellow]", default=50000)
        deadline = IntPrompt.ask("[yellow]Deadline (months)[/yellow]", default=12)
        balance = IntPrompt.ask("[yellow]Current savings balance (\xe2\x82\xb9)[/yellow]", default=int(self.user.get("balance", 0)))
        income = IntPrompt.ask("[yellow]Monthly income (\xe2\x82\xb9)[/yellow]", default=50000)
        expenses = IntPrompt.ask("[yellow]Monthly expenses (\xe2\x82\xb9)[/yellow]", default=30000)
        optimizer = SavingsGoalOptimizer()
        result = optimizer.optimize(target, deadline, balance, income, expenses)
        table = Table(title="Savings Goal Optimization", box=box.ROUNDED)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        table.add_row("Target Amount", f"\xe2\x82\xb9{result['target_amount']:,}")
        table.add_row("Deadline", f"{result['deadline_months']} months")
        table.add_row("Required Monthly Deposit", f"\xe2\x82\xb9{result['required_monthly_deposit']:,.0f}")
        table.add_row("Monthly Surplus", f"\xe2\x82\xb9{result['monthly_surplus']:,.0f}")
        table.add_row("Status", result["status"].title())
        table.add_row("Recommended Product", result["recommended_product"])
        table.add_row("Interest Rate", f"{result['product_interest_rate']}%")
        table.add_row("Maturity Amount", f"\xe2\x82\xb9{result['maturity_amount']:,.0f}")
        console.print(table)
        console.print(f"[yellow]{result['suggestion_text']}[/yellow]")
        Prompt.ask("[yellow]Press Enter to continue[/yellow]", default="")

    def _feedback_sentiment(self):
        analyzer = SentimentAnalyzer()
        with console.status("[bold yellow]Analyzing feedback...", spinner="dots"):
            results = analyzer.analyze_feedback(ECOSYSTEM_DB)
        if not results:
            console.print("[yellow]No feedback found in the database.[/yellow]")
            Prompt.ask("[yellow]Press Enter to return[/yellow]", default="")
            return
        summary = analyzer.get_sentiment_summary(results)
        table = Table(title="Feedback Sentiment Analysis", box=box.ROUNDED)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        table.add_row("Total Feedback", str(summary["total_count"]))
        table.add_row("Positive", f"{summary['positive_count']} ({summary['positive_pct']}%)")
        table.add_row("Negative", f"{summary['negative_count']} ({summary['negative_pct']}%)")
        table.add_row("Neutral", f"{summary['neutral_count']} ({summary['neutral_pct']}%)")
        table.add_row("Avg Compound Score", str(summary["avg_compound"]))
        console.print(table)
        detail_table = Table(title="Feedback Details", box=box.ROUNDED)
        detail_table.add_column("ID", style="cyan")
        detail_table.add_column("Text", style="white")
        detail_table.add_column("Sentiment", style="green")
        for r in results[:10]:
            color = "green" if r["sentiment_label"] == "Positive" else "red" if r["sentiment_label"] == "Negative" else "yellow"
            detail_table.add_row(str(r["feedback_id"]), r["text"][:50], f"[{color}]{r['sentiment_label']}[/{color}]")
        console.print(detail_table)
        if len(results) > 10:
            console.print(f"[dim]... and {len(results) - 10} more entries[/dim]")
        Prompt.ask("[yellow]Press Enter to continue[/yellow]", default="")

    def _show_bank_attributes(self, selector):
        banks = selector.paginated_browse(title="Select a bank to see attributes")
        if not banks:
            return
        from src.bank_attributes import get_bank_attrs
        bank = banks if isinstance(banks, str) else banks[0]
        attrs = get_bank_attrs(bank)
        table = Table(title=f"Attributes: {bank}", box=box.ROUNDED)
        table.add_column("Attribute", style="cyan")
        table.add_column("Value", style="green")
        for k, v in attrs.items():
            if k in ("strengths", "weaknesses"):
                continue
            if isinstance(v, float):
                if "rate" in k and k != "digital_rating":
                    table.add_row(k.replace("_", " ").title(), f"{v}%")
                elif "limit" in k or "balance" in k or "fee" in k:
                    table.add_row(k.replace("_", " ").title(), f"\xe2\x82\xb9{v:,.0f}")
                else:
                    table.add_row(k.replace("_", " ").title(), str(v))
            else:
                table.add_row(k.replace("_", " ").title(), str(v))
        console.print(table)
        if attrs.get("strengths"):
            console.print(f"[green]\u2713 Strengths: {', '.join(attrs['strengths'][:3])}[/green]")
        if attrs.get("weaknesses"):
            console.print(f"[red]\u25b3 Weaknesses: {', '.join(attrs['weaknesses'][:3])}[/red]")

    def _random_bank(self, selector):
        import random
        bank = random.choice(selector.banks)
        console.print(f"[yellow]Random bank selected: {bank}[/yellow]")
        from src.bank_attributes import get_bank_attrs
        attrs = get_bank_attrs(bank)
        table = Table(title=f"Random Pick: {bank}", box=box.ROUNDED)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        table.add_row("Type", attrs.get("type", "N/A"))
        table.add_row("Savings Rate", f"{attrs.get('savings_rate', 'N/A')}%")
        table.add_row("Digital Rating", f"{attrs.get('digital_rating', 'N/A')}/5")
        table.add_row("ATM Limit", f"\xe2\x82\xb9{attrs.get('atm_daily_limit', 'N/A'):,}")
        table.add_row("Min Balance", f"\xe2\x82\xb9{attrs.get('min_balance', 'N/A'):,}")
        table.add_row("Tagline", attrs.get("tagline", ""))
        console.print(table)

    def _user_vs_industry(self):
        result = self.da.user_vs_industry(self.user)
        if "error" in result:
            console.print(f"[red]{result['error']}[/red]")
            return
        table = Table(title=f"Your Bank ({result['bank']}) vs Industry", box=box.ROUNDED)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        table.add_row("Your Bank's Digital Share", f"{result['bank_digital_share']}%")
        table.add_row("Industry Average", f"{result['industry_avg_digital']}%")
        table.add_row("Gap", f"{result['digital_gap']:+.1f}%")
        table.add_row("Your Balance", f"\xe2\x82\xb9{result['user_balance']:,.0f}")
        if result["above_industry"]:
            table.add_row("Status", "Your bank is ABOVE industry average!")
        else:
            table.add_row("Status", "Your bank is below industry average in digital adoption")
        console.print(table)

    def run(self):
        if not self.initialize():
            console.print("[red]Failed to initialize. Check data sources.[/red]")
            return
        if not self.login_gate():
            return
        self.main_menu()
        self.um.close()
        self.monitor.close()

if __name__ == "__main__":
    app = BankingAnalyticsSuite()
    app.run()
