import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
from src.models.cash_demand_forecaster import CashDemandForecaster
from src.models.bank_clustering import BankClustering
from src.models.transaction_predictor import TransactionPredictor
from src.models.credit_scorer import CreditScorer
from src.models.churn_predictor import ChurnPredictor
from src.models.loan_default_model import LoanDefaultModel
from src.models.bank_recommender import BankRecommender

def test_cash_forecast():
    f = CashDemandForecaster()
    result = f.train()
    print("Cash Demand Metrics:", result)
    pred = f.predict()
    print("Prediction:", pred)

def test_clustering():
    bc = BankClustering()
    opt_k, opt_s = bc.get_optimal_k(6)
    print("Optimal K:", opt_k, "Score:", round(opt_s, 4))
    results = bc.train(k=opt_k)
    print("Clusters:", results["Cluster"].value_counts().to_dict())
    print("Silhouette:", bc.metrics["silhouette_score"])

def test_txn_predict():
    tp = TransactionPredictor()
    result = tp.train()
    print("XGBoost Metrics:", result)
    imp = tp.get_feature_importance()
    print("Top features:", dict(list(imp.items())[:3]))

def test_credit_scorer():
    cs = CreditScorer()
    sample = {"age": 30, "balance": 50000, "txn_count": 25,
              "fraud_count": 0, "is_minor": False, "income_bracket": "earning_5L_10L"}
    score = cs.predict(sample)
    print(f"Credit Score: {score}/900")
    assert 300 <= score <= 900

def test_churn():
    cp = ChurnPredictor()
    result = cp.predict({"days_since_last_txn": 5})
    print(f"Churn Risk: {result['risk_score']} ({result['risk_level']})")

def test_loan():
    ldm = LoanDefaultModel()
    user = {"is_minor": False, "age": 30, "credit_score": 750,
            "balance": 50000, "income_bracket": "earning_5L_10L"}
    result = ldm.predict(user, 100000, 10.5, 36)
    print(f"Loan Risk: {result['risk_score']} ({result['risk_level']})")

def test_recommender():
    br = BankRecommender()
    user = {"age": 30, "is_minor": False, "income_bracket": "earning_5L_10L", "preferences": {}}
    recs = br.recommend(user, top_n=3)
    print("Recommendations:", recs)

if __name__ == "__main__":
    print("=== Testing All Models ===\n")
    test_cash_forecast()
    print()
    test_clustering()
    print()
    test_txn_predict()
    print()
    test_credit_scorer()
    print()
    test_churn()
    print()
    test_loan()
    print()
    test_recommender()
    print("\nAll ML tests passed!")
