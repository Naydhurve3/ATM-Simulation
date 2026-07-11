import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
import pytest
from src.models import CreditScorer, ChurnPredictor, LoanDefaultModel, BankRecommender


class TestCreditScorer:
    def test_rule_based_score_adult(self):
        cs = CreditScorer()
        sample = {"age": 30, "balance": 50000, "txn_count": 25,
                  "fraud_count": 0, "is_minor": False,
                  "income_bracket": "earning_5L_10L"}
        score = cs.predict(sample)
        assert 300 <= score <= 900

    def test_rule_based_score_minor(self):
        cs = CreditScorer()
        sample = {"age": 15, "balance": 1000, "txn_count": 2,
                  "fraud_count": 0, "is_minor": True, "income_bracket": "minor"}
        score = cs.predict(sample)
        assert 200 <= score <= 900

    def test_score_increases_with_balance(self):
        cs = CreditScorer()
        base = {"age": 35, "txn_count": 20, "fraud_count": 0,
                "is_minor": False, "income_bracket": "earning_5L_10L"}
        low = cs.predict({**base, "balance": 10000})
        high = cs.predict({**base, "balance": 500000})
        assert high >= low

    def test_fraud_history_penalty(self):
        cs = CreditScorer()
        base = {"age": 30, "balance": 50000, "txn_count": 25,
                "is_minor": False, "income_bracket": "earning_5L_10L"}
        clean = cs.predict({**base, "fraud_count": 0})
        risky = cs.predict({**base, "fraud_count": 3})
        assert risky <= clean


class TestChurnPredictor:
    def test_low_risk(self):
        cp = ChurnPredictor()
        result = cp.predict({"days_since_last_txn": 1})
        assert result["risk_level"] in ("LOW", "MEDIUM", "HIGH")

    def test_high_risk(self):
        cp = ChurnPredictor()
        result = cp.predict({"days_since_last_txn": 120})
        assert result["risk_level"] in ("LOW", "MEDIUM", "HIGH")

    def test_risk_score_range(self):
        cp = ChurnPredictor()
        result = cp.predict({"days_since_last_txn": 30})
        assert 0 <= result.get("risk_score", 0) <= 1


class TestLoanDefaultModel:
    def test_low_risk_borrower(self):
        ldm = LoanDefaultModel()
        user = {"is_minor": False, "age": 35, "credit_score": 750,
                "balance": 500000, "income_bracket": "earning_10L_plus"}
        result = ldm.predict(user, 50000, 8.5, 12)
        assert result["risk_level"] in ("LOW", "MEDIUM", "HIGH", "VERY HIGH")
        assert 0 <= result["risk_score"] <= 1

    def test_high_risk_borrower(self):
        ldm = LoanDefaultModel()
        user = {"is_minor": False, "age": 22, "credit_score": 350,
                "balance": 500, "income_bracket": "unemployed"}
        result = ldm.predict(user, 500000, 18.0, 60)
        assert result["risk_level"] in ("LOW", "MEDIUM", "HIGH", "VERY HIGH")


class TestBankRecommender:
    def test_recommendations_generated(self):
        br = BankRecommender()
        user = {"age": 30, "is_minor": False,
                "income_bracket": "earning_5L_10L", "preferences": {}}
        recs = br.recommend(user, top_n=3)
        assert len(recs) > 0
        # Returns list of (bank_name, score) tuples
        assert isinstance(recs[0], (tuple, list))
        assert len(recs[0]) == 2