import json
import hashlib
from datetime import datetime
from src.data.db_manager import db
from src.utils import get_scenario_timestamp


class DataCatalog:
    @property
    def conn(self):
        return db.get_connection("feature_store")

    def record_schema(self, db_name="ecosystem"):
        conn = db.get_connection(db_name)
        cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cur.fetchall()
        catalog = {}
        for t in tables:
            tname = t["name"]
            cur2 = conn.execute(f"PRAGMA table_info({tname})")
            cols = cur2.fetchall()
            schema = [{"name": c["name"], "type": c["type"], "notnull": bool(c["notnull"]),
                       "pk": bool(c["pk"])} for c in cols]
            cur3 = conn.execute(f"SELECT COUNT(*) as cnt FROM {tname}")
            row_count = cur3.fetchone()["cnt"]
            catalog[tname] = {"schema": schema, "row_count": row_count}
        self.conn.execute(
            "INSERT INTO data_catalog (db_name, table_name, schema_json, row_count) VALUES (?, ?, ?, ?)",
            (db_name, "__full_schema__", json.dumps(catalog), sum(t["row_count"] for t in catalog.values()))
        )
        self.conn.commit()
        return catalog

    def detect_schema_changes(self, db_name="ecosystem"):
        conn = db.get_connection(db_name)
        current = {}
        cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cur.fetchall()
        for t in tables:
            tname = t["name"]
            cur2 = conn.execute(f"PRAGMA table_info({tname})")
            cols = [(c["name"], c["type"]) for c in cur2.fetchall()]
            current[tname] = cols
        row = db.fetch_one("feature_store",
            """SELECT schema_json FROM data_catalog
               WHERE db_name = ? AND table_name = '__full_schema__'
               ORDER BY recorded_at DESC LIMIT 1""",
            (db_name,))
        if not row:
            return {"changed": False, "message": "No prior schema recorded"}
        previous = json.loads(row["schema_json"])
        differences = []
        for tname, cols in current.items():
            prev_cols = {c["name"]: c["type"] for c in previous.get(tname, {}).get("schema", [])}
            curr_cols = dict(cols)
            added = set(curr_cols.keys()) - set(prev_cols.keys())
            removed = set(prev_cols.keys()) - set(curr_cols.keys())
            if added:
                differences.append(f"Table '{tname}' added columns: {added}")
            if removed:
                differences.append(f"Table '{tname}' removed columns: {removed}")
        for tname in set(previous.keys()) - set(current.keys()):
            differences.append(f"Table '{tname}' was dropped")
        if differences:
            return {"changed": True, "differences": differences}
        return {"changed": False, "message": "Schema unchanged"}

    def log_export(self, scenario, dataset_type, file_path, df):
        row_count = len(df)
        cols = list(df.columns)
        schema_snapshot = json.dumps({dataset_type: cols})
        content_hash = hashlib.md5(df.to_csv(index=False).encode()).hexdigest()
        cursor = self.conn.execute(
            "INSERT INTO export_log (scenario, dataset_type, file_path, row_count, checksum, schema_snapshot) VALUES (?, ?, ?, ?, ?, ?)",
            (scenario, dataset_type, str(file_path), row_count, content_hash, schema_snapshot)
        )
        self.conn.commit()
        export_id = cursor.lastrowid
        row = db.fetch_one("feature_store",
            "SELECT * FROM export_log WHERE export_id = ?", (export_id,))
        return dict(row) if row else {"export_id": export_id}

    def get_exports_by_scenario(self, scenario):
        rows = db.fetch_all("feature_store",
            "SELECT * FROM export_log WHERE scenario = ? ORDER BY created_at DESC", (scenario,))
        return rows

    def get_recent_exports(self, limit=20):
        rows = db.fetch_all("feature_store",
            "SELECT * FROM export_log ORDER BY created_at DESC LIMIT ?", (limit,))
        return rows

    def link_training_to_export(self, model_name, version, export_id):
        self.conn.execute(
            "UPDATE training_datasets SET scenario = (SELECT scenario FROM export_log WHERE export_id = ?) WHERE dataset_id = ?",
            (export_id, export_id)
        )
        self.conn.commit()

    def get_lineage(self, model_name, version):
        model_id = None
        row = db.fetch_one("feature_store",
            "SELECT model_id FROM model_registry WHERE model_name = ?", (model_name,))
        if row:
            model_id = row["model_id"]
        if not model_id:
            return {"error": "Model not found"}
        mv = db.fetch_one("feature_store",
            "SELECT * FROM model_versions WHERE model_id = ? AND version = ?", (model_id, version))
        if not mv:
            return {"error": "Version not found"}
        lineage = {
            "model_name": model_name,
            "version": version,
            "metrics": json.loads(mv["metrics"]),
            "hyperparameters": json.loads(mv["hyperparameters"]) if mv["hyperparameters"] else {},
            "trained_at": mv["trained_at"],
        }
        if mv["training_dataset_id"]:
            ds = db.fetch_one("feature_store",
                "SELECT * FROM training_datasets WHERE dataset_id = ?", (mv["training_dataset_id"],))
            if ds:
                lineage["training_dataset"] = dict(ds)
        if mv["feature_snapshot_id"]:
            snap = db.fetch_one("feature_store",
                "SELECT * FROM feature_snapshots WHERE snapshot_id = ?", (mv["feature_snapshot_id"],))
            if snap:
                lineage["feature_snapshot"] = dict(snap)
        return lineage
