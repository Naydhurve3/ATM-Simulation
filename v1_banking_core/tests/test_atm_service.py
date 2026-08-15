import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from unittest.mock import MagicMock, patch

from banking_core.domain.account import Account
from banking_core.services import ATMService


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


class TestATMService:
    def _make_service(self, **account_overrides):
        self.mock_account_repo = MagicMock()
        self.mock_txn_repo = MagicMock()
        account = make_account(**account_overrides)
        self.mock_account_repo.find_by_user_id.return_value = account
        service = ATMService(
            account_repo=self.mock_account_repo,
            transaction_repo=self.mock_txn_repo,
        )
        return service, account

    def test_get_balance_success(self):
        service, account = self._make_service()
        result = service.get_balance(1)
        assert result["success"] is True
        assert result["name"] == "Test User"
        assert result["balance"] == 10000.0
        assert result["bank"] == "SBI"
        assert isinstance(result["interest_rate"], float)
        self.mock_txn_repo.record.assert_called_once()

    def test_get_balance_account_not_found(self):
        service, _ = self._make_service()
        self.mock_account_repo.find_by_user_id.return_value = None
        result = service.get_balance(999)
        assert "error" in result

    def test_deposit_success(self):
        service, account = self._make_service()
        result = service.deposit(1, 5000)
        assert result["success"] is True
        assert result["amount"] == 5000
        assert result["new_balance"] == 15000.0
        self.mock_account_repo.update_balance.assert_called_once_with(1, 15000.0)
        self.mock_txn_repo.record.assert_called_once()
        self.mock_txn_repo.record_credit_event.assert_called_once_with(1, "deposit", 5000, 2)

    def test_deposit_invalid_amount(self):
        service, _ = self._make_service()
        result = service.deposit(1, -100)
        assert "error" in result

    def test_deposit_not_multiple_100(self):
        service, _ = self._make_service()
        result = service.deposit(1, 123)
        assert "error" in result

    def test_withdraw_success(self):
        service, account = self._make_service()
        result = service.withdraw(1, 2000)
        assert result["success"] is True
        assert result["amount"] == 2000
        assert result["new_balance"] == 8000.0
        self.mock_account_repo.update_balance.assert_called_once_with(1, 8000.0)
        self.mock_txn_repo.record.assert_called_once()
        self.mock_txn_repo.record_credit_event.assert_called_once_with(1, "withdrawal", 2000, -1)

    def test_withdraw_insufficient_funds(self):
        service, account = self._make_service()
        result = service.withdraw(1, 20000)
        assert "error" in result

    def test_withdraw_exact_balance(self):
        service, account = self._make_service()
        result = service.withdraw(1, 10000)
        assert result["success"] is True
        assert result["new_balance"] == 0.0

    def test_withdraw_not_multiple_100(self):
        service, _ = self._make_service()
        result = service.withdraw(1, 250)
        assert "error" in result

    def test_transfer_success(self):
        service, account = self._make_service()
        result = service.transfer(1, 3000, "ACC12345", is_upi=False)
        assert result["success"] is True
        assert result["amount"] == 3000
        assert result["new_balance"] == 7000.0
        assert result["target"] == "ACC12345"
        self.mock_account_repo.update_balance.assert_called_once_with(1, 7000.0)

    def test_transfer_upi(self):
        service, account = self._make_service()
        result = service.transfer(1, 500, "user@paytm", is_upi=True)
        assert result["success"] is True
        assert result["target"] == "user@paytm"

    def test_transfer_insufficient(self):
        service, _ = self._make_service()
        result = service.transfer(1, 999999, "ACC12345")
        assert "error" in result

    def test_mini_statement(self):
        service, account = self._make_service()
        self.mock_txn_repo.find_by_user_id.return_value = [
            {"timestamp": "2026-07-01 10:00", "type": "deposit", "amount": 5000, "balance_after": 15000},
            {"timestamp": "2026-06-28 14:30", "type": "withdraw", "amount": 2000, "balance_after": 10000},
        ]
        result = service.mini_statement(1)
        assert result["success"] is True
        assert len(result["transactions"]) == 2
        assert result["transactions"][0]["type"] == "deposit"

    def test_mini_statement_empty(self):
        service, account = self._make_service()
        self.mock_txn_repo.find_by_user_id.return_value = []
        result = service.mini_statement(1)
        assert result["success"] is True
        assert len(result["transactions"]) == 0

    def test_check_fraud_no_suspicion(self):
        service, account = self._make_service(balance=50000)
        self.mock_txn_repo.find_by_user_id.return_value = []
        mock_fd = MagicMock()
        mock_fd.score.return_value = {"is_suspicious": False}
        with patch.object(service, "_get_fraud_detector", return_value=mock_fd):
            result = service.check_fraud(1, 1000)
            assert result["is_suspicious"] is False

    def test_fraud_high_amount(self):
        service, account = self._make_service(balance=50000)
        self.mock_txn_repo.find_by_user_id.return_value = []
        mock_fd = MagicMock()
        mock_fd.score.return_value = {
            "is_suspicious": True,
            "fraud_score": 0.85,
            "reasons": ["High amount"],
        }
        with patch.object(service, "_get_fraud_detector", return_value=mock_fd):
            result = service.check_fraud(1, 40000)
            assert result["is_suspicious"] is True
            assert result["fraud_score"] == 0.85

    def test_account_not_found(self):
        service, _ = self._make_service()
        self.mock_account_repo.find_by_user_id.return_value = None
        result = service.get_balance(999)
        assert "error" in result
        result = service.withdraw(999, 1000)
        assert "error" in result
        result = service.deposit(999, 1000)
        assert "error" in result
