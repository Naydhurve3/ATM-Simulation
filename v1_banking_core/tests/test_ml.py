import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
import pytest
from banking_core.models import (
    CashDemandForecaster, BankClustering, TransactionPredictor,
    CreditScorer, ChurnPredictor, LoanDefaultModel, BankRecommender
)

SKIP_CASH = not CashDemandForecaster().is_available()
SKIP_TXN = not TransactionPredictor().is_available()

@pytest.mark.skipif(SKIP_CASH, reason="Prophet not installed")
def test_cash_forecast():
    f = CashDemandForecaster()
    result = f.train()
    assert isinstance(result, dict)

def test_clustering():
    bc = BankClustering()
    opt_k, opt_s = bc.get_optimal_k(6)
    assert opt_k > 0

@pytest.mark.skipif(SKIP_TXN, reason="XGBoost not installed")
def test_txn_predict():
    tp = TransactionPredictor()
    result = tp.train()
    assert isinstance(result, dict)

def test_credit_scorer():
    cs = CreditScorer()
    sample = {"age": 30, "balance": 50000, "txn_count": 25,
              "fraud_count": 0, "is_minor": False, "income_bracket": "earning_5L_10L"}
    score = cs.predict(sample)
    assert 300 <= score <= 900

def test_churn():
    cp = ChurnPredictor()
    result = cp.predict({"days_since_last_txn": 5})
    assert "risk_level" in result

def test_loan():
    ldm = LoanDefaultModel()
    user = {"is_minor": False, "age": 30, "credit_score": 750,
            "balance": 50000, "income_bracket": "earning_5L_10L"}
    result = ldm.predict(user, 100000, 10.5, 36)
    assert "risk_level" in result

def test_recommender():
    br = BankRecommender()
    user = {"age": 30, "is_minor": False, "income_bracket": "earning_5L_10L", "preferences": {}}
    recs = br.recommend(user, top_n=3)
    assert len(recs) > 0