import sys
import time
import random
import threading
from datetime import datetime
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt, Confirm
from rich import box
from rich.layout import Layout
from rich.text import Text
from src.utils import hash_pin, format_currency, format_number, calculate_cash_denominations, format_denominations
from src.bank_attributes import get_bank_attrs
from src.data_analysis import DataAnalysis
from src.models.real_time_fraud_detector import RealTimeFraudDetector

console = Console()

class ATMSimulator:
    def __init__(self, user_data, user_manager):
        self.user = user_data
        self.um = user_manager
        self.bank_attrs = get_bank_attrs(user_data["bank"])
        self.da = DataAnalysis()
        self.failed_attempts = 0
        self.max_attempts = 3
        self.locked = False
        self.is_minor = user_data.get("is_minor", False)
        self.age = user_data.get("age", 30)
        self.age_group = user_data.get("age_group", "Adult")
        self.fraud_detector = RealTimeFraudDetector()
        recent_txns = self.um.get_transactions(self.user["user_id"], 20)
        if recent_txns:
            self.fraud_detector.train(recent_txns)

    def _reload_user(self):
        self.user = self.um.get_user(self.user["user_id"])
        if self.user:
            self.bank_attrs = get_bank_attrs(self.user["bank"])

    def _cross_link_insight(self, txn_type, amount=0):
        try:
            if txn_type == "balance":
                avg = self.da.df.groupby("Bank_Name")["Debit_Cards_Outstanding"].mean().max()
                return f"[dim]Cross-link: Highest card base: ~{format_number(avg)} cards[/dim]"
            elif txn_type == "withdraw":
                total = self.da.df["DC_Vol_Cash_ATM"].sum()
                top = self.da.df.groupby("Bank_Name")["DC_Vol_Cash_ATM"].sum().idxmax()
                return f"[dim]Cross-link: Total DC ATM withdrawals: {format_number(total)}. Top: {top}[/dim]"
            elif txn_type == "deposit":
                total = self.da.df["DC_Vol_Cash_ATM"].sum()
                return f"[dim]Cross-link: Total ATM volume across RBI data: {format_number(total)}[/dim]"
            elif txn_type == "transfer":
                upi = self.da.df["UPI_QR_Codes"].sum()
                return f"[dim]Cross-link: Total UPI QR codes: {format_number(upi)}[/dim]"
            return ""
        except:
            return ""

    def _animated_card_insert(self):
        with console.status("[bold yellow]Inserting card...", spinner="dots"):
            time.sleep(1.2)

    def pin_check(self):
        if self.locked:
            console.print("[red]🔒 Account locked. Too many failed attempts.[/red]")
            return False
        for attempt in range(self.max_attempts):
            pin = Prompt.ask("[yellow]Enter your 4-digit PIN[/yellow]", password=True)
            if hash_pin(pin) == self.user["pin_hash"]:
                self.failed_attempts = 0
                return True
            self.failed_attempts += 1
            remaining = self.max_attempts - self.failed_attempts
            if self.failed_attempts >= self.max_attempts:
                self.locked = True
                console.print("[red]🔒 Too many failed attempts! Account locked.[/red]")
                return False
            console.print(f"[red]Incorrect PIN. {remaining} attempt(s) remaining.[/red]")
        return False

    def _simulate_sms(self, txn_type, amount, balance):
        console.print(Panel(f"""[dim]📱 SMS ALERT
{self.user['bank']}: ₹{amount:,.2f} {txn_type}d from a/c {self.user['account_no']}
Date: {datetime.now().strftime('%d-%b-%Y %H:%M')}
Bal: ₹{balance:,.2f}[/dim]""", border_style="dim", width=50))

    def _simulate_receipt(self, txn_type, amount, fee, balance):
        console.print(Panel(f"""[dim]🧾 RECEIPT
═══════════════════════
{self.user['bank']} ATM
{datetime.now().strftime('%d-%b-%Y %H:%M:%S')}
═══════════════════════
{txn_type.upper()}
Amount: ₹{amount:,.2f}
Fee:    ₹{fee:,.2f}
───────────────────────
Balance: ₹{balance:,.2f}
═══════════════════════
Thank you![/dim]""", border_style="dim", width=50))
        if Confirm.ask("[yellow]Print receipt?[/yellow]", default=True):
            console.print("[green]✅ Receipt printed[/green]")

    def _check_daily_limit(self, amount):
        used = self.user.get("atm_used_today", 0)
        limit = self.user.get("atm_daily_limit", self.bank_attrs.get("atm_daily_limit", 50000))
        if used + amount > limit:
            remaining = limit - used
            console.print(f"[red]Daily limit exceeded! Remaining: ₹{remaining:,.0f}[/red]")
            return False
        return True

    def _get_fee(self):
        return self.bank_attrs.get("atm_fee_own", 0)

    def bal_inq(self):
        with console.status("[bold yellow]Checking balance...", spinner="dots"):
            time.sleep(0.8)
        self._reload_user()
        insight = self._cross_link_insight("balance")
        rate = self.bank_attrs.get("savings_rate", 3.0)
        table = Table(show_header=False, box=box.ROUNDED)
        table.add_column("Detail", style="cyan")
        table.add_column("Value", style="green")
        table.add_row("Account Holder", self.user["name"])
        table.add_row("Account No", self.user["account_no"])
        table.add_row("Bank", f"{self.user['bank']} ({self.user['account_type'].title()})")
        table.add_row("Balance", f"₹{self.user['balance']:,.2f}")
        table.add_row("Interest Rate", f"{rate}% p.a.")
        if self.is_minor:
            table.add_row("Daily Limit", f"₹{self.user.get('atm_daily_limit', 2000):,.0f}")
        console.print(table)
        if insight:
            console.print(Panel(insight, border_style="dim"))
        self.um.record_transaction(self.user["user_id"], "balance_inquiry", 0, 0,
                                   self.user["balance"], self.user["balance"])

    def _check_fraud(self, amount):
        recent_txns = self.um.get_transactions(self.user["user_id"], 10)
        txn_info = {
            "amount": amount,
            "hour": datetime.now().hour,
            "day_of_week": datetime.now().weekday(),
            "type": "withdraw",
            "is_weekend": datetime.now().weekday() >= 5,
        }
        user_data = {
            "balance": self.user["balance"],
            "recent_txns": recent_txns,
        }
        fraud_result = self.fraud_detector.score(txn_info, user_data)
        if fraud_result["is_suspicious"]:
            console.print(f"[red]FRAUD ALERT: Suspicious transaction detected![/red]")
            console.print(f"[dim]Score: {fraud_result['fraud_score']:.2f} | Reasons: {', '.join(fraud_result['reasons'])}[/dim]")
            self.um.record_fraud_flag(self.user["user_id"], amount, fraud_result["fraud_score"],
                                      "; ".join(fraud_result["reasons"]))
            if not Confirm.ask("[yellow]This looks unusual. Still proceed?[/yellow]", default=False):
                return False
        return True

    def cash_with(self):
        if self.is_minor and self.age < 14:
            console.print("[yellow]This account is guardian-operated. Please ask your parent to transact.[/yellow]")
            return
        self._reload_user()
        balance = self.user["balance"]
        amt = IntPrompt.ask("[yellow]Enter amount to withdraw[/yellow]", default=100)
        if amt <= 0:
            console.print("[red]Invalid amount.[/red]")
            return
        if amt % 100 != 0:
            console.print("[red]Amount must be in multiples of 100.[/red]")
            return
        if amt > balance:
            console.print("[red]Insufficient funds.[/red]")
            return
        if not self._check_daily_limit(amt):
            return
        if not self._check_fraud(amt):
            return
        fee = self._get_fee()
        total_deduction = amt + fee
        if total_deduction > balance:
            console.print(f"[red]Insufficient funds (incl. fee {fee})[/red]")
            return
        if fee > 0 and not Confirm.ask(f"[yellow]Fee {fee} will be charged. Continue?[/yellow]", default=True):
            return
        with console.status("[bold yellow]Processing withdrawal...", spinner="dots"):
            time.sleep(1.5)
        new_balance = balance - total_deduction
        denominations = calculate_cash_denominations(amt)
        self.um.update_balance(self.user["user_id"], new_balance)
        self.um.update_atm_usage(self.user["user_id"], amt)
        self.um.record_transaction(self.user["user_id"], "withdraw", amt, fee,
                                    balance, new_balance, notes=str(denominations))
        self.um.record_credit_event(self.user["user_id"], "withdrawal", amt, -1)
        table = Table(show_header=False, box=box.ROUNDED)
        table.add_column("Detail", style="cyan")
        table.add_column("Value", style="green")
        table.add_row("Amount Debited", f"₹{amt:,.2f}")
        table.add_row("Fee Charged", f"₹{fee:,.2f}")
        table.add_row("Total Deducted", f"₹{total_deduction:,.2f}")
        table.add_row("New Balance", f"₹{new_balance:,.2f}")
        console.print(table)
        denom_str = format_denominations(denominations)
        console.print(Panel(f"[bold]Dispensing:[/bold]\n{denom_str}", border_style="green"))
        console.print(Panel("[green]✅ Please collect your cash[/green]", border_style="green"))
        self._simulate_sms("withdraw", amt, new_balance)
        self._simulate_receipt("withdraw", amt, fee, new_balance)
        insight = self._cross_link_insight("withdraw", amt)
        if insight:
            console.print(Panel(insight, border_style="dim"))
        self._offer_loans_if_eligible()

    def cash_dep(self):
        self._reload_user()
        amt = IntPrompt.ask("[yellow]Enter amount to deposit[/yellow]", default=100)
        if amt <= 0:
            console.print("[red]Invalid amount.[/red]")
            return
        if amt % 100 != 0:
            console.print("[red]Amount must be in multiples of 100.[/red]")
            return
        with console.status("[bold yellow]Processing deposit...", spinner="dots"):
            time.sleep(1.5)
        new_balance = self.user["balance"] + amt
        self.um.update_balance(self.user["user_id"], new_balance)
        self.um.record_transaction(self.user["user_id"], "deposit", amt, 0,
                                    self.user["balance"], new_balance)
        self.um.record_credit_event(self.user["user_id"], "deposit", amt, +2)
        console.print(Panel(f"[green]✅ ₹{amt:,.2f} deposited successfully![/green]\nNew Balance: ₹{new_balance:,.2f}",
                            border_style="green"))
        self._simulate_sms("deposit", amt, new_balance)
        self._simulate_receipt("deposit", amt, 0, new_balance)

    def fund_transfer(self):
        if self.is_minor:
            console.print("[yellow]👶 Transfer not available for minor accounts.[/yellow]")
            return
        self._reload_user()
        console.print("[yellow]Transfer options:[/yellow]")
        console.print("1. To another account (within bank)")
        console.print("2. To UPI ID")
        t_choice = Prompt.ask("[yellow]Choose[/yellow]", choices=["1", "2"], default="1")
        if t_choice == "1":
            target = Prompt.ask("[yellow]Enter beneficiary account number[/yellow]")
        else:
            target = Prompt.ask("[yellow]Enter UPI ID (e.g., name@upi)[/yellow]")
        amt = IntPrompt.ask("[yellow]Enter amount to transfer[/yellow]", default=100)
        if amt <= 0:
            console.print("[red]Invalid amount.[/red]")
            return
        if amt > self.user["balance"]:
            console.print("[red]Insufficient funds.[/red]")
            return
        with console.status("[bold yellow]Processing transfer...", spinner="dots"):
            time.sleep(2)
        new_balance = self.user["balance"] - amt
        self.um.update_balance(self.user["user_id"], new_balance)
        self.um.record_transaction(self.user["user_id"], "transfer", amt, 0,
                                    self.user["balance"], new_balance,
                                    channel="upi" if t_choice == "2" else "transfer",
                                    target_account=target)
        self.um.record_credit_event(self.user["user_id"], "transfer", amt, 0)
        console.print(Panel(f"""[green]✅ ₹{amt:,.2f} transferred to {target}[/green]
Remaining: ₹{new_balance:,.2f}""", border_style="green"))
        self._simulate_sms("transfer", amt, new_balance)

    def mini_statement(self):
        txns = self.um.get_transactions(self.user["user_id"], 10)
        table = Table(title="Mini Statement (Last 10)", box=box.ROUNDED)
        table.add_column("Date", style="dim", width=14)
        table.add_column("Type", style="cyan", width=16)
        table.add_column("Amount", style="green", width=16)
        table.add_column("Balance", style="yellow", width=16)
        for t in txns:
            ts = t.get("timestamp", "")[:10] if t.get("timestamp") else ""
            table.add_row(ts or "",
                         t.get("type", "").title()[:15],
                         format_currency(t.get("amount", 0)),
                         format_currency(t.get("balance_after", 0)))
        if not txns:
            table.add_row("", "No transactions yet", "", "")
        console.print(table)

    def change_pin(self):
        if self.um.change_pin(self.user["user_id"]):
            self._reload_user()

    def savings_goals_menu(self):
        from src.user_analytics import UserAnalytics
        ua = UserAnalytics(self.user)
        while True:
            console.print("[yellow]1. View Goals  2. Create Goal  3. Back[/yellow]")
            c = Prompt.ask("[yellow]Choose[/yellow]", choices=["1", "2", "3"])
            if c == "1":
                ua.show_savings_goals()
            elif c == "2":
                ua.create_savings_goal()
            else:
                break
        ua.close()

    def loan_offers_menu(self):
        if self.is_minor:
            console.print("[yellow]👶 Loan offers are not available for minor accounts. Focus on saving! 🎯[/yellow]")
            return
        self._reload_user()
        console.print(Panel("[bold yellow]💰 PRE-APPROVED OFFERS[/bold yellow]", border_style="yellow"))
        from src.models import LoanDefaultModel
        ldm = LoanDefaultModel()
        ldm.load()
        cs = self.user["credit_score"]
        bal = self.user["balance"]
        income = self.user.get("income_bracket", "earning_5L_10L")
        income_map = {"earning_25L_plus": 2500000, "earning_10L_25L": 1500000,
                      "earning_5L_10L": 750000, "earning_2.5L_5L": 350000,
                      "earning_under_2.5L": 150000}
        est_income = income_map.get(income, 500000)
        offers = []
        pl_amount = min(int(est_income * 0.67), 500000)
        pl_rate = self.bank_attrs.get("loan_rate_pl", 10.5)
        risk = ldm.predict(self.user, pl_amount, pl_rate, 36)
        offers.append(("Personal Loan", pl_amount, pl_rate, 36, risk, [
            "Medical emergencies — quick disbursal (24hrs)",
            "Higher education — invest in your future",
            "Wedding expenses — no collateral needed",
            "Home renovation — lower rate than credit card",
        ]))
        hl_amount = min(int(bal * 5), 800000)
        hl_rate = self.bank_attrs.get("loan_rate_home", 8.5)
        risk2 = ldm.predict(self.user, hl_amount, hl_rate, 120)
        offers.append(("Home Loan Top-Up", hl_amount, hl_rate, 120, risk2, [
            "Home extension and renovation",
            "Property furnishing and interiors",
            "Lower rate than personal loan",
            "Tax benefits under Section 24(b)",
        ]))
        od_amount = min(int(bal * 0.5), self.bank_attrs.get("overdraft_limit", 25000))
        offers.append(("Overdraft Facility", od_amount, 12.0, 1, {"eligible": od_amount > 5000, "risk_level": "LOW"}, [
            "Pay only on what you use — no fixed EMI",
            "Emergency buffer for everyday expenses",
            "No prepayment charges",
            "Interest only on utilized amount",
        ]))
        for idx, (name, amt, rate, tenure, risk_info, uses) in enumerate(offers, 1):
            if not risk_info.get("eligible", True):
                continue
            emi = round(amt * (rate / 1200) * (1 + rate / 1200) ** tenure /
                        ((1 + rate / 1200) ** tenure - 1)) if tenure > 1 else 0
            console.print(Panel(f"""[bold]{name}:[/bold] [green]₹{amt:,} @ {rate}%[/green]
EMI: ₹{emi:,}/mo ({tenure} months)  |  Risk: {risk_info.get('risk_level', 'N/A')}

[yellow]USE THIS FOR:[/yellow]
{chr(10).join(f'  ✅ {u}' for u in uses)}

[dim]Predictive insight: Based on {cs} credit score & ₹{bal:,} balance[/dim]""",
                                title=f"Offer #{idx}", border_style="cyan" if "LOW" in str(risk_info.get('risk_level', '')) else "yellow"))
        console.print("[yellow]Visit the 'My Profile' section to apply for loans.[/yellow]")
        Prompt.ask("[yellow]Press Enter to continue[/yellow]", default="")

    def _offer_loans_if_eligible(self):
        if self.is_minor or self.user["balance"] < 10000:
            return
        if random.random() < 0.3:
            if Confirm.ask("[yellow]💰 Check pre-approved loan offers?[/yellow]", default=False):
                self.loan_offers_menu()

    def run(self):
        self._animated_card_insert()
        console.print(Panel(f"[bold yellow]🏦 {self.user['bank']} ATM[/bold yellow]", border_style="yellow"))
        console.print(f"[green]Welcome, {self.user['name']}![/green]")
        if self.is_minor:
            age_label = "Child (Guardian-operated)" if self.age < 14 else "Teen (Self-operated with limits)"
            console.print(f"[cyan]👶 {age_label} Account | Daily Limit: ₹{self.user.get('atm_daily_limit', 2000):,}[/cyan]")
        if not self.pin_check():
            return
        while True:
            menu_items = [
                ("1", "Balance Inquiry"),
                ("2", "Cash Withdrawal"),
                ("3", "Cash Deposit"),
                ("4", "Fund Transfer"),
                ("5", "Mini Statement"),
                ("6", "Change PIN"),
            ]
            if self.is_minor and self.age >= 14:
                menu_items.append(("7", "🎯 Savings Goals"))
            elif not self.is_minor:
                menu_items.append(("7", "💰 Loan Offers"))
            menu_items.append(("8", "Exit"))
            table = Table(box=box.ROUNDED)
            table.add_column("Option", style="cyan", width=8)
            table.add_column("Feature", style="white")
            for opt, label in menu_items:
                table.add_row(opt, label)
            console.print(table)
            choices = [m[0] for m in menu_items]
            choice = Prompt.ask("[yellow]Select option[/yellow]", choices=choices)
            if choice == "1":
                self.bal_inq()
            elif choice == "2":
                self.cash_with()
            elif choice == "3":
                self.cash_dep()
            elif choice == "4":
                self.fund_transfer()
            elif choice == "5":
                self.mini_statement()
            elif choice == "6":
                self.change_pin()
            elif choice == "7":
                if self.is_minor and self.age >= 14:
                    self.savings_goals_menu()
                elif not self.is_minor:
                    self.loan_offers_menu()
                else:
                    break
            elif choice == "8":
                console.print(f"[green]Thank you, {self.user['name']}! Visit again![/green]")
                break
