"""Precompute ML snapshots into Neon for the serverless (Netlify) deployment.

Heavy models (Prophet, TensorFlow LSTM, XGBoost) cannot run in the 10s
Netlify function budget, so we train locally against Neon and store the
results in the `ml_snapshots` table. The web routes read snapshots in PG mode.

Usage (from repo root, with the ds_gpu env):
    set DATABASE_URL=...  (or rely on .env.local)
    python v3_web/scripts/precompute_ml_snapshots.py [--banks N]
"""
import os
import sys
import json
import time
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "v1_banking_core"))

import numpy as np
import pandas as pd

from banking_core.data.postgres_adapter import init_db, get_industry_conn, set_ml_snapshot

METRICS = ["DC_Vol_Cash_ATM", "DC_Vol_Card_Txn", "CBS_Vol", "DD_Vol", "PO_Vol"]


def real_metrics():
    conn = get_industry_conn()
    cur = conn.cursor()
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = %s", ("atm_card_stats",))
    cols = {r[0] for r in cur.fetchall()}
    conn.close()
    return [m for m in METRICS if m in cols] or METRICS[:1]


def _jsonable(obj):
    if isinstance(obj, dict):
        return {k: _jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_jsonable(v) for v in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if isinstance(obj, (pd.Timestamp, datetime, np.datetime64)):
        return str(obj)
    if isinstance(obj, float) and (np.isnan(obj) or np.isinf(obj)):
        return None
    return obj


def top_banks(n=10):
    conn = get_industry_conn()
    df = pd.read_sql(
        "SELECT \"Bank_Name\", SUM(\"DC_Vol_Cash_ATM\") AS vol "
        "FROM atm_card_stats GROUP BY \"Bank_Name\" ORDER BY vol DESC LIMIT %s",
        conn, params=(n,))
    conn.close()
    return df["Bank_Name"].tolist()


def snapshot_cash_demand(bank, metric):
    from banking_core.models import CashDemandForecaster
    fc = CashDemandForecaster()
    m = fc.train(bank, metric)
    if isinstance(m, dict) and m.get("error"):
        return
    pred = fc.predict(bank, metric)
    if isinstance(pred, dict) and pred.get("error"):
        return
    forecast = []
    try:
        comps = fc.get_components(bank, metric)
        if comps is not None:
            for _, r in comps.iterrows():
                forecast.append({"ds": str(r["ds"].date()) if hasattr(r["ds"], "date") else str(r["ds"]),
                                 "yhat": round(float(r["yhat"]), 2)})
    except Exception:
        forecast = []
    payload = {
        "predicted_value": _jsonable(pred.get("predicted_value")),
        "lower_bound": _jsonable(pred.get("lower_bound")),
        "upper_bound": _jsonable(pred.get("upper_bound")),
        "next_month": pred.get("next_month", "Next Month"),
        "forecast": forecast[-13:],
        "metrics": _jsonable(m),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "model": "prophet",
    }
    set_ml_snapshot("cash_demand", payload, bank=bank, metric=metric, kind="forecast")


def snapshot_lstm(bank, metric):
    from banking_core.models import LSTMForecaster
    lf = LSTMForecaster()
    lf.train(bank, metric)
    pred = lf.predict(bank, metric)
    if isinstance(pred, dict) and pred.get("error"):
        return
    payload = {
        "predicted_value": _jsonable(pred.get("predicted_value")),
        "lower_bound": _jsonable(pred.get("lower_bound")),
        "upper_bound": _jsonable(pred.get("upper_bound")),
        "next_month": pred.get("next_month", "Next Month"),
        "metrics": _jsonable(getattr(lf, "metrics", {})),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "model": "lstm",
    }
    set_ml_snapshot("lstm", payload, bank=bank, metric=metric, kind="forecast")


def snapshot_txn_volume(metric):
    from banking_core.models import TransactionPredictor
    tp = TransactionPredictor()
    m = tp.train(metric)
    if isinstance(m, dict) and m.get("error"):
        return
    demo = {"Total_Txn_Vol": 5_000_000, "Total_Cards": 3_000_000, "Digital_Share": 45,
            "Cash_Share": 55, "Total_ATMs": 1200, "PoS": 50000}
    row = {c: 0.0 for c in tp.feature_cols}
    for k, v in demo.items():
        if k in row:
            row[k] = v
    features = tp.predict(pd.DataFrame([row]))
    importance = {}
    try:
        imp = tp.get_feature_importance()
        if isinstance(imp, dict):
            importance = {k: float(v) for k, v in imp.items()}
    except Exception:
        pass
    payload = {
        "features": _jsonable(features),
        "importance": importance,
        "metrics": _jsonable(m),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "model": "xgboost",
    }
    set_ml_snapshot("txn_volume", payload, bank=None, metric=metric, kind="predict")


def main():
    n = int(sys.argv[sys.argv.index("--banks") + 1]) if "--banks" in sys.argv else 10
    metrics = real_metrics()
    print(f"Metrics: {metrics}")
    init_db()
    banks = top_banks(n)
    print(f"Banks: {banks}")
    t0 = time.time()
    for bank in banks:
        for metric in metrics:
            print(f"[prophet] {bank} · {metric} ...", flush=True)
            try:
                snapshot_cash_demand(bank, metric)
            except Exception as e:
                print(f"  ! {e}")
            print(f"[lstm]    {bank} · {metric} ...", flush=True)
            try:
                snapshot_lstm(bank, metric)
            except Exception as e:
                print(f"  ! {e}")
    for metric in metrics:
        print(f"[xgboost] {metric} ...", flush=True)
        try:
            snapshot_txn_volume(metric)
        except Exception as e:
            print(f"  ! {e}")
    print(f"DONE in {round(time.time() - t0, 1)}s")


if __name__ == "__main__":
    main()
