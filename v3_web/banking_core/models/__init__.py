def _lazy(cls_name, module_path, fallback=None):
    """Lazy-import a model class, returning a fallback on failure."""
    try:
        import importlib
        mod = importlib.import_module(module_path)
        return getattr(mod, cls_name)
    except Exception:
        if fallback:
            return fallback
        class _Stub:
            def __init__(self, *a, **kw): self.is_trained = False; self.metrics = {}
            def is_available(self): return False
            def train(self, *a, **kw): return {"error": f"{cls_name} unavailable"}
            def predict(self, *a, **kw): return {"error": f"{cls_name} unavailable"}
            def load(self): return False
            def save(self): pass
            def __call__(self, *a, **kw): return _Stub()
        return _Stub

CashDemandForecaster = _lazy("CashDemandForecaster", "banking_core.models.cash_demand_forecaster")
TransactionPredictor = _lazy("TransactionPredictor", "banking_core.models.transaction_predictor")
BankClustering = _lazy("BankClustering", "banking_core.models.bank_clustering")
AnomalyDetector = _lazy("AnomalyDetector", "banking_core.models.anomaly_detector")
TrendAnalyzer = _lazy("TrendAnalyzer", "banking_core.models.trend_analyzer")
ChannelMigrationPredictor = _lazy("ChannelMigrationPredictor", "banking_core.models.channel_migration")
WhatIfSimulator = _lazy("WhatIfSimulator", "banking_core.models.what_if_simulator")
CreditScorer = _lazy("CreditScorer", "banking_core.models.credit_scorer")
ChurnPredictor = _lazy("ChurnPredictor", "banking_core.models.churn_predictor")
LoanDefaultModel = _lazy("LoanDefaultModel", "banking_core.models.loan_default_model")
BankRecommender = _lazy("BankRecommender", "banking_core.models.bank_recommender")
SpendingForecaster = _lazy("SpendingForecaster", "banking_core.models.spending_forecaster")
LSTMForecaster = _lazy("LSTMForecaster", "banking_core.models.lstm_forecaster")
RealTimeFraudDetector = _lazy("RealTimeFraudDetector", "banking_core.models.real_time_fraud_detector")
InvestmentRecommender = _lazy("InvestmentRecommender", "banking_core.models.investment_recommender")
ATMReplenishmentOptimizer = _lazy("ATMReplenishmentOptimizer", "banking_core.models.atm_replenishment")
RFMSegmenter = _lazy("RFMSegmenter", "banking_core.models.rfm_segmenter")
SavingsGoalOptimizer = _lazy("SavingsGoalOptimizer", "banking_core.models.savings_optimizer")
SentimentAnalyzer = _lazy("SentimentAnalyzer", "banking_core.models.sentiment_analyzer")
