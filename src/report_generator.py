import os
import pandas as pd
import sqlite3
from datetime import datetime
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
from rich.prompt import Prompt, Confirm
from fpdf import FPDF
from PIL import Image
import fitz
from src.utils import OUTPUTS_REPORTS, OUTPUTS_CHARTS, format_currency, format_number, get_scenario_timestamp
from src.data.db_manager import db
from src.data_analysis import DataAnalysis

console = Console()

class ReportGenerator:
    def __init__(self, da=None):
        self.da = da or DataAnalysis()
        self.report_dir = OUTPUTS_REPORTS
        self.report_dir.mkdir(parents=True, exist_ok=True)

    def generate_pdf_report(self, title="Banking Analytics Report"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, title, ln=True, align="C")
        pdf.set_font("Arial", "", 10)
        pdf.cell(0, 8, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True, align="C")
        pdf.ln(10)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, "Top Banks by Transaction Volume", ln=True)
        pdf.set_font("Arial", "", 9)
        top = self.da.top_banks("Total_Txn_Vol", 10)
        for bank, val in top.items():
            pdf.cell(0, 6, f"{bank}: {format_number(val)}", ln=True)
        pdf.ln(5)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, "Overall Statistics", ln=True)
        pdf.set_font("Arial", "", 9)
        stats = self.da.get_statistics("Total_Txn_Vol")
        for k, v in stats.items():
            pdf.cell(0, 6, f"{k.capitalize()}: {format_number(v)}", ln=True)
        pdf.ln(5)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, "Digital Adoption Overview", ln=True)
        pdf.set_font("Arial", "", 9)
        avg_digital = self.da.df["Digital_Share"].mean()
        pdf.cell(0, 6, f"Average Digital Share: {avg_digital:.1f}%", ln=True)
        path = self.report_dir / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        pdf.output(str(path))
        console.print(f"[green]PDF report saved: {path}[/green]")
        return path

    def generate_portfolio_report(self, user_data, txns=None):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, f"Portfolio Report — {user_data['name']}", ln=True, align="C")
        pdf.set_font("Arial", "", 10)
        pdf.cell(0, 6, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True, align="C")
        pdf.ln(10)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, "Account Details", ln=True)
        pdf.set_font("Arial", "", 9)
        pdf.cell(0, 6, f"Account No: {user_data['account_no']}", ln=True)
        pdf.cell(0, 6, f"Bank: {user_data['bank']} ({user_data['account_type'].title()})", ln=True)
        pdf.cell(0, 6, f"Balance: Rs. {float(user_data['balance']):,.2f}", ln=True)
        pdf.cell(0, 6, f"Credit Score: {user_data['credit_score']}/900", ln=True)
        if user_data.get("is_minor"):
            pdf.cell(0, 6, f"Guardian: {user_data.get('guardian_name', 'N/A')}", ln=True)
        pdf.ln(5)
        if txns:
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 8, "Recent Transactions", ln=True)
            pdf.set_font("Arial", "", 8)
            for t in txns[:10]:
                pdf.cell(0, 5, f"{str(t.get('timestamp',''))[:10]} | {t.get('type','').title()} | Rs.{float(t.get('amount',0)):,.0f}", ln=True)
        path = self.report_dir / f"portfolio_{user_data['name'].replace(' ','_')}_{datetime.now().strftime('%Y%m%d')}.pdf"
        pdf.output(str(path))
        console.print(f"[green]Portfolio report saved: {path}[/green]")
        return path

    def export_csv(self, data, filename="export"):
        path = self.report_dir / f"{filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        if isinstance(data, pd.DataFrame):
            data.to_csv(path, index=False)
        elif isinstance(data, dict):
            pd.DataFrame([data]).to_csv(path, index=False)
        elif isinstance(data, list):
            pd.DataFrame(data).to_csv(path, index=False)
        console.print(f"[green]CSV exported: {path}[/green]")
        return path

    def export_excel(self, data, filename="export"):
        path = self.report_dir / f"{filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        writer = pd.ExcelWriter(str(path), engine="openpyxl")
        if isinstance(data, pd.DataFrame):
            data.to_excel(writer, sheet_name="Data", index=False)
        elif isinstance(data, dict):
            for name, df in data.items():
                if isinstance(df, pd.DataFrame):
                    df.to_excel(writer, sheet_name=str(name)[:31], index=False)
        writer.close()
        console.print(f"[green]Excel exported: {path}[/green]")
        return path

    def export_training_data(self):
        from src.data_generator import DataGenerator
        if Confirm.ask("[yellow]Export ALL ML training datasets?[/yellow]", default=True):
            dg = DataGenerator()
            dg.export_all(scenario="MANUAL_EXPORT")
            dg.close()
            console.print("[green]✅ All training datasets exported to outputs/training_data/[/green]")

    def show_summary_table(self):
        table = Table(title="Dataset Summary", box=box.ROUNDED)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        table.add_row("Total Banks", str(len(self.da.get_banks())))
        table.add_row("Months Covered", str(len(self.da.get_months())))
        total_txn = self.da.df["Total_Txn_Vol"].sum()
        total_val = self.da.df["Total_Txn_Val"].sum()
        table.add_row("Total Transaction Volume", format_number(total_txn))
        table.add_row("Total Transaction Value", format_currency(total_val))
        avg_digital = self.da.df["Digital_Share"].mean()
        table.add_row("Avg Digital Share", f"{avg_digital:.1f}%")
        try:
            conn = db.get_connection("ecosystem")
            user_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            txn_count = conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
            table.add_row("Registered Users", str(user_count))
            table.add_row("Total Transactions", str(txn_count))
        except:
            pass
        console.print(table)
        return table

    def show_dataset_info(self):
        console.print(Panel("[bold cyan] Training Datasets Overview[/bold cyan]", border_style="cyan"))
        table = Table(box=box.ROUNDED)
        table.add_column("Dataset", style="cyan")
        table.add_column("Used By Models", style="green")
        table.add_column("Update Trigger", style="yellow")
        datasets = [
            ("user_profiles.csv", "CreditScorer, ChurnPredictor, Recommender", "Every 5 new users"),
            ("transaction_history.csv", "SpendingForecaster, AnomalyDetector", "Every 50 transactions"),
            ("fraud_training.csv", "AnomalyDetector (Isolation Forest)", "On fraud alert"),
            ("credit_scoring.csv", "CreditScorer (Gradient Boosting)", "On loan event / user milestone"),
            ("churn_analysis.csv", "ChurnPredictor (Random Forest)", "On session end"),
            ("loan_risk_data.csv", "LoanDefaultModel (Logistic Reg)", "On loan application"),
            ("spending_patterns.csv", "WhatIfSimulator, ChannelMigration", "Every 50 transactions"),
            ("bank_preferences.csv", "BankRecommender (Cosine Sim)", "Every 5 new users"),
        ]
        for name, models, trigger in datasets:
            table.add_row(name, models, trigger)
        console.print(table)

    # ─── PASSBOOK SYSTEM ─────────────────────────────────────────────────

    def _find_linked_accounts(self, user_data):
        conn = db.get_connection("ecosystem")
        rows = conn.execute(
            "SELECT * FROM users WHERE LOWER(name) = LOWER(?) OR phone = ? OR email = ? ORDER BY user_id",
            (user_data["name"], str(user_data.get("phone", "")), str(user_data.get("email", "")))
        ).fetchall()
        if not rows:
            return [user_data]
        cols = rows[0].keys()
        accounts = []
        for row in rows:
            d = dict(zip(cols, row))
            d["is_minor"] = bool(d["is_minor"])
            accounts.append(d)
        return accounts

    def _count_total_transactions(self, accounts):
        conn = db.get_connection("ecosystem")
        total = 0
        for acc in accounts:
            total += conn.execute("SELECT COUNT(*) FROM transactions WHERE user_id = ?", (acc["user_id"],)).fetchone()[0]
        return total

    def _render_pdf_to_png(self, pdf_path, dpi=150):
        doc = fitz.open(str(pdf_path))
        images = []
        for page_num in range(len(doc)):
            page = doc[page_num]
            pix = page.get_pixmap(dpi=dpi)
            img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            images.append(img)
        doc.close()
        total_height = sum(img.height for img in images)
        max_width = max(img.width for img in images)
        stacked = Image.new("RGB", (max_width, total_height), (255, 255, 255))
        y_offset = 0
        for img in images:
            stacked.paste(img, (0, y_offset))
            y_offset += img.height
        png_path = pdf_path.with_suffix(".png")
        stacked.save(str(png_path), "PNG")
        return png_path

    def generate_passbook(self, user_data, txns=None, prompt_open=True):
        accounts = self._find_linked_accounts(user_data)
        primary = accounts[0]
        all_txns = {}
        for acc in accounts:
            uid = acc["user_id"]
            if txns is not None and uid == user_data["user_id"]:
                all_txns[uid] = txns
            else:
                conn = db.get_connection("ecosystem")
                cur = conn.execute(
                    "SELECT * FROM transactions WHERE user_id = ? ORDER BY timestamp ASC", (uid,)
                )
                cols = [d[0] for d in cur.description]
                all_txns[uid] = [dict(zip(cols, row)) for row in cur.fetchall()]
        total_txns = sum(len(t) for t in all_txns.values())
        name_slug = primary["name"].replace(" ", "_")[:20]
        filename = f"passbook_{primary['user_id']}_{name_slug}.pdf"
        path = self.report_dir / filename
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=18)
        self._passbook_cover(pdf, accounts)
        for acc in accounts:
            section_label = f"Account: {acc['bank']} ({acc['account_no']})"
            uid = acc["user_id"]
            self._passbook_account_details(pdf, acc, section_label)
            self._passbook_kyc_page(pdf, acc, section_label)
            self._passbook_welcome_page(pdf, acc, section_label)
            self._passbook_transaction_ledger(pdf, acc, all_txns.get(uid, []), section_label)
        self._passbook_charts_page(pdf, accounts, all_txns)
        self._passbook_ml_insights(pdf, accounts)
        pdf.output(str(path))
        if total_txns <= 20:
            png_path = self._render_pdf_to_png(path)
            path.unlink()
            final_path = png_path
            fmt = "PNG"
        else:
            final_path = path
            fmt = "PDF"
        console.print(f"[green]Passbook saved: {final_path} ({fmt}, {total_txns} transactions across {len(accounts)} account(s))[/green]")
        if prompt_open:
            if Confirm.ask("[yellow]Open passbook?[/yellow]", default=True):
                try:
                    os.startfile(str(final_path))
                except Exception:
                    pass
        return final_path

    def _passbook_cover(self, pdf, accounts):
        pdf.add_page()
        pdf.set_fill_color(15, 52, 96)
        pdf.rect(0, 0, 210, 297, "F")
        pdf.set_text_color(233, 69, 96)
        pdf.set_font("Arial", "B", 28)
        pdf.ln(30)
        pdf.cell(0, 15, "COMBINED PASSBOOK", ln=True, align="C")
        pdf.ln(3)
        pdf.set_font("Arial", "", 11)
        pdf.set_text_color(200, 200, 200)
        pdf.cell(0, 8, "Complete Account Statement & Record", ln=True, align="C")
        pdf.ln(10)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Arial", "B", 18)
        pdf.cell(0, 12, accounts[0]["name"], ln=True, align="C")
        pdf.ln(8)
        pdf.set_font("Arial", "", 11)
        pdf.set_text_color(180, 200, 220)
        for i, acc in enumerate(accounts):
            pdf.cell(0, 7, f"Account {i+1}: {acc['account_no']}  |  {acc['bank']}  |  {acc['account_type'].title()}", ln=True, align="C")
        pdf.ln(25)
        pdf.set_font("Arial", "", 8)
        pdf.set_text_color(150, 150, 150)
        pdf.cell(0, 6, f"Generated: {datetime.now().strftime('%d-%b-%Y %H:%M')}", ln=True, align="C")
        pdf.cell(0, 6, "This is a computer-generated document. No signature required.", ln=True, align="C")

    def _passbook_account_details(self, pdf, user_data, section_label=None):
        pdf.add_page()
        pdf.set_text_color(233, 69, 96)
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "ACCOUNT DETAILS", ln=True)
        if section_label:
            pdf.set_font("Arial", "", 9)
            pdf.set_text_color(100, 100, 100)
            pdf.cell(0, 6, section_label, ln=True)
        pdf.set_text_color(50, 50, 50)
        pdf.ln(5)
        details = [
            ("Full Name", user_data["name"]),
            ("Account No", user_data["account_no"]),
            ("Card Number", self._mask_card(user_data["card_no"])),
            ("Bank Name", user_data["bank"]),
            ("Account Type", user_data["account_type"].title()),
            ("Age Group", user_data.get("age_group", "N/A")),
            ("Age", str(user_data.get("age", "N/A"))),
            ("Phone", str(user_data.get("phone", "N/A"))),
            ("Email", user_data.get("email", "N/A")),
            ("Current Balance", f"Rs. {float(user_data['balance']):,.2f}"),
            ("Credit Score", f"{user_data.get('credit_score', 600)} / 900"),
            ("ATM Daily Limit", f"Rs. {float(user_data.get('atm_daily_limit', 50000)):,.0f}"),
            ("Income Status", user_data.get("income_status", "N/A").replace("_", " ").title()),
            ("Income Bracket", user_data.get("income_bracket", "N/A").replace("_", " ").title()),
        ]
        pdf.set_font("Arial", "", 10)
        for label, value in details:
            pdf.set_fill_color(240, 245, 255)
            pdf.set_font("Arial", "B", 10)
            pdf.cell(60, 8, label, ln=False, border=1, fill=True)
            pdf.set_font("Arial", "", 10)
            pdf.cell(0, 8, f"  {value}", ln=True, border=1, fill=True)

    def _passbook_kyc_page(self, pdf, user_data, section_label=None):
        pdf.add_page()
        pdf.set_text_color(233, 69, 96)
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "KYC & PROFILE INFORMATION", ln=True)
        if section_label:
            pdf.set_font("Arial", "", 9)
            pdf.set_text_color(100, 100, 100)
            pdf.cell(0, 6, section_label, ln=True)
        pdf.set_text_color(50, 50, 50)
        pdf.ln(5)
        if user_data.get("is_minor"):
            items = [
                ("Guardian Name", user_data.get("guardian_name", "N/A")),
                ("Guardian Phone", user_data.get("guardian_phone", "N/A")),
                ("Relation", user_data.get("guardian_relation", "N/A").capitalize()),
                ("Surname Match", "Yes" if user_data.get("kyc_surname_match") else "No"),
                ("Address Match", "Yes" if user_data.get("kyc_address_match") else "No"),
            ]
        else:
            items = [
                ("Income Status", user_data.get("income_status", "N/A").replace("_", " ").title()),
                ("Income Bracket", user_data.get("income_bracket", "N/A").replace("_", " ").title()),
            ]
        pdf.set_font("Arial", "", 10)
        for label, value in items:
            pdf.set_fill_color(240, 248, 240)
            pdf.set_font("Arial", "B", 10)
            pdf.cell(60, 8, label, ln=False, border=1, fill=True)
            pdf.set_font("Arial", "", 10)
            pdf.cell(0, 8, f"  {value}", ln=True, border=1, fill=True)
        pdf.ln(10)
        pdf.set_font("Arial", "", 9)
        pdf.set_text_color(100, 100, 100)
        if user_data.get("is_minor"):
            pdf.multi_cell(0, 5,
                "This account is operated under guardian supervision. "
                "All transactions are monitored. No ATM card is issued for child accounts (age 10-13). "
                "For teen accounts (age 14-17), a daily ATM limit of Rs. 2,000 applies.")
        else:
            pdf.multi_cell(0, 5,
                "KYC verification completed at account opening. "
                "Please keep your contact details updated for seamless service.")

    def _passbook_welcome_page(self, pdf, user_data, section_label=None):
        pdf.add_page()
        pdf.set_text_color(15, 52, 96)
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "WELCOME TO YOUR ACCOUNT", ln=True)
        if section_label:
            pdf.set_font("Arial", "", 9)
            pdf.set_text_color(100, 100, 100)
            pdf.cell(0, 6, section_label, ln=True)
        pdf.ln(5)
        pdf.set_text_color(50, 50, 50)
        pdf.set_font("Arial", "", 11)
        welcome_text = (
            f"Dear {user_data['name'].split()[0]},\n\n"
            f"Welcome to {user_data['bank']}! Your {user_data['account_type'].title()} account "
            f"({user_data['account_no']}) has been successfully opened.\n\n"
            f"A welcome bonus of Rs. 5,000 has been credited to your account."
        )
        pdf.multi_cell(0, 7, welcome_text)
        pdf.ln(8)
        pdf.set_text_color(233, 69, 96)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, "Important Information", ln=True)
        pdf.set_text_color(50, 50, 50)
        pdf.set_font("Arial", "", 10)
        terms = [
            f"ATM Daily Limit: Rs. {float(user_data.get('atm_daily_limit', 50000)):,.0f}",
            "Free SMS alerts on all transactions",
            "24/7 Customer Care & Fraud Monitoring",
            "Passbook generated on: " + datetime.now().strftime("%d-%b-%Y %H:%M"),
            "Keep your PIN confidential. Never share it with anyone.",
            "Report lost/stolen cards immediately.",
        ]
        if user_data.get("is_minor"):
            age = user_data.get("age", 0)
            if age < 14:
                terms.append("Child Savings Account: Guardian-operated, no ATM card issued")
                terms.append("Higher savings interest rate applicable")
            else:
                terms.append("Teen Savings Account: Self-operated with Rs. 2,000/day ATM limit")
                terms.append("Savings goals feature available for you!")
        for t in terms:
            pdf.cell(0, 7, f"  *  {t}", ln=True)

    def _passbook_transaction_ledger(self, pdf, user_data, txns, section_label=None):
        pdf.add_page()
        pdf.set_text_color(233, 69, 96)
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "TRANSACTION LEDGER", ln=True)
        if section_label:
            pdf.set_font("Arial", "", 9)
            pdf.set_text_color(100, 100, 100)
            pdf.cell(0, 6, section_label, ln=True)
        pdf.set_text_color(50, 50, 50)
        pdf.set_font("Arial", "", 9)
        pdf.cell(0, 6, f"Account: {user_data['account_no']}  |  {user_data['name']}", ln=True)
        pdf.ln(2)
        if not txns:
            pdf.set_font("Arial", "", 10)
            pdf.cell(0, 10, "No transactions recorded yet. Your passbook is ready for entries.", ln=True)
            return
        headers = ["Date", "Particulars", "Withdraw (Rs)", "Deposit (Rs)", "Balance (Rs)"]
        col_w = [22, 58, 38, 38, 38]
        page_width = sum(col_w)
        rows_per_page = 25
        page_num = 1
        total_pages = (len(txns) + rows_per_page - 1) // rows_per_page
        for start in range(0, len(txns), rows_per_page):
            if start > 0:
                pdf.add_page()
            pdf.set_font("Arial", "B", 8)
            pdf.set_fill_color(15, 52, 96)
            pdf.set_text_color(255, 255, 255)
            for i, h in enumerate(headers):
                pdf.cell(col_w[i], 7, h, border=1, fill=True, align="C")
            pdf.ln()
            pdf.set_text_color(50, 50, 50)
            chunk = txns[start:start + rows_per_page]
            for t in chunk:
                txn_type = t.get("type", "").title()
                ts = str(t.get("timestamp", ""))[:10]
                amount = float(t.get("amount", 0))
                fee = float(t.get("fee", 0))
                bal_before = float(t.get("balance_before", 0))
                bal_after = float(t.get("balance_after", 0))
                withdraw = amount if txn_type.lower() == "withdraw" else 0
                deposit = amount if txn_type.lower() == "deposit" else 0
                notes = str(t.get("notes_given", "") or "")
                particulars = txn_type
                if fee > 0:
                    particulars += f" (fee: Rs.{fee:.0f})"
                if notes:
                    if len(particulars) > 25:
                        particulars = particulars[:25]
                    else:
                        particulars = notes[:25] if len(notes) < 25 else notes[:22] + "..."
                pdf.set_font("Arial", "", 8)
                if txn_type.lower() == "withdraw":
                    pdf.set_text_color(180, 40, 40)
                elif txn_type.lower() == "deposit":
                    pdf.set_text_color(30, 120, 30)
                else:
                    pdf.set_text_color(50, 50, 50)
                pdf.cell(col_w[0], 6, ts[:10], border=1, align="L")
                pdf.cell(col_w[1], 6, particulars[:28], border=1, align="L")
                pdf.cell(col_w[2], 6, f"{withdraw:>10,.0f}" if withdraw > 0 else "", border=1, align="R")
                pdf.cell(col_w[3], 6, f"{deposit:>10,.0f}" if deposit > 0 else "", border=1, align="R")
                pdf.set_text_color(0, 0, 0)
                pdf.cell(col_w[4], 6, f"{bal_after:>10,.0f}", border=1, align="R")
                pdf.ln()
            pdf.set_font("Arial", "", 7)
            pdf.set_text_color(120, 120, 120)
            pdf.cell(0, 6, f"Page {page_num} of {total_pages}  |  {user_data['account_no']}  |  {user_data['name']}", ln=True, align="C")
            page_num += 1

    def _passbook_charts_page(self, pdf, accounts, all_txns):
        pdf.add_page()
        pdf.set_text_color(233, 69, 96)
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "CONSOLIDATED CHARTS", ln=True)
        pdf.set_text_color(50, 50, 50)
        pdf.ln(3)
        pdf.set_font("Arial", "", 9)
        pdf.multi_cell(0, 5, "Visual summary across all your accounts.")
        pdf.ln(5)
        chart_dir = OUTPUTS_CHARTS
        chart_dir.mkdir(parents=True, exist_ok=True)
        primary = accounts[0]
        charts = []
        try:
            from src.data_visualization import DataVisualization
            viz = DataVisualization(self.da)
            gauge_path = viz.plot_gauge(
                primary.get("credit_score", 600),
                title="Credit Score",
                path=f"passbook_gauge_{primary['user_id']}.png"
            )
            if gauge_path:
                charts.append((gauge_path, "Credit Score Gauge"))
        except Exception:
            pass
        try:
            all_txn_dicts = []
            for uid, txn_list in all_txns.items():
                for t in txn_list:
                    all_txn_dicts.append({"timestamp": t.get("timestamp"), "amount": t.get("amount", 0), "type": t.get("type", "")})
            if all_txn_dicts:
                from src.data_visualization import DataVisualization
                viz = DataVisualization(self.da)
                heat_path = viz.plot_calendar_heatmap(
                    all_txn_dicts,
                    title=f"{primary['name']} Activity (All Accounts)",
                    path=f"passbook_heat_{primary['user_id']}.png"
                )
                if heat_path:
                    charts.append((heat_path, "Activity Heatmap"))
        except Exception:
            pass
        if charts:
            for chart_path, label in charts:
                if pdf.get_y() > 220:
                    pdf.add_page()
                pdf.set_font("Arial", "B", 10)
                pdf.set_text_color(15, 52, 96)
                pdf.cell(0, 8, label, ln=True)
                try:
                    pdf.image(str(chart_path), x=20, w=160)
                    pdf.ln(3)
                except Exception:
                    pdf.set_font("Arial", "", 8)
                    pdf.set_text_color(150, 150, 150)
                    pdf.cell(0, 6, "(Chart unavailable)", ln=True)
        else:
            pdf.set_font("Arial", "", 10)
            pdf.set_text_color(150, 150, 150)
            pdf.cell(0, 10, "Charts will appear here once you have transaction history.", ln=True)

    def _passbook_ml_insights(self, pdf, accounts):
        pdf.add_page()
        pdf.set_text_color(233, 69, 96)
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "ML-POWERED INSIGHTS", ln=True)
        pdf.set_text_color(50, 50, 50)
        pdf.ln(3)
        pdf.set_font("Arial", "", 9)
        pdf.multi_cell(0, 5, "AI-driven analysis across all your accounts. These predictions help you make informed financial decisions.")
        pdf.ln(5)
        primary = accounts[0]
        insights = []
        try:
            from src.models.credit_scorer import CreditScorer
            cs = CreditScorer()
            score = cs.rule_based_score(primary)
            insights.append(("Credit Score Analysis", f"Your rule-based score: {score}/900. "
                f"Factors: balance={float(primary.get('balance',0)):,.0f}, "
                f"age_group={primary.get('age_group','N/A')}"))
        except Exception:
            pass
        try:
            from src.models.churn_predictor import ChurnPredictor
            cp = ChurnPredictor()
            churn = cp.rule_based_risk(primary)
            risk_map = {0: "Low", 1: "Medium", 2: "High"}
            risk_label = risk_map.get(churn, "Unknown")
            insights.append(("Churn Risk Assessment", f"Risk level: {risk_label}. "
                f"{'Your account is active and healthy.' if risk_label == 'Low' else 'Consider transacting more to stay active.'}"))
        except Exception:
            pass
        try:
            from src.models.spending_forecaster import SpendingForecaster
            sf = SpendingForecaster()
            forecast = sf.predict(primary["user_id"])
            if forecast:
                insights.append(("Spending Forecast (Next 30 Days)",
                    f"Predicted: Rs. {float(forecast):,.0f}. "
                    f"{'This is within normal range.' if float(forecast) < float(primary.get('balance', 5000)) else 'Consider budgeting.'}"))
        except Exception:
            pass
        try:
            from src.models.investment_recommender import InvestmentRecommender
            ir = InvestmentRecommender()
            recs = ir.recommend(primary)
            if recs:
                prod_names = [r["product"] for r in recs[:3]]
                insights.append(("Investment Suggestions",
                    f"Top picks: {', '.join(prod_names)}. "
                    f"Allocation tailored to your age ({primary.get('age','?')}) and income."))
        except Exception:
            pass
        if not insights:
            pdf.set_font("Arial", "", 10)
            pdf.set_text_color(150, 150, 150)
            pdf.cell(0, 10, "ML insights will be available after models are trained.", ln=True)
            return
        for title, detail in insights:
            pdf.set_fill_color(245, 247, 255)
            pdf.set_text_color(15, 52, 96)
            pdf.set_font("Arial", "B", 11)
            pdf.cell(0, 8, title, ln=True, fill=True)
            pdf.ln(1)
            pdf.set_text_color(50, 50, 50)
            pdf.set_font("Arial", "", 9)
            pdf.multi_cell(0, 5, detail)
            pdf.ln(4)

    def generate_account_summary_card(self, user_data, auto_open=True):
        name_slug = user_data["name"].replace(" ", "_")[:20]
        filename = f"summary_{user_data['user_id']}_{name_slug}.pdf"
        path = self.report_dir / filename
        pdf = FPDF(orientation="P", unit="mm", format="A5")
        pdf.add_page()
        pdf.set_fill_color(15, 52, 96)
        pdf.rect(0, 0, 148, 210, "F")
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Arial", "B", 14)
        pdf.ln(8)
        pdf.cell(0, 8, "ACCOUNT SUMMARY CARD", ln=True, align="C")
        pdf.ln(2)
        pdf.set_font("Arial", "", 8)
        pdf.set_text_color(200, 200, 200)
        pdf.cell(0, 5, user_data["bank"], ln=True, align="C")
        pdf.ln(5)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, user_data["name"], ln=True, align="C")
        pdf.ln(5)
        lines = [
            ("Account No", user_data["account_no"]),
            ("Card", self._mask_card(user_data["card_no"])),
            ("Type", user_data["account_type"].title()),
            ("Balance", f"Rs. {float(user_data['balance']):,.0f}"),
            ("Credit Score", f"{user_data.get('credit_score', 600)}/900"),
            ("ATM Limit", f"Rs. {float(user_data.get('atm_daily_limit', 50000)):,.0f}"),
            ("Phone", str(user_data.get("phone", "N/A"))),
            ("Email", user_data.get("email", "N/A")),
        ]
        pdf.set_font("Arial", "", 9)
        for label, value in lines:
            pdf.set_text_color(180, 210, 240)
            pdf.cell(45, 7, label, ln=False)
            pdf.set_text_color(255, 255, 255)
            pdf.cell(0, 7, value, ln=True)
        pdf.ln(8)
        pdf.set_text_color(150, 150, 150)
        pdf.set_font("Arial", "", 6)
        pdf.cell(0, 4, f"Generated: {datetime.now().strftime('%d-%b-%Y %H:%M')}", ln=True, align="C")
        pdf.cell(0, 4, "Keep this card safe. Do not share with anyone.", ln=True, align="C")
        pdf.output(str(path))
        console.print(f"[green]Account summary card saved: {path}[/green]")
        if auto_open:
            try:
                os.startfile(str(path))
                console.print("[dim]Auto-opening summary card...[/dim]")
            except Exception:
                pass
        return path

    def export_account_data_json(self, user_data, auto_open=True):
        import json
        name_slug = user_data["name"].replace(" ", "_")[:20]
        filename = f"account_data_{user_data['user_id']}_{name_slug}.json"
        path = self.report_dir / filename
        conn = db.get_connection("ecosystem")
        export = {
            "export_date": datetime.now().isoformat(),
            "account": {
                "name": user_data["name"],
                "account_no": user_data["account_no"],
                "card_no": self._mask_card(user_data["card_no"]),
                "bank": user_data["bank"],
                "account_type": user_data["account_type"],
                "age_group": user_data.get("age_group", ""),
                "is_minor": bool(user_data.get("is_minor", False)),
                "phone": user_data.get("phone", ""),
                "email": user_data.get("email", ""),
                "balance": float(user_data.get("balance", 0)),
                "credit_score": user_data.get("credit_score", 600),
                "atm_daily_limit": float(user_data.get("atm_daily_limit", 50000)),
                "created_at": str(user_data.get("created_at", "")),
            },
        }
        if user_data.get("is_minor"):
            export["account"]["guardian_name"] = user_data.get("guardian_name", "")
            export["account"]["guardian_phone"] = user_data.get("guardian_phone", "")
            export["account"]["guardian_relation"] = user_data.get("guardian_relation", "")
        txn_rows = conn.execute(
            "SELECT timestamp, type, amount, fee, balance_before, balance_after, channel, notes_given FROM transactions WHERE user_id = ? ORDER BY timestamp",
            (user_data["user_id"],)
        ).fetchall()
        export["transactions"] = [dict(r) for r in txn_rows]
        for t in export["transactions"]:
            for k, v in t.items():
                if isinstance(v, (float, int)):
                    t[k] = float(v)
                elif isinstance(v, bytes):
                    t[k] = str(v)
        with open(str(path), "w", encoding="utf-8") as f:
            json.dump(export, f, indent=2, default=str)
        console.print(f"[green]Account data JSON saved: {path}[/green]")
        if auto_open:
            try:
                os.startfile(str(path))
            except Exception:
                pass
        return path

    def _mask_card(self, card):
        return card[:4] + "-XXXX-XXXX-" + card[-4:]

    def generate_all_passbook_assets(self, user_data, txns=None, prompt_open=True):
        paths = []
        paths.append(self.generate_passbook(user_data, txns, prompt_open=prompt_open))
        paths.append(self.generate_account_summary_card(user_data, auto_open=False))
        paths.append(self.export_account_data_json(user_data, auto_open=False))
        console.print(f"[green]All passbook assets generated ({len(paths)} files)[/green]")
        return paths
