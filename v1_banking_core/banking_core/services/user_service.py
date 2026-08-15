import sqlite3
from typing import Optional

from banking_core.utils import (
    hash_pin, get_age_group, generate_account_no, generate_card_no, ensure_dirs,
)
from banking_core.bank_attributes import get_bank_attrs, get_bank_prefix
from banking_core.data.db_manager import db


class UserService:
    """Pure banking user logic (registration, KYC, auth, recovery, account data).

    UI-free: returns dicts / error strings. Consumed by both the CLI (v2)
    and the web app (v3).
    """

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

    # ── Lookup / Auth ─────────────────────────────────────────

    def find_user(self, identifier: str) -> Optional[dict]:
        """Resolve an identifier (email / phone / account no / card no) to a user."""
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

    def get_user(self, user_id: int) -> Optional[dict]:
        c = self.conn.cursor()
        c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = c.fetchone()
        if row:
            col_names = [d[0] for d in c.description]
            d = dict(zip(col_names, row))
            d["is_minor"] = bool(d["is_minor"])
            return d
        return None

    def verify_pin(self, user_id: int, pin: str) -> bool:
        user = self.get_user(user_id)
        if not user:
            return False
        return hash_pin(pin) == user["pin_hash"]

    def authenticate(self, identifier: str, pin: str):
        """Login by identifier + PIN. Returns user dict, or an error string."""
        user = self.find_user(identifier)
        if not user:
            return "Account not found"
        if hash_pin(pin) != user["pin_hash"]:
            return "Incorrect PIN"
        user["is_minor"] = bool(user["is_minor"])
        self.log_session(user["user_id"])
        return user

    # ── Registration / KYC ────────────────────────────────────

    def register(self, data: dict):
        """Create a new account.

        data keys: name, phone, email, age, income_status, income_bracket,
        guardian (dict: name, phone, relation, guardian_aadhaar, child_aadhaar,
        address_match, surname_match), bank, pin.
        Returns the created user dict, or an error string.
        """
        name = data["name"]
        phone = data["phone"]
        email = data["email"]
        age = int(data["age"])
        income_status = data.get("income_status", "not_earning_student")
        income_bracket = data.get("income_bracket", income_status)
        guardian_data = data.get("guardian", {}) or {}
        bank = data["bank"]
        pin = data["pin"]

        age_group, is_minor = get_age_group(age)
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

        c = self.conn.cursor()
        if c.execute("SELECT user_id FROM users WHERE email = ?", (email,)).fetchone():
            return "This email is already registered"
        if c.execute("SELECT user_id FROM users WHERE phone = ?", (phone,)).fetchone():
            return "This phone number is already registered"

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
            "pin_hash": hash_pin(pin),
            "balance": 5000,
            "atm_daily_limit": atm_limit,
            "credit_score": 600 if not is_minor else 650,
        }
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
            user_data["user_id"] = c.lastrowid
            user_data["is_minor"] = bool(is_minor)
            return user_data
        except sqlite3.IntegrityError as e:
            return f"Registration error: {e}"

    # ── Account updates ───────────────────────────────────────

    def update_user(self, user_id: int, **kwargs):
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

    def update_balance(self, user_id: int, new_balance: float):
        c = self.conn.cursor()
        c.execute("UPDATE users SET balance = ? WHERE user_id = ?", (new_balance, user_id))
        self.conn.commit()

    def update_atm_usage(self, user_id: int, amount: float):
        c = self.conn.cursor()
        c.execute("UPDATE users SET atm_used_today = atm_used_today + ? WHERE user_id = ?",
                  (amount, user_id))
        self.conn.commit()

    def reset_atm_usage(self):
        c = self.conn.cursor()
        c.execute("UPDATE users SET atm_used_today = 0")
        self.conn.commit()

    # ── Transactions / history ────────────────────────────────

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

    def record_fraud_flag(self, user_id, amount, fraud_score, reasons):
        c = self.conn.cursor()
        c.execute("""INSERT INTO fraud_flags (user_id, anomaly_score, flagged_by, is_confirmed)
                     VALUES (?,?,?,0)""",
                  (user_id, fraud_score, reasons[:200]))
        self.conn.commit()

    def get_transactions(self, user_id: int, limit: int = 20) -> list:
        c = self.conn.cursor()
        c.execute("SELECT * FROM transactions WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?",
                  (user_id, limit))
        cols = [d[0] for d in c.description]
        return [dict(zip(cols, row)) for row in c.fetchall()]

    # ── PIN management ────────────────────────────────────────

    def change_pin(self, user_id: int, old_pin: str, new_pin: str):
        if not self.verify_pin(user_id, old_pin):
            return "Incorrect current PIN"
        if not (new_pin.isdigit() and len(new_pin) == 4):
            return "PIN must be exactly 4 digits"
        c = self.conn.cursor()
        c.execute("UPDATE users SET pin_hash = ? WHERE user_id = ?",
                  (hash_pin(new_pin), user_id))
        self.conn.commit()
        return True

    def reset_pin(self, user_id: int, new_pin: str):
        if not (new_pin.isdigit() and len(new_pin) == 4):
            return "PIN must be exactly 4 digits"
        c = self.conn.cursor()
        c.execute("UPDATE users SET pin_hash = ? WHERE user_id = ?", (hash_pin(new_pin), user_id))
        self.conn.commit()
        return True

    # ── Sessions ──────────────────────────────────────────────

    def log_session(self, user_id: int):
        c = self.conn.cursor()
        c.execute("INSERT INTO user_sessions (user_id) VALUES (?)", (user_id,))
        self.conn.commit()

    def end_session(self, user_id: int):
        c = self.conn.cursor()
        c.execute("""UPDATE user_sessions SET logout_at = CURRENT_TIMESTAMP
            WHERE user_id = ? AND logout_at IS NULL""", (user_id,))
        self.conn.commit()
        self._export_scenario("SESSION_END")

    # ── Stats ─────────────────────────────────────────────────

    def get_user_count(self) -> int:
        return self.conn.cursor().execute("SELECT COUNT(*) FROM users").fetchone()[0]

    def _export_scenario(self, scenario):
        from banking_core.data_generator import DataGenerator
        try:
            dg = DataGenerator()
            dg.export_scenario(scenario)
        except Exception:
            pass

    def close(self):
        pass
