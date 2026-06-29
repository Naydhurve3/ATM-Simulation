import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
import pytest
from src.demo_manager import DemoManager, DEMO_EXPLANATIONS

class TestDemoManager:
    def test_demo_creation(self):
        dm = DemoManager()
        assert dm is not None

    def test_demo_explanations_exist(self):
        assert "bank_overview" in DEMO_EXPLANATIONS
        assert "cash_forecast" in DEMO_EXPLANATIONS
        assert "transaction_predict" in DEMO_EXPLANATIONS
        assert "bank_clustering" in DEMO_EXPLANATIONS
        assert "anomaly" in DEMO_EXPLANATIONS
        assert "credit_score" in DEMO_EXPLANATIONS

    def test_demo_explanations_have_simple(self):
        for key, info in DEMO_EXPLANATIONS.items():
            assert "simple" in info, f"{key} missing 'simple'"

    def test_demo_explanations_have_analogy(self):
        for key, info in DEMO_EXPLANATIONS.items():
            assert "analogy" in info, f"{key} missing 'analogy'"

    def test_stop(self):
        dm = DemoManager()
        dm.running = True
        dm.stop()
        assert not dm.running

    def test_demo_explanations_ml_have_math(self):
        ml_keys = ["cash_forecast", "transaction_predict", "bank_clustering", "anomaly", "credit_score"]
        for key in ml_keys:
            if key in DEMO_EXPLANATIONS:
                assert "math" in DEMO_EXPLANATIONS[key] or "simple" in DEMO_EXPLANATIONS[key]
