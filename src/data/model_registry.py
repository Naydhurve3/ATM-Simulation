import json
import time
from datetime import datetime, date
from src.data.db_manager import db
from src.utils import DATA_MODELS


class ModelRegistry:
    @property
    def conn(self):
        return db.get_connection("feature_store")

    def register_model(self, model_name, description=""):
        cursor = self.conn.execute(
            "INSERT OR IGNORE INTO model_registry (model_name, description) VALUES (?, ?)",
            (model_name, description)
        )
        self.conn.commit()
        row = db.fetch_one("feature_store",
            "SELECT model_id FROM model_registry WHERE model_name = ?", (model_name,))
        return row["model_id"] if row else None

    def _get_or_create_model_id(self, model_name):
        row = db.fetch_one("feature_store",
            "SELECT model_id FROM model_registry WHERE model_name = ?", (model_name,))
        if row:
            return row["model_id"]
        return self.register_model(model_name)

    def get_next_version(self, model_name):
        model_id = self._get_or_create_model_id(model_name)
        row = db.fetch_one("feature_store",
            "SELECT COALESCE(MAX(version), 0) as max_ver FROM model_versions WHERE model_id = ?",
            (model_id,))
        return row["max_ver"] + 1 if row else 1

    def log_training(self, model_name, metrics, hyperparameters=None,
                     training_dataset_id=None, feature_snapshot_id=None,
                     model_path=None, training_duration_ms=None):
        model_id = self._get_or_create_model_id(model_name)
        version = self.get_next_version(model_name)
        cursor = self.conn.execute(
            """INSERT INTO model_versions
               (model_id, version, hyperparameters, metrics, training_dataset_id,
                feature_snapshot_id, model_path, training_duration_ms)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (model_id, version,
             json.dumps(hyperparameters or {}),
             json.dumps(metrics or {}),
             training_dataset_id,
             feature_snapshot_id,
             model_path,
             training_duration_ms)
        )
        self.conn.commit()
        return version

    def get_version_metrics(self, model_name, version=None):
        model_id = self._get_or_create_model_id(model_name)
        if version:
            row = db.fetch_one("feature_store",
                """SELECT * FROM model_versions
                   WHERE model_id = ? AND version = ?""",
                (model_id, version))
            if row:
                row["metrics"] = json.loads(row["metrics"])
            return row
        rows = db.fetch_all("feature_store",
            """SELECT * FROM model_versions
               WHERE model_id = ?
               ORDER BY version DESC""",
            (model_id,))
        for r in rows:
            r["metrics"] = json.loads(r["metrics"])
        return rows

    def get_latest_metrics(self, model_name):
        model_id = self._get_or_create_model_id(model_name)
        row = db.fetch_one("feature_store",
            """SELECT version, metrics, trained_at FROM model_versions
               WHERE model_id = ? ORDER BY version DESC LIMIT 1""",
            (model_id,))
        if row:
            row["metrics"] = json.loads(row["metrics"])
        return row

    def get_performance_trend(self, model_name, metric_key="MAE", last_n=10):
        model_id = self._get_or_create_model_id(model_name)
        rows = db.fetch_all("feature_store",
            """SELECT version, metrics, trained_at FROM model_versions
               WHERE model_id = ?
               ORDER BY version DESC LIMIT ?""",
            (model_id, last_n))
        trend = []
        for r in reversed(rows):
            metrics = json.loads(r["metrics"])
            val = metrics.get(metric_key)
            if val is not None:
                trend.append({"version": r["version"], metric_key: val, "trained_at": r["trained_at"]})
        return trend

    def promote_to_production(self, model_name, version, notes=""):
        self.conn.execute(
            "UPDATE model_versions SET is_production = 0 WHERE model_id = (SELECT model_id FROM model_registry WHERE model_name = ?)",
            (model_name,))
        self.conn.execute(
            "UPDATE model_versions SET is_production = 1 WHERE model_id = (SELECT model_id FROM model_registry WHERE model_name = ?) AND version = ?",
            (model_name, version))
        self.conn.execute(
            "INSERT INTO production_log (model_name, version, notes) VALUES (?, ?, ?)",
            (model_name, version, notes))
        self.conn.commit()

    def get_production_version(self, model_name):
        model_id = self._get_or_create_model_id(model_name)
        row = db.fetch_one("feature_store",
            """SELECT * FROM model_versions
               WHERE model_id = ? AND is_production = 1
               ORDER BY version DESC LIMIT 1""",
            (model_id,))
        if row:
            row["metrics"] = json.loads(row["metrics"])
        return row

    def compare_models(self, model_names):
        results = {}
        for name in model_names:
            latest = self.get_latest_metrics(name)
            if latest:
                results[name] = {
                    "version": latest["version"],
                    "metrics": latest["metrics"],
                    "trained_at": latest["trained_at"]
                }
        return results

    def get_staleness(self, model_name, max_days=7):
        latest = self.get_latest_metrics(model_name)
        if not latest:
            return True
        trained_date = datetime.strptime(latest["trained_at"][:10], "%Y-%m-%d").date()
        return (date.today() - trained_date).days > max_days

    def get_stale_models(self, max_days=7):
        rows = db.fetch_all("feature_store",
            "SELECT DISTINCT m.model_name FROM model_registry m")
        return [r["model_name"] for r in rows if self.get_staleness(r["model_name"], max_days)]

    def get_all_model_status(self):
        rows = db.fetch_all("feature_store",
            """SELECT mr.model_name, mv.version, mv.metrics, mv.trained_at
               FROM model_registry mr
               LEFT JOIN model_versions mv ON mv.model_id = mr.model_id
               AND mv.version = (SELECT MAX(mv2.version) FROM model_versions mv2 WHERE mv2.model_id = mr.model_id)
               ORDER BY mr.model_name""")
        statuses = {}
        for r in rows:
            name = r["model_name"]
            if r["version"] is None:
                statuses[name] = {"version": None, "metrics": {}, "freshness_days": None}
                continue
            trained_date = datetime.strptime(r["trained_at"][:10], "%Y-%m-%d").date()
            freshness = (date.today() - trained_date).days
            metrics = json.loads(r["metrics"]) if isinstance(r["metrics"], str) else (r["metrics"] or {})
            statuses[name] = {
                "version": r["version"],
                "metrics_summary": metrics,
                "last_trained": r["trained_at"],
                "freshness_days": freshness
            }
        return statuses

    def get_freshness_report(self):
        statuses = self.get_all_model_status()
        from rich.table import Table
        from rich import box
        table = Table(title="Model Freshness Report", box=box.ROUNDED)
        table.add_column("Model Name", style="cyan")
        table.add_column("Version", style="white")
        table.add_column("Last Trained", style="white")
        table.add_column("Days Since Retrain", style="white")
        table.add_column("Status", style="white")
        for model_name, info in statuses.items():
            if info["version"] is None:
                table.add_row(model_name, "[dim]N/A[/dim]", "[dim]N/A[/dim]", "[dim]N/A[/dim]", "[dim]Untrained[/dim]")
                continue
            days = info["freshness_days"]
            if days < 3:
                status = "[green]Fresh[/green]"
            elif days <= 7:
                status = "[yellow]Moderate[/yellow]"
            else:
                status = "[red]Stale[/red]"
            table.add_row(model_name, str(info["version"]), info["last_trained"][:10], str(days), status)
        return table

    def log_retrain_event(self, model_name, triggered_by, version, txn_count, user_count):
        self.conn.execute(
            """INSERT INTO model_versions
               (model_id, version, hyperparameters, metrics, training_dataset_id)
               VALUES ((SELECT model_id FROM model_registry WHERE model_name = ?), ?, ?, ?, ?)""",
            (model_name, version, json.dumps({"triggered_by": triggered_by}),
             json.dumps({"txn_count": txn_count, "user_count": user_count}), None)
        )
        self.conn.commit()

    def get_model_ids_list(self):
        rows = db.fetch_all("feature_store",
            "SELECT model_name FROM model_registry ORDER BY model_name")
        return [r["model_name"] for r in rows]

    def delete_model(self, model_name):
        model_id = self._get_or_create_model_id(model_name)
        self.conn.execute("DELETE FROM model_versions WHERE model_id = ?", (model_id,))
        self.conn.execute("DELETE FROM model_registry WHERE model_id = ?", (model_id,))
        self.conn.commit()
