"""Precompute the One-Click Analysis Report + per-user ML snapshots into Neon.

The web app (Vercel serverless) never trains models — it reads these JSONB
snapshots, so a page load costs a JSON read instead of 200-500 MB of ML.

Usage (from repo root, ds_gpu env; DATABASE_URL read from .env.local):
    python v3_web/scripts/precompute_analysis.py [--banks N] [--users uid,uid]
                                                [--forecasts] [--forecast-banks N]

    --banks           banks used for trend/migration sections (default 3)
    --users           comma-separated user ids; default: ALL users
    --forecasts       also refresh cash-demand/lstm/txn-volume snapshots
    --forecast-banks  banks for the forecast snapshots (default 10)
"""
import os
import sys
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "v1_banking_core"))


def _load_dotenv_local():
    if os.environ.get("DATABASE_URL"):
        return
    path = os.path.join(ROOT, ".env.local")
    if not os.path.exists(path):
        print("WARN: no DATABASE_URL and no .env.local found")
        return
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            if key.strip() == "DATABASE_URL":
                os.environ["DATABASE_URL"] = val.strip().strip('"').strip("'")
                print("DATABASE_URL loaded from .env.local")


def main():
    argv = sys.argv[1:]
    def arg_flag(name, default):
        if name in argv:
            return argv[argv.index(name) + 1]
        return default

    banks_n = int(arg_flag("--banks", "3"))
    forecast_banks = int(arg_flag("--forecast-banks", "10"))
    users_arg = arg_flag("--users", "")
    do_forecasts = "--forecasts" in argv

    _load_dotenv_local()
    from banking_core.data.postgres_adapter import init_db, get_pg_connection
    from banking_core.analytics.report_generator import (
        compute_global_report, store_global_report, compute_user_report, store_user_report,
    )

    t0 = time.time()
    init_db()

    print(f"[global] computing analysis report (banks={banks_n}) ...", flush=True)
    report = compute_global_report(top_banks_n=banks_n)
    n = store_global_report(report)
    print(f"[global] stored {n} snapshots "
          f"(summary keys: {', '.join(sorted(report.keys()))})", flush=True)
    print(f"[global] payload size ~{len(str(report)) // 1024} KB", flush=True)

    if do_forecasts:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import precompute_ml_snapshots as legacy
        metrics = legacy.real_metrics()
        banks = legacy.top_banks(forecast_banks)
        print(f"[forecast] {len(banks)} banks x {len(metrics)} metrics "
              f"(prophet + lstm + xgboost) ...", flush=True)
        for bank in banks:
            for metric in metrics:
                try:
                    legacy.snapshot_cash_demand(bank, metric)
                except Exception as e:
                    print(f"  ! cash_demand {bank} {metric}: {e}")
                try:
                    legacy.snapshot_lstm(bank, metric)
                except Exception as e:
                    print(f"  ! lstm {bank} {metric}: {e}")
        for metric in metrics:
            try:
                legacy.snapshot_txn_volume(metric)
            except Exception as e:
                print(f"  ! txn_volume {metric}: {e}")

    conn = get_pg_connection()
    cur = conn.cursor()
    if users_arg:
        cur.execute("SELECT user_id FROM users WHERE user_id::text = ANY(%s)",
                    (users_arg.split(","),))
    else:
        cur.execute("SELECT user_id FROM users")
    user_ids = [r[0] for r in cur.fetchall()]
    conn.close()
    print(f"[users] {len(user_ids)} user(s): {user_ids}", flush=True)
    for uid in user_ids:
        try:
            rep = compute_user_report(uid)
            ok = store_user_report(uid, rep)
            print(f"[user:{uid}] stored={ok} keys={', '.join(sorted(rep.keys()))}", flush=True)
        except Exception as e:
            print(f"  ! user {uid}: {e}")

    print(f"DONE in {round(time.time() - t0, 1)}s")


if __name__ == "__main__":
    main()
