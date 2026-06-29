import sqlite3
import random
import json
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt, Confirm
from rich import box
from src.utils import (
    ECOSYSTEM_DB, hash_pin, validate_name, validate_phone,
    validate_email, validate_age, get_age_group, generate_account_no,
    generate_card_no, income_bracket_options, get_scenario_timestamp,
    ensure_dirs
)
from src.bank_attributes import get_bank_attrs, get_bank_prefix
from src.data_analysis import DataAnalysis
from src.data.db_manager import db

console = Console()

class UserManager:
    def __init__(self):
        ensure_dirs()
        self._init_db()

    @property
    def conn(self):
        return db.get_connection("ecosystem")

    def _init_db(self):
        c = self.conn.cursor()
        c.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL, phone TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL, age INTEGER NOT NULL,
                age_group TEXT, is_minor BOOLEAN DEFAULT 0,
                guardian_name TEXT, guardian_phone TEXT,
                guardian_relation TEXT, guardian_aadhaar_last4 TEXT,
                child_aadhaar_last4 TEXT, kyc_address_match BOOLEAN,
                kyc_surname_match BOOLEAN, income_status TEXT,
                income_bracket TEXT, account_no TEXT UNIQUE NOT NULL,
                card_no TEXT UNIQUE NOT NULL, bank TEXT NOT NULL,
                account_type TEXT, pin_hash TEXT NOT NULL,
                balance REAL DEFAULT 5000, atm_daily_limit REAL DEFAULT 50000,
                atm_used_today REAL DEFAULT 0, credit_score INTEGER DEFAULT 600,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP, is_active BOOLEAN DEFAULT 1,
                preferences TEXT DEFAULT '{}'
            );
            CREATE TABLE IF NOT EXISTS transactions (
                txn_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER REFERENCES users(user_id),
                type TEXT NOT NULL, amount REAL, fee REAL DEFAULT 0,
                balance_before REAL, balance_after REAL,
                channel TEXT DEFAULT 'atm', target_account TEXT,
                target_bank TEXT, bank TEXT, notes_given TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_fraud BOOLEAN DEFAULT 0, fraud_score REAL
            );
            CREATE TABLE IF NOT EXISTS loan_applications (
                loan_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER REFERENCES users(user_id),
                loan_type TEXT, amount_requested REAL,
                amount_approved REAL, interest_rate REAL,
                tenure_months INTEGER, status TEXT,
                risk_score REAL, predicted_default REAL,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                decision_at TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS fraud_flags (
                flag_id INTEGER PRIMARY KEY AUTOINCREMENT,
                txn_id INTEGER REFERENCES transactions(txn_id),
                user_id INTEGER REFERENCES users(user_id),
                anomaly_score REAL, flagged_by TEXT,
                is_confirmed BOOLEAN DEFAULT 0,
                scenario_exported BOOLEAN DEFAULT 0,
                flagged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS credit_history (
                entry_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER REFERENCES users(user_id),
                event_type TEXT, amount REAL,
                score_impact REAL,
                recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS user_sessions (
                session_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER REFERENCES users(user_id),
                login_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                logout_at TIMESTAMP, actions_count INTEGER DEFAULT 0,
                scenario_exported BOOLEAN DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS savings_goals (
                goal_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER REFERENCES users(user_id),
                goal_name TEXT, target_amount REAL,
                current_amount REAL DEFAULT 0, deadline TEXT,
                is_completed BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS feedback (
                feedback_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER REFERENCES users(user_id),
                rating INTEGER, comments TEXT, category TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        self.conn.commit()

    def register(self):
        console.print(Panel("[bold yellow]📝 New Account Registration[/bold yellow]", border_style="yellow"))
        name = self._prompt_name()
        phone = self._prompt_phone()
        email = self._prompt_email()
        age = self._prompt_age()
        age_group, is_minor = get_age_group(age)
        income_status, income_bracket = self._prompt_income()
        guardian_data = {}
        if is_minor:
            guardian_data = self._prompt_guardian(age)
        from src.ui_helpers import BankSelector
        da = DataAnalysis()
        selector = BankSelector(da.get_banks())
        if is_minor:
            console.print("[cyan]Now choose a bank. Look for banks with good minor account features![/cyan]")
        bank = selector.select("Choose your bank")
        if not bank:
            console.print("[red]Bank selection cancelled[/red]")
            return None
        bank_attrs = get_bank_attrs(bank)
        prefix = get_bank_prefix(bank)
        account_no = generate_account_no(prefix)
        card_no = generate_card_no()
        if is_minor:
            acct_type = "child_savings" if age < 14 else "teen_savings"
            atm_limit = 0 if age < 14 else bank_attrs.get("minor_limit", 2000)
        else:
            acct_type = "savings"
            atm_limit = bank_attrs.get("atm_daily_limit", 50000)
        console.print("[yellow]Set your 4-digit ATM PIN[/yellow]")
        pin = self._prompt_pin()
        pin_hash = hash_pin(pin)
        user_data = {
            "name": name, "phone": phone, "email": email,
            "age": age, "age_group": age_group,
            "is_minor": 1 if is_minor else 0,
            "guardian_name": guardian_data.get("name", ""),
            "guardian_phone": guardian_data.get("phone", ""),
            "guardian_relation": guardian_data.get("relation", ""),
            "guardian_aadhaar_last4": guardian_data.get("guardian_aadhaar", ""),
            "child_aadhaar_last4": guardian_data.get("child_aadhaar", ""),
            "kyc_address_match": guardian_data.get("address_match"),
            "kyc_surname_match": guardian_data.get("surname_match"),
            "income_status": income_status,
            "income_bracket": income_bracket,
            "account_no": account_no,
            "card_no": card_no,
            "bank": bank,
            "account_type": acct_type,
            "pin_hash": pin_hash,
            "balance": 5000,
            "atm_daily_limit": atm_limit,
            "credit_score": 600 if not is_minor else 650,
        }
        c = self.conn.cursor()
        existing_email = c.execute("SELECT user_id FROM users WHERE email = ?", (email,)).fetchone()
        existing_phone = c.execute("SELECT user_id FROM users WHERE phone = ?", (phone,)).fetchone()
        if existing_email:
            console.print("[red]This email is already registered. Try logging in instead.[/red]")
            if Confirm.ask("[yellow]Go to login?[/yellow]", default=True):
                return self.login()
            return None
        if existing_phone:
            console.print("[red]This phone number is already registered. Try logging in instead.[/red]")
            if Confirm.ask("[yellow]Go to login?[/yellow]", default=True):
                return self.login()
            return None
        try:
            c.execute("""INSERT INTO users
                (name,phone,email,age,age_group,is_minor,
                 guardian_name,guardian_phone,guardian_relation,
                 guardian_aadhaar_last4,child_aadhaar_last4,
                 kyc_address_match,kyc_surname_match,
                 income_status,income_bracket,
                 account_no,card_no,bank,account_type,pin_hash,
                 balance,atm_daily_limit,credit_score)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                       (user_data["name"], user_data["phone"], user_data["email"],
                        user_data["age"], user_data["age_group"], user_data["is_minor"],
                        user_data["guardian_name"], user_data["guardian_phone"],
                        user_data["guardian_relation"],
                        user_data["guardian_aadhaar_last4"],
                        user_data["child_aadhaar_last4"],
                        user_data["kyc_address_match"],
                        user_data["kyc_surname_match"],
                        user_data["income_status"], user_data["income_bracket"],
                        user_data["account_no"], user_data["card_no"],
                        user_data["bank"], user_data["account_type"],
                        user_data["pin_hash"], user_data["balance"],
                        user_data["atm_daily_limit"], user_data["credit_score"]))
            self.conn.commit()
            user_id = c.lastrowid
            user_data["user_id"] = user_id
            console.print(Panel(f"""[green]✅ Account created successfully![/green]
Account No: [bold]{account_no}[/bold]
Card No:    [bold]{card_no}[/bold]
Bank:       {bank}
Type:       {acct_type.title()}
Balance:    ₹5,000.00 (Welcome bonus!)""", border_style="green"))
            self._export_scenario("NEW_USER_MILESTONE")
            try:
                from src.report_generator import ReportGenerator
                rg = ReportGenerator()
                path = rg.generate_passbook(user_data, prompt_open=True)
                console.print(f"[green]Digital passbook: {path}[/green]")
                if Confirm.ask("[yellow]Would you like to download your Account Summary Card & Data File?[/yellow]", default=False):
                    rg.generate_account_summary_card(user_data, auto_open=True)
                    rg.export_account_data_json(user_data, auto_open=False)
            except Exception as e:
                console.print(f"[dim]Passbook generation: {e}[/dim]")
            return user_data
        except sqlite3.IntegrityError as e:
            console.print(f"[red]Registration error: {e}[/red]")
            return None

    def _lookup_user(self, identifier):
        c = self.conn.cursor()
        if "@" in identifier:
            c.execute("SELECT * FROM users WHERE email = ?", (identifier.strip(),))
        elif identifier.isdigit() and len(identifier) == 10:
            c.execute("SELECT * FROM users WHERE phone = ?", (identifier.strip(),))
        elif identifier.isdigit() and len(identifier) < 10:
            c.execute("SELECT * FROM users WHERE account_no LIKE ?", (f"%{identifier.strip()}",))
        else:
            c.execute("SELECT * FROM users WHERE card_no = ?", (identifier.strip(),))
        row = c.fetchone()
        if row:
            col_names = [d[0] for d in c.description]
            d = dict(zip(col_names, row))
            d["is_minor"] = bool(d["is_minor"])
            return d
        return None

    def _mask_card(self, card):
        return card[:4] + "-XXXX-XXXX-" + card[-4:]

    def _mask_account(self, acct):
        if len(acct) <= 4:
            return acct
        prefix = acct[:3]
        suffix = acct[-2:]
        return prefix + "****" + suffix

    def _login_user(self, user, c):
        pin = Prompt.ask("[yellow]Enter PIN[/yellow]", password=True)
        if hash_pin(pin) != user["pin_hash"]:
            console.print("[red]Incorrect PIN[/red]")
            return None
        user["is_minor"] = bool(user["is_minor"])
        self._log_session(user["user_id"])
        console.print(f"[green]Welcome back, {user['name']}![/green]")
        return user

    def login(self, method=None):
        console.print(Panel("[bold yellow]Login to Your Account[/bold yellow]", border_style="yellow"))
        c = self.conn.cursor()
        if not method:
            method = Prompt.ask("[yellow]Login via[/yellow]", choices=["card", "email", "phone", "account"], default="card")
        try:
            if method == "account":
                acct = Prompt.ask("[yellow]Account Number[/yellow]")
                if not acct:
                    return None
                c.execute("SELECT * FROM users WHERE account_no = ?", (acct.strip(),))
                user = c.fetchone()
                if not user:
                    console.print("[red]No account found with that number[/red]")
                    return None
            elif method == "card":
                card = Prompt.ask("[yellow]Card Number (XXXX-XXXX-XXXX-XXXX)[/yellow]")
                if not card:
                    return None
                c.execute("SELECT * FROM users WHERE card_no = ?", (card.strip(),))
                user = c.fetchone()
                if not user:
                    console.print("[red]Card not found[/red]")
                    return None
            elif method == "email":
                email = Prompt.ask("[yellow]Registered Email[/yellow]")
                c.execute("SELECT * FROM users WHERE email = ?", (email.strip(),))
                user = c.fetchone()
                if not user:
                    console.print("[red]No account found with that email[/red]")
                    return None
            elif method == "phone":
                phone = Prompt.ask("[yellow]Registered Phone (10 digits)[/yellow]")
                c.execute("SELECT * FROM users WHERE phone = ?", (phone.strip(),))
                user = c.fetchone()
                if not user:
                    console.print("[red]No account found with that phone[/red]")
                    return None
            col_names = [d[0] for d in c.description]
            user_dict = dict(zip(col_names, user))
            return self._login_user(user_dict, c)
        except Exception as e:
            console.print(f"[red]Login error: {e}[/red]")
            return None

    def forgot_card(self):
        console.print(Panel("[bold yellow]Forgot Card / Account Number[/bold yellow]", border_style="yellow"))
        console.print("[dim]Enter your registered email or phone to retrieve your account details.[/dim]")
        lookup = Prompt.ask("[yellow]Enter your Email or Phone[/yellow]")
        user = self._lookup_user(lookup)
        if not user:
            console.print("[red]No account found with that information[/red]")
            return None
        console.print(f"[green]Account found: {user['name']}[/green]")
        console.print(f"[yellow]Card:    [bold]{self._mask_card(user['card_no'])}[/bold][/yellow]")
        console.print(f"[yellow]Account: [bold]{self._mask_account(user['account_no'])}[/bold][/yellow]")
        console.print(f"[dim]Bank: {user['bank']} | {user['account_type'].title()}[/dim]")
        console.print("[dim]Now log in with your PIN (no card needed).[/dim]")
        if Confirm.ask("[yellow]Login now?[/yellow]", default=True):
            return self._login_user(user, self.conn.cursor())
        return None

    def forgot_pin(self):
        console.print(Panel("[bold yellow]Forgot PIN[/bold yellow]", border_style="yellow"))
        console.print("[dim]Verify your identity to reset your PIN. Enter any one of the following:[/dim]")
        console.print("[dim]  - Card number[/dim]")
        console.print("[dim]  - Account number[/dim]")
        console.print("[dim]  - Registered email[/dim]")
        console.print("[dim]  - Registered phone[/dim]")
        lookup = Prompt.ask("[yellow]Enter any identifier[/yellow]")
        user = self._lookup_user(lookup)
        if not user:
            console.print("[red]No account found[/red]")
            return None
        console.print(f"[green]Account found: {user['name']}[/green]")
        console.print(f"[dim]Card: {self._mask_card(user['card_no'])} | Account: {self._mask_account(user['account_no'])}[/dim]")
        console.print("[yellow]Step 1: Confirm your identity[/yellow]")
        name_check = Prompt.ask("[yellow]Enter your full name on the account[/yellow]")
        if name_check.strip().upper() != user["name"].upper():
            console.print("[red]Name does not match[/red]")
            return None
        card_last4 = Prompt.ask("[yellow]Enter the last 4 digits of your card[/yellow]")
        if card_last4.strip() != user["card_no"][-4:]:
            console.print("[red]Last 4 digits do not match[/red]")
            return None
        console.print("[green]Identity verified![/green]")
        new_pin = Prompt.ask("[yellow]Enter new 4-digit PIN[/yellow]", password=True)
        if not (new_pin.isdigit() and len(new_pin) == 4):
            console.print("[red]PIN must be exactly 4 digits[/red]")
            return None
        confirm_pin = Prompt.ask("[yellow]Confirm new PIN[/yellow]", password=True)
        if new_pin != confirm_pin:
            console.print("[red]PINs do not match[/red]")
            return None
        c = self.conn.cursor()
        c.execute("UPDATE users SET pin_hash = ? WHERE user_id = ?", (hash_pin(new_pin), user["user_id"]))
        self.conn.commit()
        console.print("[green]PIN reset successfully![/green]")
        if Confirm.ask("[yellow]Login now?[/yellow]", default=True):
            return self._login_user(user, c)
        return None

    def recover_full_access(self):
        console.print(Panel("[bold yellow]Recover Full Access (KYC Verification)[/bold yellow]", border_style="yellow"))
        console.print("[dim]We need multiple details to verify your identity. All fields are required.[/dim]")
        email = Prompt.ask("[yellow]Step 1: Registered Email[/yellow]")
        phone = Prompt.ask("[yellow]Step 2: Registered Phone (10 digits)[/yellow]")
        name = Prompt.ask("[yellow]Step 3: Full Name on Account[/yellow]")
        age_str = Prompt.ask("[yellow]Step 4: Your Age[/yellow]")
        c = self.conn.cursor()
        c.execute("""
            SELECT * FROM users
            WHERE email = ? AND phone = ? AND LOWER(name) = LOWER(?) AND age = ?
        """, (email.strip(), phone.strip(), name.strip(), age_str.strip()))
        row = c.fetchone()
        if not row:
            console.print("[red]Information does not match our records. Please try again or contact support.[/red]")
            return None
        col_names = [d[0] for d in c.description]
        user = dict(zip(col_names, row))
        user["is_minor"] = bool(user["is_minor"])
        console.print(f"[green]Identity verified! Welcome, {user['name']}.[/green]")
        console.print(f"[yellow]Card:    [bold]{self._mask_card(user['card_no'])}[/bold][/yellow]")
        console.print(f"[yellow]Account: [bold]{self._mask_account(user['account_no'])}[/bold][/yellow]")
        console.print(f"[yellow]Bank:    [bold]{user['bank']}[/bold][/yellow]")
        console.print(f"[yellow]Balance: [bold]Rs.{user['balance']:,.0f}[/bold][/yellow]")
        if Confirm.ask("[yellow]Reset your PIN and login?[/yellow]", default=True):
            new_pin = Prompt.ask("[yellow]Enter new 4-digit PIN[/yellow]", password=True)
            if not (new_pin.isdigit() and len(new_pin) == 4):
                console.print("[red]PIN must be exactly 4 digits[/red]")
                return None
            confirm_pin = Prompt.ask("[yellow]Confirm new PIN[/yellow]", password=True)
            if new_pin != confirm_pin:
                console.print("[red]PINs do not match[/red]")
                return None
            c.execute("UPDATE users SET pin_hash = ? WHERE user_id = ?", (hash_pin(new_pin), user["user_id"]))
            self.conn.commit()
            console.print("[green]PIN reset! Logging you in...[/green]")
            return self._login_user(user, c)
        if Confirm.ask("[yellow]Login with existing PIN?[/yellow]", default=True):
            return self._login_user(user, c)
        return None

    def login_or_register(self):
        console.print("[yellow]1. Login  |  2. Register  |  3. Forgot Card  |  4. Forgot PIN  |  5. Recover Access  |  6. Exit[/yellow]")
        choice = Prompt.ask("Choose", choices=["1", "2", "3", "4", "5", "6"])
        if choice == "1":
            return self.login(method=None)
        elif choice == "2":
            return self.register()
        elif choice == "3":
            return self.forgot_card()
        elif choice == "4":
            return self.forgot_pin()
        elif choice == "5":
            return self.recover_full_access()
        return None

    def update_user(self, user_id, **kwargs):
        fields = []
        values = []
        for k, v in kwargs.items():
            if k in ("name", "phone", "email", "preferences"):
                fields.append(f"{k} = ?")
                values.append(v)
        if not fields:
            return
        values.append(user_id)
        c = self.conn.cursor()
        c.execute(f"UPDATE users SET {', '.join(fields)} WHERE user_id = ?", values)
        self.conn.commit()

    def record_transaction(self, user_id, txn_type, amount, fee=0, balance_before=0,
                           balance_after=0, channel="atm", target_account="",
                           target_bank="", bank="", notes=""):
        c = self.conn.cursor()
        c.execute("""INSERT INTO transactions
            (user_id,type,amount,fee,balance_before,balance_after,
             channel,target_account,target_bank,bank,notes_given)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                  (user_id, txn_type, amount, fee, balance_before,
                   balance_after, channel, target_account, target_bank, bank, notes))
        self.conn.commit()
        c.execute("UPDATE users SET last_active = CURRENT_TIMESTAMP WHERE user_id = ?", (user_id,))
        self.conn.commit()
        user = self.get_user(user_id)
        total_txns = c.execute("SELECT COUNT(*) FROM transactions WHERE user_id = ?",
                               (user_id,)).fetchone()[0]
        if total_txns > 0 and total_txns % 50 == 0:
            self._export_scenario("THRESHOLD_REACHED")

    def record_credit_event(self, user_id, event_type, amount, impact):
        c = self.conn.cursor()
        c.execute("INSERT INTO credit_history (user_id,event_type,amount,score_impact) VALUES (?,?,?,?)",
                  (user_id, event_type, amount, impact))
        self.conn.commit()
        c.execute("UPDATE users SET credit_score = credit_score + ? WHERE user_id = ?",
                  (impact, user_id))
        self.conn.commit()

    def update_balance(self, user_id, new_balance):
        c = self.conn.cursor()
        c.execute("UPDATE users SET balance = ? WHERE user_id = ?", (new_balance, user_id))
        self.conn.commit()

    def update_atm_usage(self, user_id, amount):
        c = self.conn.cursor()
        c.execute("UPDATE users SET atm_used_today = atm_used_today + ? WHERE user_id = ?",
                  (amount, user_id))
        self.conn.commit()
        c.execute("SELECT atm_used_today, atm_daily_limit FROM users WHERE user_id = ?",
                  (user_id,))
        used, limit = c.fetchone()
        if used >= limit * 0.9:
            console.print(f"[yellow]⚠️  You've used {used:.0f}/{limit:.0f} of today's ATM limit[/yellow]")

    def reset_atm_usage(self):
        c = self.conn.cursor()
        c.execute("UPDATE users SET atm_used_today = 0")
        self.conn.commit()

    def get_user(self, user_id):
        c = self.conn.cursor()
        c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = c.fetchone()
        if row:
            col_names = [d[0] for d in c.description]
            d = dict(zip(col_names, row))
            d["is_minor"] = bool(d["is_minor"])
            return d
        return None

    def get_transactions(self, user_id, limit=20):
        c = self.conn.cursor()
        c.execute("SELECT * FROM transactions WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?",
                  (user_id, limit))
        cols = [d[0] for d in c.description]
        return [dict(zip(cols, row)) for row in c.fetchall()]

    def change_pin(self, user_id):
        user = self.get_user(user_id)
        if not user:
            return False
        old = Prompt.ask("[yellow]Enter current PIN[/yellow]", password=True)
        if hash_pin(old) != user["pin_hash"]:
            console.print("[red]Incorrect current PIN[/red]")
            return False
        new = self._prompt_pin()
        confirm = Prompt.ask("[yellow]Confirm new PIN[/yellow]", password=True)
        if new != confirm:
            console.print("[red]PINs do not match[/red]")
            return False
        c = self.conn.cursor()
        c.execute("UPDATE users SET pin_hash = ? WHERE user_id = ?",
                  (hash_pin(new), user_id))
        self.conn.commit()
        console.print("[green]✅ PIN changed successfully![/green]")
        return True

    def _prompt_name(self):
        while True:
            raw = Prompt.ask("[yellow]Full Name (First Last)[/yellow]")
            ok, result = validate_name(raw)
            if ok:
                return result
            console.print(f"[red]{result}[/red]")

    def _prompt_phone(self):
        while True:
            raw = Prompt.ask("[yellow]Phone Number (10 digits)[/yellow]")
            ok, result = validate_phone(raw)
            if ok:
                return result
            console.print(f"[red]{result}[/red]")

    def _prompt_email(self):
        while True:
            raw = Prompt.ask("[yellow]Email Address[/yellow]")
            ok, result = validate_email(raw)
            if ok:
                return result
            console.print(f"[red]{result}[/red]")

    def _prompt_age(self):
        while True:
            raw = Prompt.ask("[yellow]Age[/yellow]")
            ok, result = validate_age(raw)
            if ok:
                age_group, _ = get_age_group(result)
                console.print(f"[dim]Category: {age_group}[/dim]")
                return result
            console.print(f"[red]{result}[/red]")

    def _prompt_pin(self):
        while True:
            pin = Prompt.ask("[yellow]Enter 4-digit PIN[/yellow]", password=True)
            if pin.isdigit() and len(pin) == 4:
                return pin
            console.print("[red]PIN must be exactly 4 digits[/red]")

    def _prompt_income(self):
        console.print("[cyan]Income Status:[/cyan]")
        opts = income_bracket_options()
        for i, (val, label) in enumerate(opts, 1):
            console.print(f"  {i}. {label}")
        while True:
            choice = Prompt.ask("[yellow]Select[/yellow]", default="1")
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(opts):
                    val, label = opts[idx]
                    status = "earning" if val.startswith("earning") else "not_earning"
                    return status, val
            except:
                pass
            console.print("[red]Invalid choice[/red]")

    def _prompt_guardian(self, child_age):
        console.print(Panel("[bold cyan]🧒 Minor Account — Guardian Details Required[/bold cyan]", border_style="cyan"))
        console.print("[dim]As per RBI guidelines, a guardian is required for minors.[/dim]")
        guardian_name = self._prompt_name()
        guardian_phone = self._prompt_phone()
        relation = Prompt.ask("[yellow]Relationship to child[/yellow]",
                              choices=["Father", "Mother", "Legal Guardian"])
        child_aadhaar = Prompt.ask("[yellow]Child's Aadhaar (last 4 digits)[/yellow]",
                                   default="1234")
        guardian_aadhaar = Prompt.ask("[yellow]Guardian's Aadhaar (last 4 digits)[/yellow]",
                                      default="5678")
        console.print("[cyan]Verifying KYC...[/cyan]")
        surname_match = guardian_name.split()[-1].upper() == Prompt.ask(
            "[yellow]Child's surname[/yellow]", default="Unknown").strip().upper()
        address_match = Confirm.ask(
            "[yellow]Does the child's address match guardian's address?[/yellow]", default=True)
        if address_match and surname_match:
            console.print("[green]✅ KYC Verified — Address & Surname match![/green]")
        elif address_match:
            console.print("[yellow]⚠️  Address matches but surname differs. Additional verification may be needed.[/yellow]")
        else:
            console.print("[yellow]⚠️  Address mismatch detected. Please provide address proof.[/yellow]")
        return {
            "name": guardian_name, "phone": guardian_phone,
            "relation": relation, "child_aadhaar": child_aadhaar,
            "guardian_aadhaar": guardian_aadhaar,
            "surname_match": surname_match, "address_match": address_match,
        }

    def _log_session(self, user_id):
        c = self.conn.cursor()
        c.execute("INSERT INTO user_sessions (user_id) VALUES (?)", (user_id,))
        self.conn.commit()

    def end_session(self, user_id):
        c = self.conn.cursor()
        c.execute("""UPDATE user_sessions SET logout_at = CURRENT_TIMESTAMP
            WHERE user_id = ? AND logout_at IS NULL""", (user_id,))
        self.conn.commit()
        self._export_scenario("SESSION_END")

    def _export_scenario(self, scenario):
        from src.data_generator import DataGenerator
        try:
            dg = DataGenerator()
            dg.export_scenario(scenario)
        except:
            pass

    def get_user_count(self):
        return self.conn.cursor().execute("SELECT COUNT(*) FROM users").fetchone()[0]

    def close(self):
        pass
