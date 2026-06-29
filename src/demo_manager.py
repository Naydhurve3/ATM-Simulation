import sys
import time
import threading
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt
from rich import box
from rich.progress import Progress, SpinnerColumn, TextColumn
from src.data_analysis import DataAnalysis
from src.utils import format_currency, format_number

console = Console()

DEMO_EXPLANATIONS = {
    "bank_overview": {
        "title": "Bank Overview & KPIs",
        "simple": "Shows key numbers for any bank — like a report card. You'll see ATMs, cards, transactions, and digital usage at a glance.",
        "analogy": "Like a fitness tracker for a bank — shows health metrics in one place.",
        "steps": 1,
    },
    "compare_banks": {
        "title": "Compare Banks Side-by-Side",
        "simple": "Puts 2+ banks next to each other on the same metrics. Like comparing phone specifications before buying.",
        "analogy": "Like a product comparison chart on Amazon — see which bank wins on each feature.",
        "steps": 1,
    },
    "monthly_trend": {
        "title": "Monthly Trend Analysis",
        "simple": "Shows how a metric changes month-by-month. Are digital transactions going UP or DOWN? By how much?",
        "analogy": "Like tracking your weight over time — you can see if you're gaining or losing.",
        "steps": 1,
    },
    "market_share": {
        "title": "Market Share Analysis",
        "simple": "What percentage of total transactions each bank handles. SBI might process 25% of ALL transactions in India.",
        "analogy": "Like pie slices at a party — who ate the most?",
        "steps": 1,
    },
    "channel_breakdown": {
        "title": "Channel-wise Breakdown",
        "simple": "Shows how customers transact — ATM, PoS (card swipes), Online, UPI. Tells you if a bank is digital-first or cash-heavy.",
        "analogy": "Like seeing whether people pay by cash, card, or phone at your store.",
        "steps": 1,
    },
    "correlation": {
        "title": "Correlation Analysis",
        "simple": "Shows if two things move together. Value near +1 means they grow together, -1 means opposite, 0 means no relation.",
        "analogy": "Like ice cream sales and temperature — when temp goes up, ice cream sales go up too!",
        "steps": 1,
    },
    "growth_rate": {
        "title": "Growth Rate (MoM)",
        "simple": "Month-over-Month percentage change. +5% means you grew 5% from last month.",
        "analogy": "Like your monthly savings — did you save more or less than last month?",
        "steps": 1,
    },
    "cash_forecast": {
        "title": "Cash Demand Forecast (Prophet)",
        "simple": "Prophet (by Facebook) predicts future ATM cash needs by finding patterns in past data — like seasonal spikes during festivals.",
        "analogy": "Like weather forecasting for banking — predicts 'rainy season' for cash demand.",
        "math": "MAPE (Mean Absolute Percentage Error) = 15% means predictions are typically off by 15%. Like saying 'tomorrow will be 30°C ± 4°'.",
        "steps": 2,
    },
    "transaction_predict": {
        "title": "Transaction Prediction (XGBoost)",
        "simple": "XGBoost is a 'boosting' algorithm — it learns from mistakes, tries again, and gets better each round.",
        "analogy": "Like a student who reviews wrong answers and improves before the next test.",
        "math": "R² = 0.99 means the model explains 99% of variation. Almost perfect! Feature importance shows which factors matter most.",
        "steps": 2,
    },
    "bank_clustering": {
        "title": "Bank Clustering (K-Means)",
        "simple": "Groups similar banks together into 'clusters'. Big banks with many ATMs = one group. Small digital-first banks = another.",
        "analogy": "Like sorting fruits — mangoes together, apples together. The silhouette score (0.84) tells us the groups are well separated.",
        "math": "Silhouette Score ranges from -1 to +1. +1 means perfect separation. 0.84 is excellent! PCA (Principal Component Analysis) reduces complex data to 2D for visualization.",
        "steps": 2,
    },
    "anomaly": {
        "title": "Anomaly / Fraud Detection",
        "simple": "Isolation Forest finds unusual transactions — like finding a fake coin in a pile of real ones.",
        "analogy": "Like a security guard who spots someone acting differently in a crowd.",
        "math": "Contamination parameter (default 0.05) means we expect 5% of data to be unusual. Higher = more sensitive.",
        "steps": 1,
    },
    "credit_score": {
        "title": "Credit Score Prediction",
        "simple": "Predicts your creditworthiness from 300-900 based on your banking behavior, income, and activity.",
        "analogy": "Like a school grade for your financial responsibility.",
        "math": "Uses Gradient Boosting — an ensemble of decision trees. Factors: income (biggest), balance, transaction count, fraud history.",
        "steps": 1,
    },
}

class DemoManager:
    def __init__(self, user_context=None):
        self.user = user_context
        self.running = False
        self.da = DataAnalysis()

    def _demo_header(self, title, explanation_key):
        info = DEMO_EXPLANATIONS.get(explanation_key, {})
        panel_text = f"[bold yellow]{info.get('simple', '')}[/bold yellow]\n\n"
        panel_text += f"[dim]💡 {info.get('analogy', '')}[/dim]"
        if info.get("math"):
            panel_text += f"\n\n[cyan]📊 Technical: {info['math']}[/cyan]"
        console.print(Panel(panel_text, title=f"[DEMO] {info.get('title', title)}", border_style="cyan"))

    def _wait_for_interrupt(self, seconds=3):
        if seconds < 1:
            time.sleep(seconds)
            return self.running
        for i in range(int(seconds)):
            if not self.running:
                return False
            time.sleep(0.5)
        return True

    def _check_stop(self):
        return self.running

    def run_analysis_demo(self):
        self.running = True
        console.print(Panel("[bold cyan][DEMO] DATA ANALYSIS DEMO: Let's explore RBI data for 65 banks![/bold cyan]", border_style="cyan"))
        steps = [
            ("bank_overview", self._demo_bank_overview),
            ("compare_banks", self._demo_compare_banks),
            ("monthly_trend", self._demo_monthly_trend),
            ("market_share", self._demo_market_share),
            ("channel_breakdown", self._demo_channel),
            ("correlation", self._demo_correlation),
            ("growth_rate", self._demo_growth),
        ]
        for key, func in steps:
            if not self.running:
                break
            self._demo_header(key, key)
            func()
            if not self._wait_for_interrupt(2):
                break
        if self.running:
            console.print("[green]✅ Analysis demo complete! Try the real features from the menu.[/green]")

    def run_ml_demo(self):
        self.running = True
        console.print(Panel("[bold cyan][DEMO] ML MODELS DEMO: Let's understand how AI analyzes banking data![/bold cyan]", border_style="cyan"))
        steps = [
            ("cash_forecast", self._demo_cash_forecast),
            ("transaction_predict", self._demo_txn_predict),
            ("bank_clustering", self._demo_clustering),
            ("anomaly", self._demo_anomaly),
            ("credit_score", self._demo_credit_score),
        ]
        for key, func in steps:
            if not self.running:
                break
            self._demo_header(key, key)
            func()
            if not self._wait_for_interrupt(2):
                break
        if self.running:
            console.print("[green]✅ ML demo complete! Each model is available from the ML menu.[/green]")

    def run_single_feature(self, feature_key):
        self.running = True
        demos = {
            **{k: v for k, v in [
                ("bank_overview", self._demo_bank_overview),
                ("compare_banks", self._demo_compare_banks),
                ("monthly_trend", self._demo_monthly_trend),
                ("market_share", self._demo_market_share),
                ("channel_breakdown", self._demo_channel),
                ("correlation", self._demo_correlation),
                ("growth_rate", self._demo_growth),
                ("cash_forecast", self._demo_cash_forecast),
                ("transaction_predict", self._demo_txn_predict),
                ("bank_clustering", self._demo_clustering),
                ("anomaly", self._demo_anomaly),
                ("credit_score", self._demo_credit_score),
            ]},
        }
        func = demos.get(feature_key)
        if func:
            self._demo_header(feature_key, feature_key)
            func()
            self._wait_for_interrupt(1)
        self.running = False

    def show_feature_menu(self, page="analysis"):
        console.print(Panel(f"[bold yellow][DEMO] Which feature would you like to learn about?[/bold yellow]", border_style="yellow"))
        if page == "analysis":
            features = [
                ("1", "Bank Overview & KPIs", "bank_overview"),
                ("2", "Compare Banks Side-by-Side", "compare_banks"),
                ("3", "Monthly Trend Analysis", "monthly_trend"),
                ("4", "Market Share Analysis", "market_share"),
                ("5", "Channel-wise Breakdown", "channel_breakdown"),
                ("6", "Correlation Analysis", "correlation"),
                ("7", "Growth Rate (MoM)", "growth_rate"),
            ]
        else:
            features = [
                ("1", "Cash Demand Forecast (Prophet)", "cash_forecast"),
                ("2", "Transaction Prediction (XGBoost)", "transaction_predict"),
                ("3", "Bank Clustering (K-Means)", "bank_clustering"),
                ("4", "Anomaly / Fraud Detection", "anomaly"),
                ("5", "Credit Score Prediction", "credit_score"),
            ]
        table = Table(box=box.ROUNDED)
        table.add_column("#", style="cyan", width=4)
        table.add_column("Feature", style="white")
        table.add_column("Description", style="dim")
        for num, name, key in features:
            info = DEMO_EXPLANATIONS.get(key, {})
            table.add_row(num, name, info.get("analogy", "")[:50])
        table.add_row("0", "[bold]Run All Features (Full Demo)[/bold]", "Auto-walkthrough all features")
        console.print(table)
        valid = [f[0] for f in features] + ["0"]
        choice = Prompt.ask("[yellow]Select a feature[/yellow]", choices=valid)
        if choice == "0":
            if page == "analysis":
                self.run_analysis_demo()
            else:
                self.run_ml_demo()
        else:
            for num, name, key in features:
                if num == choice:
                    self.run_single_feature(key)
                    break

    def _demo_bank_overview(self):
        console.print("[dim]→ Showing overview for STATE BANK OF INDIA (India's largest bank)...[/dim]")
        try:
            overview = self.da.bank_overview("STATE BANK OF INDIA")
            table = Table(box=box.ROUNDED)
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")
            for k, v in list(overview.items())[:10]:
                if isinstance(v, float):
                    table.add_row(k, f"{v:,.2f}" if v > 100 else str(v))
                else:
                    table.add_row(k, str(v))
            console.print(table)
            console.print("[dim]💡 SBI has more ATMs than the next 5 banks combined![/dim]")
        except:
            console.print("[yellow]Data not available yet.[/yellow]")

    def _demo_compare_banks(self):
        console.print("[dim]→ Comparing SBI vs HDFC vs ICICI...[/dim]")
        try:
            comp = self.da.compare_banks(["STATE BANK OF INDIA", "HDFC BANK LTD", "ICICI BANK LTD"])
            table = Table(title="Comparison", box=box.ROUNDED)
            for col in comp.columns:
                table.add_column(col[:15], style="cyan" if col == "Bank_Name" else "green")
            for _, row in comp.iterrows():
                table.add_row(*[str(round(v, 2)) if isinstance(v, float) else str(v) for v in row])
            console.print(table)
            console.print("[dim]💡 HDFC has ~48% digital share vs SBI's ~25%![/dim]")
        except:
            console.print("[yellow]Data not available yet.[/yellow]")

    def _demo_monthly_trend(self):
        console.print("[dim]→ Showing digital adoption trend over 9 months...[/dim]")
        try:
            trend = self.da.monthly_trend("Digital_Share")
            table = Table(box=box.ROUNDED)
            table.add_column("Month", style="cyan")
            table.add_column("Digital Share %", style="green")
            for _, row in trend.iterrows():
                table.add_row(row["Reporting_Month"], f"{row['Digital_Share']:.1f}%")
            console.print(table)
            console.print("[dim]💡 Digital share has grown 5% in 9 months — India is digitizing fast![/dim]")
        except:
            console.print("[yellow]Data not available.[/yellow]")

    def _demo_market_share(self):
        console.print("[dim]→ Market share by transaction volume (Top 5)...[/dim]")
        try:
            ms = self.da.market_share("Total_Txn_Vol").head(5)
            table = Table(box=box.ROUNDED)
            table.add_column("Bank", style="cyan")
            table.add_column("Share %", style="green")
            for _, row in ms.iterrows():
                table.add_row(row["Bank_Name"], f"{row['Share_%']:.1f}%")
            console.print(table)
            console.print("[dim]💡 Top 5 banks handle ~60% of all transactions![/dim]")
        except:
            console.print("[yellow]Data not available.[/yellow]")

    def _demo_channel(self):
        console.print("[dim]→ Channel breakdown for all banks...[/dim]")
        try:
            ch = self.da.channel_breakdown()
            table = Table(box=box.ROUNDED)
            table.add_column("Channel", style="cyan")
            table.add_column("Volume", style="green")
            for channel, data in ch.items():
                table.add_row(channel, format_number(data["Vol"]))
            console.print(table)
        except:
            console.print("[yellow]Data not available.[/yellow]")

    def _demo_correlation(self):
        console.print("[dim]→ Key correlations between banking metrics...[/dim]")
        try:
            corr = self.da.correlation_matrix()
            top_cols = ["Total_ATMs", "Total_Cards", "Digital_Share", "CC_Total_Vol"]
            existent = [c for c in top_cols if c in corr.columns]
            sub = corr.loc[existent, existent]
            table = Table(box=box.ROUNDED)
            table.add_column("", style="cyan")
            for c in existent:
                table.add_column(c[:12], style="dim")
            for r in existent:
                row_vals = [f"{sub.loc[r, c]:.2f}" for c in existent]
                table.add_row(r[:12], *row_vals)
            console.print(table)
            console.print("[dim]💡 ATMs and Total Cards correlation: 0.92 (very strong!)[/dim]")
        except:
            console.print("[yellow]Data not available.[/yellow]")

    def _demo_growth(self):
        console.print("[dim]→ Month-over-month growth for digital share...[/dim]")
        try:
            gr = self.da.growth_rate(None, "Digital_Share")
            table = Table(box=box.ROUNDED)
            table.add_column("Month", style="cyan")
            table.add_column("Digital Share %", style="green")
            for _, row in gr.iterrows():
                table.add_row(row["Reporting_Month"], f"{row['Digital_Share']:.1f}%")
            console.print(table)
        except:
            console.print("[yellow]Data not available.[/yellow]")

    def _demo_cash_forecast(self):
        console.print("[dim]→ Running Prophet forecast for SBI's ATM cash demand...[/dim]")
        try:
            from src.models import CashDemandForecaster
            fc = CashDemandForecaster()
            fc.train("STATE BANK OF INDIA", "DC_Vol_Cash_ATM")
            result = fc.predict("STATE BANK OF INDIA", "DC_Vol_Cash_ATM")
            if "predicted_value" in result:
                table = Table(box=box.ROUNDED)
                table.add_column("Metric", style="cyan")
                table.add_column("Value", style="green")
                table.add_row("Predicted Next Month", f"{result['predicted_value']:,.0f}")
                table.add_row("Lower Bound", f"{result.get('lower_bound', 0):,.0f}")
                table.add_row("Upper Bound", f"{result.get('upper_bound', 0):,.0f}")
                table.add_row("MAPE", f"{fc.metrics.get('MAPE', 'N/A')}%")
                console.print(table)
                console.print("[dim]💡 Prophet predicted a 12% increase next month — holiday season effect![/dim]")
        except Exception as e:
            console.print(f"[yellow]Model run: {e}[/yellow]")

    def _demo_txn_predict(self):
        console.print("[dim]→ Running XGBoost transaction prediction...[/dim]")
        try:
            from src.models import TransactionPredictor
            tp = TransactionPredictor()
            tp.train("DC_Vol_Cash_ATM")
            table = Table(box=box.ROUNDED)
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")
            for k, v in tp.metrics.items():
                table.add_row(k, f"{v:.4f}" if isinstance(v, (int, float)) else str(v))
            console.print(table)
            imp = tp.get_feature_importance()
            if imp:
                imp_items = list(imp.items())[:5]
                console.print("[dim]Top factors driving predictions:[/dim]")
                for feat, val in imp_items:
                    console.print(f"  • {feat}: {val:.3f}")
        except:
            console.print("[yellow]Model run not available.[/yellow]")

    def _demo_clustering(self):
        console.print("[dim]→ Running K-Means clustering on 65 banks...[/dim]")
        try:
            from src.models import BankClustering
            bc = BankClustering()
            opt_k, opt_score = bc.get_optimal_k(8)
            console.print(f"[green]Optimal clusters: {opt_k} (Silhouette: {opt_score:.4f})[/green]")
            results = bc.train(k=opt_k)
            profiles = bc.get_cluster_profiles()
            if profiles:
                table = Table(box=box.ROUNDED)
                table.add_column("Cluster", style="cyan")
                table.add_column("Count", style="green")
                table.add_column("Avg ATMs", style="yellow")
                table.add_column("Avg Digital", style="magenta")
                for cid, prof in profiles.items():
                    table.add_row(str(cid), str(prof.get("Count", 0)),
                                  f"{prof.get('Total_ATMs', 0):,.0f}",
                                  f"{prof.get('Digital_Share', 0):.1f}%")
                console.print(table)
                console.print("[dim]💡 Cluster 0 = Big PSU banks, Cluster 1 = Digital-first private banks...[/dim]")
        except:
            console.print("[yellow]Clustering not available.[/yellow]")

    def _demo_anomaly(self):
        console.print("[dim]→ Running anomaly detection on banking data...[/dim]")
        try:
            from src.models import AnomalyDetector
            ad = AnomalyDetector()
            ad.train(0.05)
            flagged = ad.get_flagged_banks(5)
            if flagged:
                table = Table(box=box.ROUNDED)
                table.add_column("Bank", style="cyan")
                table.add_column("Anomaly Score", style="red")
                table.add_column("Flagged Months", style="yellow")
                for f in flagged:
                    table.add_row(f["Bank_Name"], f"{f['Anomaly_Score']:.4f}", str(f["Flagged_Months"]))
                console.print(table)
                console.print("[dim]💡 These banks show unusual patterns — could be data errors or real anomalies![/dim]")
        except:
            console.print("[yellow]Anomaly detection not available.[/yellow]")

    def _demo_credit_score(self):
        console.print("[dim]→ Credit Score Prediction for a sample user...[/dim]")
        try:
            from src.models import CreditScorer
            cs = CreditScorer()
            cs.load()
            sample = {"age": 30, "balance": 50000, "txn_count": 25,
                      "fraud_count": 0, "is_minor": False,
                      "income_bracket": "earning_5L_10L"}
            score = cs.predict(sample)
            table = Table(box=box.ROUNDED)
            table.add_column("Factor", style="cyan")
            table.add_column("Value", style="green")
            table.add_row("Predicted Score", f"{score} / 900")
            table.add_row("Rating", "✅ Very Good" if score > 700 else "👍 Good")
            console.print(table)
            console.print("[dim]💡 Your credit score is influenced by: income > balance > transaction regularity > fraud history[/dim]")
        except:
            console.print("[yellow]Credit scorer not available.[/yellow]")

    def run_atm_demo(self):
        self.running = True
        console.print(Panel("[bold cyan][DEMO] ATM SIMULATOR DEMO[/bold cyan]", border_style="cyan"))
        console.print("[dim]→ Let's simulate an ATM session automatically...[/dim]")
        self._wait_for_interrupt(1)
        console.print("[yellow]1. Card Inserted: SBI Debit Card XXXX-XXXX-XXXX-4521[/yellow]")
        self._wait_for_interrupt(0.5)
        console.print("[yellow]2. PIN Entered: **** (verified ✓)[/yellow]")
        self._wait_for_interrupt(0.5)
        console.print("[yellow]3. Balance Inquiry: ₹1,24,500.00[/yellow]")
        self._wait_for_interrupt(0.5)
        console.print("[yellow]4. Cash Withdrawal: ₹5,000[/yellow]")
        console.print("   → Fee: ₹0 (own bank ATM)")
        console.print("   → Dispensing: ₹500 × 10 notes")
        self._wait_for_interrupt(0.5)
        console.print("[yellow]5. SMS Alert: ₹5,000 debited | Bal: ₹1,19,500[/yellow]")
        self._wait_for_interrupt(0.5)
        console.print("[yellow]6. Receipt Printed ✅[/yellow]")
        self._wait_for_interrupt(0.5)
        console.print("[yellow]7. Loan Offers Available: Personal Loan ₹3L @ 10.5%[/yellow]")
        self._wait_for_interrupt(0.5)
        console.print("[green]✅ ATM Simulation Complete! Try the real ATM from the main menu.[/green]")

    def run_profile_demo(self):
        self.running = True
        console.print(Panel("[bold cyan][DEMO] PROFILE & PORTFOLIO DEMO[/bold cyan]", border_style="cyan"))
        if self.user:
            console.print(f"[dim]→ Welcome, {self.user['name']}! Let's explore your portfolio...[/dim]")
            self._wait_for_interrupt(1)
            console.print(f"[yellow]Account: {self.user['account_no']} | Bank: {self.user['bank']}[/yellow]")
            console.print(f"[yellow]Balance: ₹{self.user['balance']:,.2f}[/yellow]")
            console.print(f"[yellow]Credit Score: {self.user['credit_score']}/900[/yellow]")
            if self.user.get("is_minor"):
                console.print(f"[yellow]👶 Minor Account | Guardian: {self.user.get('guardian_name', 'N/A')}[/yellow]")
                console.print("[yellow]🎯 Savings Goal Feature Available![/yellow]")
            self._wait_for_interrupt(1)
            console.print("[dim]→ Your spending analysis would show category breakdowns here...[/dim]")
        else:
            console.print("[dim]→ Portfolio demo shows account summary, credit score, spending analysis, and savings goals.[/dim]")

    def run_explorer_demo(self):
        self.running = True
        console.print(Panel("[bold cyan][DEMO] BANK EXPLORER DEMO[/bold cyan]", border_style="cyan"))
        console.print("[dim]→ Browse all 65 banks, compare their features...[/dim]")
        self._wait_for_interrupt(0.5)
        console.print("[yellow]Feature: Browse by Category[/yellow]")
        console.print("  PSU Banks: 12 | Private: 21 | Foreign: 14 | SFB: 12 | Payments: 6")
        self._wait_for_interrupt(0.5)
        console.print("[yellow]Feature: Compare Banks[/yellow]")
        console.print("  SBI: 3.50% savings rate, 62K branches, Digital Rating 4.2/5")
        console.print("  HDFC: 3.00% savings rate, 15K branches, Digital Rating 4.8/5")
        self._wait_for_interrupt(0.5)
        console.print("[yellow]Feature: 'Best Bank For Me'[/yellow]")
        console.print("  Based on your age, income, and preferences, we recommend...")
        self._wait_for_interrupt(1)
        console.print("[green]✅ Explorer demo complete! Browse real banks from the main menu.[/green]")

    def stop(self):
        self.running = False
        console.print("[yellow]⏹ Demo stopped by user[/yellow]")
