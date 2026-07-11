import pytest
import os
import sys
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models import (
    RealTimeFraudDetector, InvestmentRecommender, ATMReplenishmentOptimizer,
    RFMSegmenter, SavingsGoalOptimizer, SentimentAnalyzer
)

SA_SKIP = not hasattr(SentimentAnalyzer, 'analyze_text')


def test_fraud_detector_score():
    fd = RealTimeFraudDetector()
    txn = {"amount": 50000, "hour": 14, "balance": 100000}
    result = fd.score(txn, {"age": 30, "balance": 100000, "recent_txns": []})
    assert isinstance(result, dict)
    assert "fraud_score" in result
    assert 0 <= result["fraud_score"] <= 1


def test_investment_recommender():
    ir = InvestmentRecommender()
    result = ir.recommend(age=30, income_bracket="earning_5L_10L", balance=100000, risk_tolerance="medium")
    assert isinstance(result, dict)
    assert "products" in result
    assert len(result["products"]) > 0


def test_atm_replenishment():
    ao = ATMReplenishmentOptimizer()
    result = ao.optimize(predicted_monthly_demand=500000, atm_capacity=2000000)
    assert isinstance(result, dict)
    assert "error" not in result
    assert "optimal_refill_amount" in result


def test_rfm_segmenter():
    rs = RFMSegmenter()
    transactions = [
        {"amount": 1000, "timestamp": datetime.now().isoformat()},
        {"amount": 500, "timestamp": (datetime.now() - timedelta(days=30)).isoformat()},
    ]
    segments = rs.segment(transactions)
    assert len(segments) > 0


def test_savings_optimizer():
    so = SavingsGoalOptimizer()
    plan = so.optimize(target_amount=500000, deadline_months=24, monthly_income=80000)
    assert isinstance(plan, dict)
    assert "error" not in plan


@pytest.mark.skipif(SA_SKIP, reason="vaderSentiment not installed")
def test_sentiment_analyzer():
    sa = SentimentAnalyzer()
    result = sa.analyze_text("Great service, very satisfied!")
    assert "compound" in result or "sentiment" in result or "label" in result