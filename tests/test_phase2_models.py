import pytest
import os
import sys
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models.real_time_fraud_detector import RealTimeFraudDetector
from src.models.investment_recommender import InvestmentRecommender
from src.models.atm_replenishment import ATMReplenishmentOptimizer
from src.models.rfm_segmenter import RFMSegmenter
from src.models.savings_optimizer import SavingsGoalOptimizer
from src.models.sentiment_analyzer import SentimentAnalyzer
from src.models.model_monitor import ModelMonitor
from src.utils import DATA_MODELS, ECOSYSTEM_DB

class TestRealTimeFraudDetector:
    def test_train_and_score(self):
        detector = RealTimeFraudDetector()
        txns = [
            {"amount": 500, "hour": 10, "day_of_week": 0, "type": "withdraw"},
            {"amount": 1000, "hour": 14, "day_of_week": 1, "type": "withdraw"},
            {"amount": 2000, "hour": 11, "day_of_week": 2, "type": "withdraw"},
        ]
        detector.train(txns)
        assert detector.is_trained

    def test_score_normal(self):
        detector = RealTimeFraudDetector()
        txns = [{"amount": 1000, "hour": 12, "day_of_week": 0, "type": "withdraw"}]
        detector.train(txns)
        result = detector.score({"amount": 500, "hour": 12, "day_of_week": 0, "type": "withdraw", "is_weekend": False}, {"balance": 50000, "recent_txns": []})
        assert 0 <= result["fraud_score"] <= 1
        assert "method" in result

    def test_score_suspicious_large_amount(self):
        detector = RealTimeFraudDetector()
        txns = [{"amount": 1000, "hour": 12, "day_of_week": 0, "type": "withdraw"}]
        detector.train(txns)
        result = detector.score({"amount": 100000, "hour": 3, "day_of_week": 0, "type": "withdraw", "is_weekend": True}, {"balance": 50000, "recent_txns": []})
        assert "reasons" in result
        assert len(result["reasons"]) > 0

class TestInvestmentRecommender:
    def test_recommend_adult(self):
        rec = InvestmentRecommender()
        result = rec.recommend(age=30, income_bracket="earning_5L_10L", balance=100000, risk_tolerance="moderate")
        products = result.get("products", [])
        assert len(products) > 0
        for item in products:
            assert "name" in item
            assert "allocation_pct" in item
            assert "expected_return_pct" in item

    def test_recommend_minor(self):
        rec = InvestmentRecommender()
        result = rec.recommend(age=15, income_bracket="not_earning_student", balance=5000, risk_tolerance="conservative")
        products = result.get("products", [])
        for item in products:
            assert item["name"] in ("Recurring Deposit", "Public Provident Fund")

    def test_total_allocation(self):
        rec = InvestmentRecommender()
        result = rec.recommend(age=30, income_bracket="earning_5L_10L", balance=100000, risk_tolerance="moderate")
        products = result.get("products", [])
        total_pct = sum(item["allocation_pct"] for item in products)
        assert abs(total_pct - 100) < 0.01

class TestATMReplenishmentOptimizer:
    def test_optimize(self):
        opt = ATMReplenishmentOptimizer()
        result = opt.optimize(predicted_monthly_demand=5000000)
        assert "optimal_refill_amount" in result
        assert "optimal_refills_per_month" in result
        assert result["optimal_refill_amount"] > 0
        assert result["optimal_refills_per_month"] > 0

    def test_compare_strategies(self):
        opt = ATMReplenishmentOptimizer()
        result = opt.compare_strategies(5000000)
        strategies = result.get("strategies", [])
        assert len(strategies) == 3
        assert strategies[2]["strategy_name"] == "Optimized (EOQ)"
        assert "best_strategy" in result

class TestRFMSegmenter:
    def test_segment(self):
        seg = RFMSegmenter()
        txns = []
        for i in range(10):
            txns.append({
                "amount": 1000 + i * 100,
                "timestamp": (datetime.now() - timedelta(days=i)).isoformat(),
                "type": "withdraw" if i % 2 == 0 else "deposit",
            })
        result = seg.segment(txns)
        assert "rfm_score" in result
        assert "total_score" in result
        assert "segment" in result
        assert 3 <= result["total_score"] <= 15

    def test_empty_transactions(self):
        seg = RFMSegmenter()
        result = seg.segment([])
        assert result["segment"] in ("Lost", "Unknown")

class TestSavingsGoalOptimizer:
    def test_optimize_achievable(self):
        opt = SavingsGoalOptimizer()
        result = opt.optimize(target_amount=60000, deadline_months=12, current_balance=0, monthly_income=30000, monthly_expenses=20000)
        assert result["status"] == "achievable"
        assert result["required_monthly_deposit"] > 0

    def test_optimize_difficult(self):
        opt = SavingsGoalOptimizer()
        result = opt.optimize(target_amount=1000000, deadline_months=6, current_balance=0, monthly_income=20000, monthly_expenses=18000)
        assert result["status"] in ("tight", "difficult")

    def test_recurring_deposit(self):
        opt = SavingsGoalOptimizer()
        result = opt.suggest_recurring_deposit(monthly_amount=5000, tenure_months=12)
        assert result["total_deposited"] == 60000
        assert result["maturity_amount"] > result["total_deposited"]

class TestSentimentAnalyzer:
    def test_analyze_positive(self):
        sa = SentimentAnalyzer()
        result = sa.analyze_text("This bank is excellent! Great service!")
        assert result["sentiment_label"] == "Positive"
        assert result["compound"] > 0

    def test_analyze_negative(self):
        sa = SentimentAnalyzer()
        result = sa.analyze_text("Terrible experience. Worst customer service ever.")
        assert result["sentiment_label"] == "Negative"
        assert result["compound"] < 0

    def test_analyze_neutral(self):
        sa = SentimentAnalyzer()
        result = sa.analyze_text("The ATM is located at the corner.")
        assert result["sentiment_label"] == "Neutral"

class TestModelMonitor:
    def test_log_and_retrieve(self):
        monitor = ModelMonitor()
        monitor.log_metrics("TestModel", {"MAE": 10.5, "RMSE": 15.2})
        trend = monitor.get_performance_trend("TestModel", "MAE")
        assert len(trend) > 0
        assert len(trend[0]) == 3

    def test_staleness(self):
        monitor = ModelMonitor()
        is_stale = monitor.get_staleness("NonExistentModel", max_days=0)
        assert is_stale

    def test_latest_metrics(self):
        monitor = ModelMonitor()
        monitor.log_metrics("TestModel2", {"MAE": 5.0, "R2": 0.95})
        latest = monitor.get_latest_metrics("TestModel2")
        assert "MAE" in latest
        assert latest["MAE"] == 5.0


