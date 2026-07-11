from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Account:
    account_id: int
    user_id: int
    name: str
    bank: str
    account_number: str
    card_number: str
    account_type: str
    balance: float
    daily_limit: float
    used_today: float
    credit_score: int
    is_minor: bool
    age: int
    age_group: str
    phone: str
    email: str
    pin_hash: str


class AccountRules:
    @staticmethod
    def can_withdraw(account: Account, amount: float) -> tuple[bool, Optional[str]]:
        if amount <= 0:
            return False, "Invalid amount"
        if amount % 100 != 0:
            return False, "Amount must be in multiples of 100"
        if amount > account.balance:
            return False, "Insufficient funds"
        if account.is_minor and account.age < 14:
            return False, "This account is guardian-operated"
        projected = account.used_today + amount
        if projected > account.daily_limit:
            remaining = account.daily_limit - account.used_today
            return False, f"Daily limit exceeded. Remaining: ₹{remaining:,.0f}"
        return True, None

    @staticmethod
    def can_deposit(account: Account, amount: float) -> tuple[bool, Optional[str]]:
        if amount <= 0:
            return False, "Invalid amount"
        if amount % 100 != 0:
            return False, "Amount must be in multiples of 100"
        return True, None

    @staticmethod
    def can_transfer(account: Account, amount: float) -> tuple[bool, Optional[str]]:
        if account.is_minor:
            return False, "Transfer not available for minor accounts"
        if amount <= 0:
            return False, "Invalid amount"
        if amount > account.balance:
            return False, "Insufficient funds"
        return True, None
