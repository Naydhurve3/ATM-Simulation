import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
import pytest
import numpy as np
from src.models import CreditScorer, ChurnPredictor, LoanDefaultModel, BankRecommender

class TestCreditScorer:
    def test_rule_based_score_adult(self):
        cs = CreditScorer()
        sample = {"age": 30, "balance": 50000, "txn_count": 25,
                  "fraud_count": 0, "is_minor": False,
                  "income_bracket": "earning_5L_10L"}
        score = cs.predict(sample)
        assert 300 <= score <= 900
        assert score > 650

    def test_rule_based_score_minor(self):
        cs = CreditScorer()
        sample = {"age": 14, "balance": 12000, "txn_count": 5,
                  "fraud_count": 0, "is_minor": True,
                  "income_bracket": "not_earning_student"}
        score = cs.predict(sample)
        assert 300 <= score <= 900
        assert score >= 650

    def test_low_balance_score(self):
        cs = CreditScorer()
        sample = {"age": 25, "balance": 500, "txn_count": 1,
                  "fraud_count": 2, "is_minor": False,
                  "income_bracket": "not_earning_unemployed"}
        score = cs.predict(sample)
        assert 300 <= score <= 900

class TestChurnPredictor:
    def test_rule_based_churn_high(self):
        cp = ChurnPredictor()
        result = cp.predict({"days_since_last_txn": 90})
        assert "risk_score" in result
        assert result["risk_level"] == "HIGH"

    def test_rule_based_churn_low(self):
        cp = ChurnPredictor()
        result = cp.predict({"days_since_last_txn": 5})
        assert result["risk_level"] == "LOW"

class TestLoanDefaultModel:
    def test_minor_not_eligible(self):
        ldm = LoanDefaultModel()
        user = {"is_minor": True, "age": 14, "credit_score": 650, "balance": 5000}
        result = ldm.predict(user, 100000, 10.5, 36)
        assert not result["eligible"]

    def test_adult_eligible(self):
        ldm = LoanDefaultModel()
        user = {"is_minor": False, "age": 30, "credit_score": 750,
                "balance": 50000, "income_bracket": "earning_5L_10L"}
        result = ldm.predict(user, 100000, 10.5, 36)
        assert "risk_score" in result

class TestBankRecommender:
    def test_recommender_returns_list(self):
        br = BankRecommender()
        user = {"age": 30, "is_minor": False, "income_bracket": "earning_5L_10L",
                "preferences": {}}
        recs = br.recommend(user, top_n=3)
        assert len(recs) <= 3
        assert all(isinstance(r, tuple) for r in recs)

    def test_recommender_minor(self):
        br = BankRecommender()
        user = {"age": 14, "is_minor": True, "income_bracket": "not_earning_student",
                "preferences": {}}
        recs = br.recommend(user, top_n=3)
        assert len(recs) > 0
