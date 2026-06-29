import sqlite3
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("Agg")
from datetime import datetime, date
from src.data.db_manager import db
from src.data.model_registry import ModelRegistry


class ModelMonitor:
    def __init__(self):
        self.registry = ModelRegistry()

    def log_metrics(self, model_name, metrics_dict):
        return self.registry.log_training(model_name, metrics_dict)

    def get_performance_trend(self, model_name, metric="MAE", last_n=10):
        return self.registry.get_performance_trend(model_name, metric, last_n)

    def get_latest_metrics(self, model_name):
        result = self.registry.get_latest_metrics(model_name)
        if result:
            return result.get("metrics", {})
        return {}

    def get_all_model_status(self):
        return self.registry.get_all_model_status()

    def plot_performance_trend(self, model_name, metric, output_path):
        return self.registry.get_performance_trend(model_name, metric, 20)

    def get_staleness(self, model_name, max_days=7):
        return self.registry.get_staleness(model_name, max_days)

    def get_stale_models(self, max_days=7):
        return self.registry.get_stale_models(max_days)

    def close(self):
        pass


def check_and_log_all_models(models_dict, monitor, scenario_name):
    results = {}
    for model_name, model_instance in models_dict.items():
        try:
            metrics = model_instance.train()
            if metrics and isinstance(metrics, dict):
                numeric_metrics = {k: v for k, v in metrics.items() if isinstance(v, (int, float))}
                if numeric_metrics:
                    version = monitor.log_metrics(model_name, numeric_metrics)
                    results[model_name] = {"status": "logged", "version": version, "metrics": numeric_metrics}
                else:
                    results[model_name] = {"status": "no_numeric_metrics", "raw_metrics": metrics}
            else:
                results[model_name] = {"status": "no_metrics_returned"}
        except Exception as e:
            results[model_name] = {"status": "error", "error": str(e)}
    return results
