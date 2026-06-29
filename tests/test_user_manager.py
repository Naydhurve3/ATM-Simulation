import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
import pytest
from src.utils import validate_name, validate_phone, validate_email, validate_age, get_age_group

class TestValidation:
    def test_valid_name(self):
        ok, result = validate_name("Rohan Sharma")
        assert ok
        assert result == "Rohan Sharma"

    def test_short_name(self):
        ok, result = validate_name("A")
        assert not ok

    def test_single_word_name(self):
        ok, result = validate_name("Rohan")
        assert not ok

    def test_valid_phone(self):
        ok, result = validate_phone("9876543210")
        assert ok

    def test_short_phone(self):
        ok, result = validate_phone("12345")
        assert not ok

    def test_invalid_phone_prefix(self):
        ok, result = validate_phone("1234567890")
        assert not ok

    def test_valid_email(self):
        ok, result = validate_email("test@example.com")
        assert ok
        assert result == "test@example.com"

    def test_invalid_email(self):
        ok, result = validate_email("not-an-email")
        assert not ok

    def test_valid_age(self):
        ok, result = validate_age(25)
        assert ok

    def test_too_young(self):
        ok, result = validate_age(9)
        assert not ok

    def test_too_old(self):
        ok, result = validate_age(121)
        assert not ok

    def test_age_group_child(self):
        label, is_minor = get_age_group(12)
        assert label == "Child"
        assert is_minor

    def test_age_group_teen(self):
        label, is_minor = get_age_group(15)
        assert label == "Teen"
        assert is_minor

    def test_age_group_adult(self):
        label, is_minor = get_age_group(30)
        assert label == "Adult"
        assert not is_minor

    def test_age_group_senior(self):
        label, is_minor = get_age_group(65)
        assert label == "Senior"
        assert not is_minor

class TestBankAliases:
    def test_sbi_alias(self):
        from src.utils import resolve_bank_alias
        assert resolve_bank_alias("SBI") == "STATE BANK OF INDIA"

    def test_hdfc_alias(self):
        from src.utils import resolve_bank_alias
        assert resolve_bank_alias("HDFC") == "HDFC BANK LTD"

class TestAccountGeneration:
    def test_account_no_format(self):
        from src.utils import generate_account_no
        acc = generate_account_no("SBI")
        assert acc.startswith("SBI")
        assert len(acc) > 3

    def test_card_no_format(self):
        from src.utils import generate_card_no
        card = generate_card_no()
        assert card.count("-") == 3
