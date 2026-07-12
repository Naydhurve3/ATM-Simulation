from datetime import datetime
from typing import Optional

from src.domain.account import Account, AccountRules
from src.repositories.account_repository import AccountRepository
from src.repositories.transaction_repository import TransactionRepository


class ATMService:
    def __init__(
        self,
        account_repo: Optional[AccountRepository] = None,
        transaction_repo: Optional[TransactionRepository] = None,
    ):
        self.account_repo = account_repo or AccountRepository()
        self.txn_repo = transaction_repo or TransactionRepository()
        self.rules = AccountRules()
        self._fraud_detector = None
        self._bank_attrs_cache = {}

    def _get_fraud_detector(self):
        if self._fraud_detector is None:
            from src.models.real_time_fraud_detector import RealTimeFraudDetector
            self._fraud_detector = RealTimeFraudDetector()
        return self._fraud_detector

    def _get_bank_attrs(self, bank: str) -> dict:
        if bank not in self._bank_attrs_cache:
            from src.bank_attributes import get_bank_attrs
            self._bank_attrs_cache[bank] = get_bank_attrs(bank)
        return self._bank_attrs_cache[bank]

    def _reload_account(self, user_id: int) -> Optional[Account]:
        return self.account_repo.find_by_user_id(user_id)

    def get_account(self, user_id: int) -> Optional[Account]:
        return self._reload_account(user_id)

    def get_balance(self, user_id: int) -> dict:
        account = self._reload_account(user_id)
        if not account:
            return {"error": "Account not found"}
        bank_attrs = self._get_bank_attrs(account.bank)
        interest_rate = bank_attrs.get("savings_rate", 3.0)
        self.txn_repo.record(
            user_id=user_id,
            txn_type="balance_inquiry",
            amount=0,
            fee=0,
            balance_before=account.balance,
            balance_after=account.balance,
        )
        return {
            "success": True,
            "name": account.name,
            "account_number": account.account_number,
            "bank": account.bank,
            "account_type": account.account_type,
            "balance": account.balance,
            "interest_rate": interest_rate,
            "daily_limit": account.daily_limit,
            "used_today": account.used_today,
            "credit_score": account.credit_score,
        }

    def check_fraud(self, user_id: int, amount: float) -> dict:
        account = self._reload_account(user_id)
        if not account:
            return {"error": "Account not found"}
        recent_txns = self.txn_repo.find_by_user_id(user_id, limit=10)
        txn_info = {
            "amount": amount,
            "hour": datetime.now().hour,
            "day_of_week": datetime.now().weekday(),
            "type": "withdraw",
            "is_weekend": datetime.now().weekday() >= 5,
        }
        user_info = {"balance": account.balance, "recent_txns": recent_txns}
        fraud_result = self._get_fraud_detector().score(txn_info, user_info)
        return {
            "is_suspicious": fraud_result.get("is_suspicious", False),
            "fraud_score": fraud_result.get("fraud_score", 0),
            "reasons": fraud_result.get("reasons", []),
        }

    def withdraw(self, user_id: int, amount: float, fee: float = 0, channel: str = "atm") -> dict:
        account = self._reload_account(user_id)
        if not account:
            return {"error": "Account not found"}
        allowed, reason = self.rules.can_withdraw(account, amount)
        if not allowed:
            return {"error": reason}
        bank_attrs = self._get_bank_attrs(account.bank)
        if fee == 0:
            fee = bank_attrs.get("atm_fee_own", 0)
        total_deduction = amount + fee
        if total_deduction > account.balance:
            return {"error": f"Insufficient funds (incl. fee ₹{fee:,.0f})"}
        new_balance = account.balance - total_deduction
        self.account_repo.update_balance(account.user_id, new_balance)
        self.account_repo.update_daily_usage(account.user_id, amount)
        self.txn_repo.record(
            user_id=user_id,
            txn_type="withdraw",
            amount=amount,
            fee=fee,
            balance_before=account.balance,
            balance_after=new_balance,
            channel=channel,
            notes=str(self._get_denominations(amount)),
        )
        self.txn_repo.record_credit_event(user_id, "withdrawal", amount, -1)
        return {
            "success": True,
            "amount": amount,
            "fee": fee,
            "total_deducted": total_deduction,
            "new_balance": new_balance,
            "balance_after": new_balance,
            "denominations": self._get_denominations(amount),
        }

    def deposit(self, user_id: int, amount: float, channel: str = "atm") -> dict:
        account = self._reload_account(user_id)
        if not account:
            return {"error": "Account not found"}
        allowed, reason = self.rules.can_deposit(account, amount)
        if not allowed:
            return {"error": reason}
        new_balance = account.balance + amount
        self.account_repo.update_balance(account.user_id, new_balance)
        self.txn_repo.record(
            user_id=user_id,
            txn_type="deposit",
            amount=amount,
            fee=0,
            balance_before=account.balance,
            balance_after=new_balance,
            channel=channel,
        )
        self.txn_repo.record_credit_event(user_id, "deposit", amount, 2)
        return {
            "success": True,
            "amount": amount,
            "new_balance": new_balance,
            "balance_after": new_balance,
        }

    def transfer(self, user_id: int, amount: float, target: str, is_upi: bool = False, channel: str = None) -> dict:
        account = self._reload_account(user_id)
        if not account:
            return {"error": "Account not found"}
        allowed, reason = self.rules.can_transfer(account, amount)
        if not allowed:
            return {"error": reason}
        new_balance = account.balance - amount
        channel = channel or ("upi" if is_upi else "transfer")
        self.account_repo.update_balance(account.user_id, new_balance)
        self.txn_repo.record(
            user_id=user_id,
            txn_type="transfer",
            amount=amount,
            fee=0,
            balance_before=account.balance,
            balance_after=new_balance,
            channel=channel,
            target_account=target,
        )
        self.txn_repo.record_credit_event(user_id, "transfer", amount, 0)
        return {
            "success": True,
            "amount": amount,
            "target": target,
            "new_balance": new_balance,
        }

    def mini_statement(self, user_id: int, limit: int = 10) -> dict:
        account = self._reload_account(user_id)
        if not account:
            return {"error": "Account not found"}
        txns = self.txn_repo.find_by_user_id(user_id, limit=limit)
        return {
            "success": True,
            "transactions": [
                {
                    "timestamp": t.get("timestamp", ""),
                    "type": t.get("type", ""),
                    "amount": t.get("amount", 0),
                    "balance_after": t.get("balance_after", 0),
                }
                for t in txns
            ],
        }

    def _get_fee(self, bank: str) -> float:
        bank_attrs = self._get_bank_attrs(bank)
        return bank_attrs.get("atm_fee_own", 0)

    def _get_denominations(self, amount: float) -> dict:
        from src.utils import calculate_cash_denominations
        return calculate_cash_denominations(int(amount))
