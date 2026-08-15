import sqlite3
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt, Confirm
from rich import box
from banking_core.utils import (
    hash_pin, validate_name, validate_phone,
    validate_email, validate_age, get_age_group, income_bracket_options,
)
from banking_core.bank_attributes import get_bank_attrs, get_bank_prefix
from banking_core.data_analysis import DataAnalysis
from banking_core.services import UserService

console = Console()


class UserManager:
    """Rich CLI presentation layer over banking_core.services.UserService."""

    def __init__(self):
        self.service = UserService()

    @property
    def conn(self):
        return self.service.conn

    # ── Registration ──────────────────────────────────────────

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
        from atm_cli.ui_helpers import BankSelector
        da = DataAnalysis()
        selector = BankSelector(da.get_banks())
        if is_minor:
            console.print("[cyan]Now choose a bank. Look for banks with good minor account features![/cyan]")
        bank = selector.select("Choose your bank")
        if not bank:
            console.print("[red]Bank selection cancelled[/red]")
            return None
        console.print("[yellow]Set your 4-digit ATM PIN[/yellow]")
        pin = self._prompt_pin()

        result = self.service.register({
            "name": name, "phone": phone, "email": email, "age": age,
            "income_status": income_status, "income_bracket": income_bracket,
            "guardian": guardian_data, "bank": bank, "pin": pin,
        })
        if isinstance(result, str):
            console.print(f"[red]{result}[/red]")
            if Confirm.ask("[yellow]Go to login?[/yellow]", default=True):
                return self.login()
            return None
        if result is None:
            console.print("[red]Registration failed[/red]")
            return None

        user_data = result
        console.print(Panel(f"""[green]✅ Account created successfully![/green]
Account No: [bold]{user_data['account_no']}[/bold]
Card No:    [bold]{user_data['card_no']}[/bold]
Bank:       {user_data['bank']}
Type:       {user_data['account_type'].title()}
Balance:    ₹5,000.00 (Welcome bonus!)""", border_style="green"))
        self._export_scenario("NEW_USER_MILESTONE")
        try:
            from banking_core.report_generator import ReportGenerator
            rg = ReportGenerator()
            path = rg.generate_passbook(user_data, prompt_open=True)
            console.print(f"[green]Digital passbook: {path}[/green]")
            if Confirm.ask("[yellow]Would you like to download your Account Summary Card & Data File?[/yellow]", default=False):
                rg.generate_account_summary_card(user_data, auto_open=True)
                rg.export_account_data_json(user_data, auto_open=False)
        except Exception as e:
            console.print(f"[dim]Passbook generation: {e}[/dim]")
        return user_data

    # ── Login / recovery ──────────────────────────────────────

    def _mask_card(self, card):
        return card[:4] + "-XXXX-XXXX-" + card[-4:]

    def _mask_account(self, acct):
        if len(acct) <= 4:
            return acct
        prefix = acct[:3]
        suffix = acct[-2:]
        return prefix + "****" + suffix

    def _login_user(self, user, c=None):
        pin = Prompt.ask("[yellow]Enter PIN[/yellow]", password=True)
        if not self.service.verify_pin(user["user_id"], pin):
            console.print("[red]Incorrect PIN[/red]")
            return None
        user["is_minor"] = bool(user["is_minor"])
        self.service.log_session(user["user_id"])
        console.print(f"[green]Welcome back, {user['name']}![/green]")
        return user

    def login(self, method=None):
        console.print(Panel("[bold yellow]Login to Your Account[/bold yellow]", border_style="yellow"))
        if not method:
            method = Prompt.ask("[yellow]Login via[/yellow]", choices=["card", "email", "phone", "account"], default="card")
        label_map = {
            "account": "[yellow]Account Number[/yellow]",
            "card": "[yellow]Card Number (XXXX-XXXX-XXXX-XXXX)[/yellow]",
            "email": "[yellow]Registered Email[/yellow]",
            "phone": "[yellow]Registered Phone (10 digits)[/yellow]",
        }
        identifier = Prompt.ask(label_map.get(method, label_map["card"]))
        if not identifier:
            return None
        user = self.service.find_user(identifier)
        if not user:
            console.print("[red]No account found with that information[/red]")
            return None
        return self._login_user(user)

    def forgot_card(self):
        console.print(Panel("[bold yellow]Forgot Card / Account Number[/bold yellow]", border_style="yellow"))
        console.print("[dim]Enter your registered email or phone to retrieve your account details.[/dim]")
        lookup = Prompt.ask("[yellow]Enter your Email or Phone[/yellow]")
        user = self.service.find_user(lookup)
        if not user:
            console.print("[red]No account found with that information[/red]")
            return None
        console.print(f"[green]Account found: {user['name']}[/green]")
        console.print(f"[yellow]Card:    [bold]{self._mask_card(user['card_no'])}[/bold][/yellow]")
        console.print(f"[yellow]Account: [bold]{self._mask_account(user['account_no'])}[/bold][/yellow]")
        console.print(f"[dim]Bank: {user['bank']} | {user['account_type'].title()}[/dim]")
        console.print("[dim]Now log in with your PIN (no card needed).[/dim]")
        if Confirm.ask("[yellow]Login now?[/yellow]", default=True):
            return self._login_user(user)
        return None

    def forgot_pin(self):
        console.print(Panel("[bold yellow]Forgot PIN[/bold yellow]", border_style="yellow"))
        console.print("[dim]Verify your identity to reset your PIN. Enter any one of the following:[/dim]")
        console.print("[dim]  - Card number[/dim]")
        console.print("[dim]  - Account number[/dim]")
        console.print("[dim]  - Registered email[/dim]")
        console.print("[dim]  - Registered phone[/dim]")
        lookup = Prompt.ask("[yellow]Enter any identifier[/yellow]")
        user = self.service.find_user(lookup)
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
        result = self.service.reset_pin(user["user_id"], new_pin)
        if isinstance(result, str):
            console.print(f"[red]{result}[/red]")
            return None
        console.print("[green]PIN reset successfully![/green]")
        if Confirm.ask("[yellow]Login now?[/yellow]", default=True):
            return self._login_user(user)
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
            result = self.service.reset_pin(user["user_id"], new_pin)
            if isinstance(result, str):
                console.print(f"[red]{result}[/red]")
                return None
            console.print("[green]PIN reset! Logging you in...[/green]")
            return self._login_user(user)
        if Confirm.ask("[yellow]Login with existing PIN?[/yellow]", default=True):
            return self._login_user(user)
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

    # ── PIN change ────────────────────────────────────────────

    def change_pin(self, user_id):
        user = self.service.get_user(user_id)
        if not user:
            return False
        old = Prompt.ask("[yellow]Enter current PIN[/yellow]", password=True)
        new = self._prompt_pin()
        confirm = Prompt.ask("[yellow]Confirm new PIN[/yellow]", password=True)
        if new != confirm:
            console.print("[red]PINs do not match[/red]")
            return False
        result = self.service.change_pin(user_id, old, new)
        if isinstance(result, str):
            console.print(f"[red]{result}[/red]")
            return False
        console.print("[green]✅ PIN changed successfully![/green]")
        return True

    # ── Delegated to UserService ──────────────────────────────

    def update_user(self, user_id, **kwargs):
        self.service.update_user(user_id, **kwargs)

    def record_transaction(self, user_id, txn_type, amount, fee=0, balance_before=0,
                           balance_after=0, channel="atm", target_account="",
                           target_bank="", bank="", notes=""):
        self.service.record_transaction(user_id, txn_type, amount, fee, balance_before,
                                        balance_after, channel, target_account,
                                        target_bank, bank, notes)

    def record_credit_event(self, user_id, event_type, amount, impact):
        self.service.record_credit_event(user_id, event_type, amount, impact)

    def record_fraud_flag(self, user_id, amount, fraud_score, reasons):
        self.service.record_fraud_flag(user_id, amount, fraud_score, reasons)

    def update_balance(self, user_id, new_balance):
        self.service.update_balance(user_id, new_balance)

    def update_atm_usage(self, user_id, amount):
        self.service.update_atm_usage(user_id, amount)

    def reset_atm_usage(self):
        self.service.reset_atm_usage()

    def get_user(self, user_id):
        return self.service.get_user(user_id)

    def get_transactions(self, user_id, limit=20):
        return self.service.get_transactions(user_id, limit)

    def end_session(self, user_id):
        self.service.end_session(user_id)

    def get_user_count(self):
        return self.service.get_user_count()

    def _export_scenario(self, scenario):
        from banking_core.data_generator import DataGenerator
        try:
            dg = DataGenerator()
            dg.export_scenario(scenario)
        except Exception:
            pass

    # ── Input prompts ─────────────────────────────────────────

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
            except Exception:
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

    def close(self):
        pass
