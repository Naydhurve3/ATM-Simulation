import sqlite3
from datetime import datetime, date
from src.utils import ECOSYSTEM_DB
from src.data.db_manager import db
from src.data.model_registry import ModelRegistry
from rich.console import Console
from rich.table import Table
from rich import box

console = Console()


class AutoRetrainScheduler:
    def __init__(self, txn_threshold=50, user_threshold=5, days_threshold=7):
        self.txn_threshold = txn_threshold
        self.user_threshold = user_threshold
        self.days_threshold = days_threshold
        self.registry = ModelRegistry()

    @property
    def conn(self):
        return db.get_connection("ecosystem")

    def check_triggers(self, user_manager):
        cur = self.conn.execute("SELECT COUNT(*) FROM transactions")
        txn_count = cur.fetchone()[0]
        cur = self.conn.execute("SELECT COUNT(*) FROM users")
        user_count = cur.fetchone()[0]
        model_statuses = self.registry.get_all_model_status()
        latest_trained = None
        for name, info in model_statuses.items():
            if info["version"] is not None and info["last_trained"]:
                d = datetime.strptime(info["last_trained"][:10], "%Y-%m-%d").date()
                if latest_trained is None or d > latest_trained:
                    latest_trained = d
        reasons = []
        days_since_last_retrain = None
        if latest_trained is not None:
            days_since_last_retrain = (date.today() - latest_trained).days
        else:
            days_since_last_retrain = 999
            reasons.append("No previous retrain found")
        if days_since_last_retrain >= self.days_threshold:
            reasons.append(f"Days since last retrain ({days_since_last_retrain}) >= threshold ({self.days_threshold})")
        if txn_count >= self.txn_threshold:
            reasons.append(f"Transaction count ({txn_count}) >= threshold ({self.txn_threshold})")
        if user_count >= self.user_threshold:
            reasons.append(f"User count ({user_count}) >= threshold ({self.user_threshold})")
        should_retrain = len(reasons) > 0
        return {
            "should_retrain": should_retrain,
            "reasons": reasons,
            "txn_count": txn_count,
            "user_count": user_count,
            "days_since_last_retrain": days_since_last_retrain,
        }

    def log_retrain(self, model_name, triggered_by, version, txn_count, user_count):
        self.registry.log_retrain_event(model_name, triggered_by, version, txn_count, user_count)

    def retrain_if_needed(self, user_manager, models_dict):
        triggers = self.check_triggers(user_manager)
        if not triggers["should_retrain"]:
            return {"retrained": False, "models_retrained": [], "triggers": []}
        models_retrained = []
        for model_name, model_instance in models_dict.items():
            try:
                metrics = model_instance.train()
                if metrics and isinstance(metrics, dict):
                    numeric_metrics = {k: v for k, v in metrics.items() if isinstance(v, (int, float))}
                    if numeric_metrics:
                        version = self.registry.log_training(model_name, numeric_metrics)
                        self.registry.log_retrain_event(model_name, "auto", version, triggers["txn_count"], triggers["user_count"])
                        models_retrained.append(model_name)
            except Exception:
                pass
        return {
            "retrained": True,
            "models_retrained": models_retrained,
            "triggers": triggers["reasons"],
        }

    def get_freshness_report(self, model_monitor=None):
        return self.registry.get_freshness_report()

    def get_model_freshness_status(self, model_monitor=None):
        statuses = self.registry.get_all_model_status()
        total = len(statuses)
        fresh_count = 0
        stale_models = []
        for name, info in statuses.items():
            if info["version"] is None:
                continue
            days = info["freshness_days"]
            if days < 3:
                fresh_count += 1
            if days > 7:
                stale_models.append(name)
        stal = total - fresh_count
        return {
            "total_models": total,
            "fresh_count": fresh_count,
            "stale_count": stal,
            "stale_models": stale_models,
        }

    def close(self):
        pass
