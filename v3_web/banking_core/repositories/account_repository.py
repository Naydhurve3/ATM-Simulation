import os
from typing import Optional

from banking_core.domain.account import Account

_USE_PG = os.environ.get("DATABASE_URL") is not None


class AccountRepository:
    def __init__(self, database=None):
        self.database = database

    def _get_conn(self):
        if _USE_PG:
            from banking_core.data.postgres_adapter import get_pg_connection
            return get_pg_connection()
        from banking_core.data.db_manager import db
        return (self.database or db).get_connection("ecosystem")

    def find_by_user_id(self, user_id: int) -> Optional[Account]:
        conn = self._get_conn()
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = c.fetchone()
        if not row:
            return None
        cols = [d[0] for d in c.description]
        u = dict(zip(cols, row))
        return Account(
            account_id=u["user_id"],
            user_id=u["user_id"],
            name=u["name"],
            bank=u["bank"],
            account_number=u["account_no"],
            card_number=u["card_no"],
            account_type=u["account_type"],
            balance=u["balance"],
            daily_limit=u["atm_daily_limit"],
            used_today=u["atm_used_today"],
            credit_score=u["credit_score"],
            is_minor=bool(u["is_minor"]),
            age=u["age"],
            age_group=u["age_group"],
            phone=u["phone"],
            email=u["email"],
            pin_hash=u["pin_hash"],
        )

    def find_by_user_id_v2(self, user_id: int) -> Optional[dict]:
        conn = self._get_conn()
        c = conn.cursor()
        c.execute("SELECT * FROM accounts_v2 WHERE user_id = ?", (user_id,))
        row = c.fetchone()
        if not row:
            return None
        cols = [d[0] for d in c.description]
        return dict(zip(cols, row))

    def update_balance(self, user_id: int, new_balance: float):
        conn = self._get_conn()
        c = conn.cursor()
        c.execute("UPDATE users SET balance = ? WHERE user_id = ?", (new_balance, user_id))
        if not _USE_PG:
            new_paise = int(round(new_balance * 100))
            c.execute("UPDATE accounts_v2 SET balance_paise = ? WHERE user_id = ?",
                      (new_paise, user_id))
        conn.commit()

    def update_daily_usage(self, user_id: int, amount: float):
        conn = self._get_conn()
        c = conn.cursor()
        c.execute(
            "UPDATE users SET atm_used_today = atm_used_today + ? WHERE user_id = ?",
            (amount, user_id),
        )
        if not _USE_PG:
            amount_paise = int(round(amount * 100))
            c.execute(
                "UPDATE accounts_v2 SET used_today_paise = used_today_paise + ? WHERE user_id = ?",
                (amount_paise, user_id),
            )
        conn.commit()
        c.execute(
            "SELECT atm_used_today, atm_daily_limit FROM users WHERE user_id = ?",
            (user_id,),
        )
        row = c.fetchone()
        if row:
            used, limit = row
            return {"used": used, "limit": limit}
        return None

    def get_user_count(self) -> int:
        conn = self._get_conn()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM users")
        return c.fetchone()[0]
