import pandas as pd
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
from src.utils import format_currency, format_number
from src.data.db_manager import db

console = Console()

class UserAnalytics:
    def __init__(self, user_data):
        self.user = user_data

    @property
    def conn(self):
        return db.get_connection("ecosystem")

    def show_dashboard(self):
        table = Table(title=f"👤 {self.user['name']}'s Portfolio", box=box.ROUNDED)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        table.add_row("Account No", self.user["account_no"])
        table.add_row("Card No", self.user["card_no"])
        table.add_row("Bank", f"{self.user['bank']} ({self.user['account_type'].title()})")
        table.add_row("Age Group", self.user["age_group"])
        table.add_row("Balance", f"₹{self.user['balance']:,.2f}")
        table.add_row("Credit Score", f"{self.user['credit_score']} / 900")
        table.add_row("ATM Limit Today", f"₹{self.user['atm_daily_limit']:,.0f}")
        table.add_row("Account Status", "🟢 Active" if self.user["is_active"] else "🔴 Inactive")
        if self.user.get("is_minor"):
            table.add_row("Account Type", "👶 Minor (Guardian-managed)" if self.user["age"] < 14 else "🧑 Teen (Self-operated with limits)")
            table.add_row("Guardian", self.user.get("guardian_name", "N/A"))
        console.print(table)

    def show_spending_analysis(self):
        txns = self.conn.execute("""
            SELECT type, COUNT(*) as count, SUM(amount) as total,
                   AVG(amount) as avg_amt, SUM(fee) as total_fees
            FROM transactions WHERE user_id = ?
            GROUP BY type
        """, (self.user["user_id"],)).fetchall()
        if not txns:
            console.print("[yellow]No transaction history yet. Use the ATM to generate data![/yellow]")
            return
        table = Table(title="Spending Breakdown", box=box.ROUNDED)
        table.add_column("Type", style="cyan")
        table.add_column("Count", style="green")
        table.add_column("Total", style="yellow")
        table.add_column("Avg/Txn", style="magenta")
        table.add_column("Fees Paid", style="red")
        grand_total = 0
        grand_fees = 0
        grand_count = 0
        for t in txns:
            t_type, cnt, total, avg, fees = t
            total = total or 0
            fees = fees or 0
            table.add_row(t_type.title(), str(cnt), format_currency(total),
                          format_currency(avg or 0), format_currency(fees))
            grand_total += total
            grand_fees += fees
            grand_count += cnt
        table.add_row("[bold]Total[/bold]", str(grand_count), format_currency(grand_total),
                      "", format_currency(grand_fees))
        console.print(table)
        self._show_monthly_trend()

    def _show_monthly_trend(self):
        monthly = self.conn.execute("""
            SELECT strftime('%Y-%m', timestamp) as month,
                   SUM(CASE WHEN type='withdraw' THEN amount ELSE 0 END) as spent,
                   SUM(CASE WHEN type='deposit' THEN amount ELSE 0 END) as deposited
            FROM transactions WHERE user_id = ?
            GROUP BY month ORDER BY month DESC LIMIT 6
        """, (self.user["user_id"],)).fetchall()
        if monthly:
            table = Table(title="Monthly Activity (Last 6)", box=box.ROUNDED)
            table.add_column("Month", style="cyan")
            table.add_column("Spent", style="red")
            table.add_column("Deposited", style="green")
            table.add_column("Net", style="yellow")
            for m in monthly:
                net = (m[2] or 0) - (m[1] or 0)
                net_str = f"+₹{net:,.0f}" if net >= 0 else f"-₹{abs(net):,.0f}"
                table.add_row(m[0], format_currency(m[1] or 0),
                              format_currency(m[2] or 0), net_str)
            console.print(table)

    def show_transaction_history(self, limit=15):
        txns = self.conn.execute("""
            SELECT timestamp, type, amount, fee, balance_after, channel, target_account
            FROM transactions WHERE user_id = ?
            ORDER BY timestamp DESC LIMIT ?
        """, (self.user["user_id"], limit)).fetchall()
        if not txns:
            console.print("[yellow]No transactions yet[/yellow]")
            return
        table = Table(title=f"Last {limit} Transactions", box=box.ROUNDED)
        table.add_column("Date", style="dim")
        table.add_column("Type", style="cyan")
        table.add_column("Amount", style="green")
        table.add_column("Fee", style="red")
        table.add_column("Balance", style="yellow")
        table.add_column("Channel", style="magenta")
        for t in txns:
            ts, t_type, amt, fee, bal, chan, target = t
            amt = amt or 0; fee = fee or 0; bal = bal or 0
            table.add_row(ts[:16] if ts else "", t_type.title(),
                          format_currency(amt), format_currency(fee),
                          format_currency(bal), chan or "atm")
        console.print(table)

    def show_savings_goals(self):
        goals = self.conn.execute("""
            SELECT goal_name, target_amount, current_amount, deadline, is_completed
            FROM savings_goals WHERE user_id = ?
        """, (self.user["user_id"],)).fetchall()
        if not goals:
            console.print("[yellow]No savings goals set. You can create one![/yellow]")
            return
        table = Table(title="🎯 Savings Goals", box=box.ROUNDED)
        table.add_column("Goal", style="cyan")
        table.add_column("Target", style="green")
        table.add_column("Saved", style="yellow")
        table.add_column("Progress", style="magenta")
        table.add_column("Deadline", style="red")
        for g in goals:
            name, target, current, deadline, done = g
            pct = (current / target * 100) if target > 0 else 0
            done_str = "✅" if done else "🔄"
            table.add_row(f"{done_str} {name}", format_currency(target),
                          format_currency(current), f"{pct:.0f}%",
                          deadline or "No deadline")
        console.print(table)

    def create_savings_goal(self):
        from rich.prompt import Prompt, IntPrompt
        name = Prompt.ask("[yellow]Goal name[/yellow]")
        target = IntPrompt.ask("[yellow]Target amount (₹)[/yellow]")
        deadline = Prompt.ask("[yellow]Deadline (optional, YYYY-MM-DD or press Enter)[/yellow]", default="")
        self.conn.execute("""
            INSERT INTO savings_goals (user_id, goal_name, target_amount, deadline)
            VALUES (?, ?, ?, ?)
        """, (self.user["user_id"], name, target, deadline or None))
        self.conn.commit()
        console.print(f"[green]✅ Goal '{name}' created![/green]")

    def show_credit_score_breakdown(self):
        table = Table(title=f"Credit Score: {self.user['credit_score']} / 900", box=box.ROUNDED)
        table.add_column("Factor", style="cyan")
        table.add_column("Impact", style="green")
        bal = self.user["balance"]
        txns = self.conn.execute("SELECT COUNT(*), COALESCE(SUM(fee),0) FROM transactions WHERE user_id=?",
                                 (self.user["user_id"],)).fetchone()
        txn_count = txns[0] if txns else 0
        total_fees = txns[1] if txns else 0
        score = self.user["credit_score"]
        if self.user.get("is_minor"):
            table.add_row("Account Type", "Minor (protected score)")
            table.add_row("Base Score", "650 (minors start higher)")
            table.add_row("Savings Consistency", f"+{min(bal/10000, 5)*10:.0f}")
        else:
            table.add_row("Base Score", "600")
            table.add_row("Income Factor", f"+{max(0, (score - 600) // 3)}")
            table.add_row("Balance Factor", f"+{min(bal/5000, 10):.0f}")
            table.add_row("Transaction Activity", f"+{min(txn_count, 20):.0f}")
            table.add_row("Fee Impact", f"-{min(total_fees/100, 10):.0f}")
        table.add_row("", "")
        table.add_row("📊 Rating", self._get_rating(score))
        console.print(table)

    def _get_rating(self, score):
        if score >= 800: return "🌟 Excellent"
        if score >= 750: return "✅ Very Good"
        if score >= 650: return "👍 Good"
        if score >= 550: return "⚠️ Fair"
        return "❌ Poor"

    def close(self):
        pass
