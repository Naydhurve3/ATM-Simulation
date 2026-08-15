import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from banking_core.domain.account import Account, AccountRules


def make_account(**overrides):
    base = dict(
        account_id=1,
        user_id=1,
        name="Test User",
        bank="SBI",
        account_number="SBI10004521",
        card_number="1234567890123456",
        account_type="savings",
        balance=10000.0,
        daily_limit=50000.0,
        used_today=0.0,
        credit_score=700,
        is_minor=False,
        age=30,
        age_group="Adult",
        phone="9876543210",
        email="test@example.com",
        pin_hash="hash",
    )
    base.update(overrides)
    return Account(**base)


class TestCanWithdraw:
    def test_valid_withdrawal(self):
        account = make_account()
        ok, reason = AccountRules.can_withdraw(account, 1000)
        assert ok
        assert reason is None

    def test_negative_amount(self):
        account = make_account()
        ok, reason = AccountRules.can_withdraw(account, -100)
        assert not ok
        assert "Invalid" in reason

    def test_zero_amount(self):
        account = make_account()
        ok, reason = AccountRules.can_withdraw(account, 0)
        assert not ok
        assert "Invalid" in reason

    def test_not_multiple_of_100(self):
        account = make_account()
        ok, reason = AccountRules.can_withdraw(account, 250)
        assert not ok
        assert "multiples of 100" in reason

    def test_insufficient_balance(self):
        account = make_account(balance=500)
        ok, reason = AccountRules.can_withdraw(account, 1000)
        assert not ok
        assert "Insufficient" in reason

    def test_exact_balance(self):
        account = make_account(balance=1000)
        ok, reason = AccountRules.can_withdraw(account, 1000)
        assert ok

    def test_guardian_operated_minor(self):
        account = make_account(is_minor=True, age=12)
        ok, reason = AccountRules.can_withdraw(account, 100)
        assert not ok
        assert "guardian-operated" in reason

    def test_teen_can_withdraw(self):
        account = make_account(is_minor=True, age=15)
        ok, reason = AccountRules.can_withdraw(account, 500)
        assert ok

    def test_daily_limit_exceeded(self):
        account = make_account(used_today=48000, daily_limit=50000)
        ok, reason = AccountRules.can_withdraw(account, 3000)
        assert not ok
        assert "Daily limit" in reason

    def test_daily_limit_boundary(self):
        account = make_account(used_today=45000, daily_limit=50000)
        ok, reason = AccountRules.can_withdraw(account, 5000)
        assert ok

    def test_large_withdrawal_adult(self):
        account = make_account(balance=100000, daily_limit=100000)
        ok, reason = AccountRules.can_withdraw(account, 75000)
        assert ok


class TestCanDeposit:
    def test_valid_deposit(self):
        account = make_account()
        ok, reason = AccountRules.can_deposit(account, 1000)
        assert ok

    def test_negative_deposit(self):
        account = make_account()
        ok, reason = AccountRules.can_deposit(account, -100)
        assert not ok

    def test_not_multiple_of_100(self):
        account = make_account()
        ok, reason = AccountRules.can_deposit(account, 123)
        assert not ok


class TestCanTransfer:
    def test_valid_transfer(self):
        account = make_account()
        ok, reason = AccountRules.can_transfer(account, 1000)
        assert ok

    def test_minor_transfer_blocked(self):
        account = make_account(is_minor=True, age=12)
        ok, reason = AccountRules.can_transfer(account, 100)
        assert not ok
        assert "Transfer not available" in reason

    def test_transfer_exact_balance(self):
        account = make_account(balance=5000)
        ok, reason = AccountRules.can_transfer(account, 5000)
        assert ok

    def test_transfer_overdraft_blocked(self):
        account = make_account(balance=1000)
        ok, reason = AccountRules.can_transfer(account, 5001)
        assert not ok
