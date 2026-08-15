from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class TransactionType(Enum):
    BALANCE_INQUIRY = "balance_inquiry"
    WITHDRAW = "withdraw"
    DEPOSIT = "deposit"
    TRANSFER = "transfer"
    PIN_CHANGE = "pin_change"


@dataclass
class Transaction:
    txn_id: int
    user_id: int
    type: str
    amount: float
    fee: float
    balance_before: float
    balance_after: float
    channel: str
    target_account: Optional[str]
    target_bank: Optional[str]
    bank: Optional[str]
    notes: Optional[str]
    timestamp: str
    is_fraud: bool
    fraud_score: Optional[float]
