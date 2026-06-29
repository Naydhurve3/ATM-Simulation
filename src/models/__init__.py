from .cash_demand_forecaster import CashDemandForecaster
from .transaction_predictor import TransactionPredictor
from .bank_clustering import BankClustering
from .anomaly_detector import AnomalyDetector
from .trend_analyzer import TrendAnalyzer
from .channel_migration import ChannelMigrationPredictor
from .what_if_simulator import WhatIfSimulator
from .credit_scorer import CreditScorer
from .churn_predictor import ChurnPredictor
from .loan_default_model import LoanDefaultModel
from .bank_recommender import BankRecommender
from .spending_forecaster import SpendingForecaster
try:
    from .lstm_forecaster import LSTMForecaster
except Exception:
    class LSTMForecaster:
        def __init__(self): self.is_trained = False; self.metrics = {}
        def is_available(self): return False
        def train(self, *a, **kw): return {"error": "TensorFlow unavailable"}
        def predict(self, *a, **kw): return {"error": "TensorFlow unavailable"}
        def backtest(self, *a, **kw): return {"error": "TensorFlow unavailable"}
        def load(self): return False
        def save(self): pass
from .real_time_fraud_detector import RealTimeFraudDetector
from .investment_recommender import InvestmentRecommender
from .atm_replenishment import ATMReplenishmentOptimizer
from .rfm_segmenter import RFMSegmenter
from .savings_optimizer import SavingsGoalOptimizer
from .sentiment_analyzer import SentimentAnalyzer
