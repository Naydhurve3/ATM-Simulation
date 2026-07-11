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

CashDemandForecaster = _lazy("CashDemandForecaster", "src.models.cash_demand_forecaster")
TransactionPredictor = _lazy("TransactionPredictor", "src.models.transaction_predictor")
BankClustering = _lazy("BankClustering", "src.models.bank_clustering")
AnomalyDetector = _lazy("AnomalyDetector", "src.models.anomaly_detector")
TrendAnalyzer = _lazy("TrendAnalyzer", "src.models.trend_analyzer")
ChannelMigrationPredictor = _lazy("ChannelMigrationPredictor", "src.models.channel_migration")
WhatIfSimulator = _lazy("WhatIfSimulator", "src.models.what_if_simulator")
CreditScorer = _lazy("CreditScorer", "src.models.credit_scorer")
ChurnPredictor = _lazy("ChurnPredictor", "src.models.churn_predictor")
LoanDefaultModel = _lazy("LoanDefaultModel", "src.models.loan_default_model")
BankRecommender = _lazy("BankRecommender", "src.models.bank_recommender")
SpendingForecaster = _lazy("SpendingForecaster", "src.models.spending_forecaster")
LSTMForecaster = _lazy("LSTMForecaster", "src.models.lstm_forecaster")
RealTimeFraudDetector = _lazy("RealTimeFraudDetector", "src.models.real_time_fraud_detector")
InvestmentRecommender = _lazy("InvestmentRecommender", "src.models.investment_recommender")
ATMReplenishmentOptimizer = _lazy("ATMReplenishmentOptimizer", "src.models.atm_replenishment")
RFMSegmenter = _lazy("RFMSegmenter", "src.models.rfm_segmenter")
SavingsGoalOptimizer = _lazy("SavingsGoalOptimizer", "src.models.savings_optimizer")
SentimentAnalyzer = _lazy("SentimentAnalyzer", "src.models.sentiment_analyzer")
