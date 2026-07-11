from typing import List, Optional

from src.data.db_manager import db


class TransactionRepository:
    def __init__(self, database=None):
        self.database = database or db

    def _get_conn(self):
        return self.database.get_connection("ecosystem")

    def _get_account_id(self, user_id: int) -> Optional[int]:
        conn = self._get_conn()
        c = conn.cursor()
        c.execute("SELECT account_id FROM accounts_v2 WHERE user_id = ?", (user_id,))
        row = c.fetchone()
        return row[0] if row else None

    def record(
        self,
        user_id: int,
        txn_type: str,
        amount: float,
        fee: float = 0,
        balance_before: float = 0,
        balance_after: float = 0,
        channel: str = "atm",
        target_account: str = "",
        target_bank: str = "",
        notes: str = "",
    ):
        conn = self._get_conn()
        c = conn.cursor()
        c.execute(
            """INSERT INTO transactions
               (user_id, type, amount, fee, balance_before, balance_after,
                channel, target_account, target_bank, notes_given)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (user_id, txn_type, amount, fee, balance_before,
             balance_after, channel, target_account, target_bank, notes),
        )
        account_id = self._get_account_id(user_id)
        if account_id:
            amount_paise = int(round(amount * 100))
            fee_paise = int(round(fee * 100))
            bb_paise = int(round(balance_before * 100))
            ba_paise = int(round(balance_after * 100))
            c.execute(
                """INSERT INTO transactions_v2
                   (account_id, user_id, type, amount_paise, fee_paise,
                    balance_before_paise, balance_after_paise,
                    channel, target_account, notes)
                   VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (account_id, user_id, txn_type, amount_paise, fee_paise,
                 bb_paise, ba_paise, channel, target_account, notes),
            )
        conn.commit()
        c.execute(
            "UPDATE users SET last_active = CURRENT_TIMESTAMP WHERE user_id = ?",
            (user_id,),
        )
        conn.commit()

    def record_credit_event(self, user_id: int, event_type: str, amount: float, impact: int):
        conn = self._get_conn()
        c = conn.cursor()
        c.execute(
            "INSERT INTO credit_history (user_id, event_type, amount, score_impact) VALUES (?,?,?,?)",
            (user_id, event_type, amount, impact),
        )
        conn.commit()
        c.execute(
            "UPDATE users SET credit_score = credit_score + ? WHERE user_id = ?",
            (impact, user_id),
        )
        conn.commit()

    def record_fraud_flag(self, user_id: int, amount: float, fraud_score: float, reasons: str):
        conn = self._get_conn()
        c = conn.cursor()
        c.execute(
            "INSERT INTO fraud_flags (user_id, anomaly_score, flagged_by) VALUES (?,?,?)",
            (user_id, fraud_score, reasons),
        )
        conn.commit()

    def find_by_user_id(self, user_id: int, limit: int = 20) -> List[dict]:
        conn = self._get_conn()
        c = conn.cursor()
        c.execute(
            "SELECT * FROM transactions WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?",
            (user_id, limit),
        )
        cols = [d[0] for d in c.description]
        return [dict(zip(cols, row)) for row in c.fetchall()]

    def find_by_user_id_v2(self, user_id: int, limit: int = 20) -> List[dict]:
        conn = self._get_conn()
        c = conn.cursor()
        c.execute(
            "SELECT * FROM transactions_v2 WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?",
            (user_id, limit),
        )
        cols = [d[0] for d in c.description]
        return [dict(zip(cols, row)) for row in c.fetchall()]

    def get_count(self) -> int:
        conn = self._get_conn()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM transactions")
        return c.fetchone()[0]

    def get_avg_balance(self) -> float:
        conn = self._get_conn()
        c = conn.cursor()
        c.execute("SELECT AVG(balance) FROM users")
        row = c.fetchone()
        return round(row[0] or 0, 2)
