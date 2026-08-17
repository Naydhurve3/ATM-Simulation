"""Offline analysis report generator (runs locally / CI, never on serverless).

Computes chart-ready JSON for the One-Click Analysis Report page and per-user
ML snapshots, then stores them in the Neon `ml_snapshots` table via
`set_ml_snapshot`. The web app only reads these JSONB payloads at request
time, so a page load costs a JSON read instead of training models.

Entry points:
    compute_global_report(top_banks_n=3)  -> dict (industry-wide report)
    compute_user_report(user_id)          -> dict (personalized report)
    store_global_report(...)              -> writes granular + combined snapshots
    store_user_report(user_id)            -> writes report_user_<id>

The web routes in PG mode read these snapshots; on a miss they compute the
report once (write-through) so every later visit is instant.
"""
import json
from datetime import datetime, timezone

import numpy as np
import pandas as pd


def _jsonable(obj):
    """JSON-safe conversion of numpy/pandas/Decimal values."""
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
    if hasattr(obj, "item"):  # Decimal & co
        try:
            return float(obj)
        except Exception:
            return str(obj)
    return obj


def _run_model(inst, predict_fn, train_fn=None):
    """Same predict->train->predict fallback the web routes use."""
    try:
        result = predict_fn()
        if result is not None and (not isinstance(result, dict) or "error" not in result):
            return True, result, None
        error = result.get("error") if isinstance(result, dict) else "Empty result"
    except Exception as e:
        error = f"{type(e).__name__}: {e}"
    if train_fn is not None:
        try:
            train_fn()
            result = predict_fn()
            if result is not None and (not isinstance(result, dict) or "error" not in result):
                return True, result, None
            error = result.get("error") if isinstance(result, dict) else "Empty result"
        except Exception as e:
            error = f"{type(e).__name__}: {e}"
    return False, None, error


def _pg_conn():
    from banking_core.data.postgres_adapter import get_pg_connection
    return get_pg_connection()


def _industry_df():
    from banking_core.data.postgres_adapter import get_industry_conn
    conn = get_industry_conn()
    df = pd.read_sql('SELECT * FROM "atm_card_stats"', conn)
    conn.close()
    return df


# ── Personal report ─────────────────────────────────────────

def _feature_context(user, user_id):
    c = _pg_conn().cursor()
    c.execute("SELECT COUNT(*) FROM transactions WHERE user_id=? AND type IN ('withdraw','transfer')", (user_id,))
    txn_count = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM fraud_flags WHERE user_id=?", (user_id,))
    fraud_count = c.fetchone()[0]
    last_active = user.get("last_active") or ""
    days_inactive = 999
    if last_active:
        try:
            from datetime import date
            days_inactive = (date.today() - datetime.strptime(last_active[:10], "%Y-%m-%d").date()).days
        except Exception:
            days_inactive = 0
    return {
        "age": user.get("age") or 25,
        "age_group": user.get("age_group") or "Adult",
        "income_bracket": user.get("income_bracket") or "not_earning_student",
        "balance": user.get("balance") or 5000,
        "txn_count": txn_count,
        "fraud_count": fraud_count,
        "days_inactive": days_inactive,
        "bank": user.get("bank") or "",
        "credit_score": user.get("credit_score") or 600,
        "is_minor": bool(user.get("is_minor", False)),
    }


def _income_amount(bracket):
    low_map = {
        "not_earning_student": 0, "not_earning_homemaker": 0, "not_earning_unemployed": 0,
        "not_earning_retired": 0, "earning_under_2.5L": 200000, "earning_2.5L_5L": 375000,
        "earning_5L_10L": 750000, "earning_10L_25L": 1750000, "earning_25L_plus": 3000000,
    }
    return low_map.get(bracket, 500000)


def _credit_breakdown(account, feats):
    base = 600 if not account.is_minor else 650
    income = min(120, feats["income_bracket"].startswith("earning") * 40 + int(feats["income_bracket"].count("L") * 15))
    balance = min(80, int(account.balance / 50000) * 8)
    activity = min(60, min(feats["txn_count"], 12) * 5)
    fees = -min(40, feats["fraud_count"] * 10)
    breakdown = {"base": base, "income": income, "balance": balance, "activity": activity, "fees": fees}
    total = max(300, min(900, base + income + balance + activity + fees))
    rating = "Excellent" if total >= 750 else "Good" if total >= 650 else "Fair" if total >= 550 else "Poor"
    return breakdown, total, rating


def _savings_suggestions(user_id, account):
    c = _pg_conn().cursor()
    c.execute("SELECT * FROM savings_goals WHERE user_id=? AND is_completed=FALSE", (user_id,))
    cols = [d[0] for d in c.description]
    goals = [dict(zip(cols, r)) for r in c.fetchall()]
    if not goals:
        return [], 0, 0
    total_target = sum(float(g["target_amount"]) for g in goals)
    total_current = sum(float(g["current_amount"] or 0) for g in goals)
    suggestions = []
    for g in goals:
        progress = (float(g["current_amount"] or 0) / float(g["target_amount"]) * 100) if float(g["target_amount"]) > 0 else 0
        months_left = 12
        if g.get("deadline"):
            try:
                dl = datetime.strptime(str(g["deadline"])[:10], "%Y-%m-%d").date()
                from datetime import date
                months_left = max(1, round((dl - date.today()).days / 30.44))
            except Exception:
                months_left = 12
        monthly = (float(g["target_amount"]) - float(g["current_amount"] or 0)) / months_left if months_left else 0
        suggestions.append({
            "goal_name": g.get("goal_name"),
            "target_amount": round(float(g["target_amount"]), 0),
            "current_amount": round(float(g["current_amount"] or 0), 0),
            "progress": round(progress, 1),
            "suggested_monthly": round(monthly, 0),
            "months_left": months_left,
        })
    return suggestions, total_target, total_current


def _user_txns(user_id):
    c = _pg_conn().cursor()
    c.execute("SELECT * FROM transactions WHERE user_id=? ORDER BY timestamp DESC LIMIT 200", (user_id,))
    cols = [d[0] for d in c.description]
    return [dict(zip(cols, r)) for r in c.fetchall()]


def compute_user_report(user_id):
    """Personalized ML + analytics snapshot for one user (chart-ready JSON)."""
    from banking_core.services import UserService
    from banking_core.services.atm_service import ATMService

    report = {}
    try:
        user = UserService().get_user(user_id)
        account = ATMService().get_account(user_id)
        if not user or not account:
            return report
        feats = _feature_context(user, user_id)
        report["profile"] = {
            "name": user.get("name"), "bank": user.get("bank"), "account_type": user.get("account_type"),
            "age": feats["age"], "age_group": feats["age_group"],
            "income_bracket": feats["income_bracket"],
        }
        report["generated_at"] = datetime.now(timezone.utc).isoformat()

        try:
            c = _pg_conn().cursor()
            c.execute("SELECT COUNT(*) as n, COALESCE(SUM(amount),0) as tot, AVG(amount) as avg_amt "
                      "FROM transactions WHERE user_id=? AND type IN ('withdraw','transfer')", (user_id,))
            row = c.fetchone()
            report["stats"] = {"txn_count": row[0], "total_spent": row[1], "avg_amount": row[2]}
        except Exception:
            pass

        try:
            c = _pg_conn().cursor()
            c.execute("""SELECT TO_CHAR(timestamp, 'YYYY-MM') as month, type, SUM(amount) as total
                         FROM transactions WHERE user_id=? GROUP BY month, type ORDER BY month LIMIT 6""", (user_id,))
            cols = [d[0] for d in c.description]
            report["monthly"] = [dict(zip(cols, r)) for r in c.fetchall()]
        except Exception:
            pass

        breakdown, total, rating = _credit_breakdown(account, feats)
        report["credit"] = {"breakdown": breakdown, "total": total, "rating": rating}

        try:
            from banking_core.models import CreditScorer
            cs = CreditScorer()
            ok, res, err = _run_model(cs, lambda: cs.predict({
                "age": feats["age"], "income_bracket": feats["income_bracket"],
                "balance": account.balance, "txn_count": feats["txn_count"]}), cs.train)
            report["credit_ml"] = res if ok else {"error": err}
        except Exception as e:
            report["credit_ml"] = {"error": str(e)}

        try:
            from banking_core.models import ChurnPredictor
            cp = ChurnPredictor()
            ok, res, err = _run_model(cp, lambda: cp.predict({
                "age": feats["age"], "income_bracket": feats["income_bracket"],
                "balance": account.balance, "txn_count": feats["txn_count"],
                "days_inactive": feats["days_inactive"]}), cp.train)
            report["churn"] = res if ok else {"error": err}
        except Exception as e:
            report["churn"] = {"error": str(e)}

        try:
            from banking_core.models import LoanDefaultModel
            lm = LoanDefaultModel()
            ok, res, err = _run_model(lm, lambda: lm.predict({
                "credit_score": feats["credit_score"], "balance": feats["balance"],
                "age": feats["age"], "income_bracket": feats["income_bracket"]},
                200000, 10.0, 24), lm.train)
            loan = {"params": {"amount": 200000, "rate": 10.0, "tenure": 24}}
            if ok:
                loan["result"] = res
                try:
                    sched = lm.generate_amortization_schedule(200000, 10.0, 24)
                    if isinstance(sched, list) and sched:
                        loan["emi"] = round(float(sched[0].get("payment", 0)), 0)
                        loan["total_interest"] = round(sum(float(s.get("interest", 0)) for s in sched), 0)
                        loan["total_payment"] = loan["emi"] * len(sched)
                except Exception:
                    pass
            else:
                loan["error"] = err
            report["loan"] = loan
        except Exception as e:
            report["loan"] = {"error": str(e)}

        try:
            from banking_core.models import BankRecommender
            br = BankRecommender()
            ok, res, err = _run_model(br, lambda: br.recommend({
                "age": feats["age"], "income_bracket": feats["income_bracket"],
                "balance": account.balance, "bank": account.bank}, 5), br.train)
            report["bankrec"] = {"banks": res[:5]} if ok and isinstance(res, list) else {"error": err}
        except Exception as e:
            report["bankrec"] = {"error": str(e)}

        try:
            from banking_core.models import RFMSegmenter
            txns = _user_txns(user_id)
            if txns:
                rfm = RFMSegmenter()
                result = rfm.segment(txns)
                if result:
                    result["behavior"] = rfm.get_segment_behavior(result.get("segment")) if result.get("segment") else None
                report["rfm"] = result
        except Exception as e:
            report["rfm"] = {"error": str(e)}

        try:
            from banking_core.models import InvestmentRecommender
            ir = InvestmentRecommender()
            result = ir.recommend(age=user["age"], income_bracket=feats["income_bracket"],
                                  balance=account.balance, risk_tolerance="moderate")
            products = result.get("products", []) if isinstance(result, dict) else []
            report["investments"] = {
                "products": [{
                    "product_key": p.get("product_key", ""),
                    "name": p.get("name", ""),
                    "category": p.get("product_key", "Product"),
                    "allocation_pct": p.get("allocation_pct", 0),
                    "amount": p.get("amount", 0),
                    "expected_return_pct": p.get("expected_return_pct", 0),
                } for p in products],
                "total_yearly": result.get("total_expected_return_yearly", 0) if isinstance(result, dict) else 0,
            }
        except Exception as e:
            report["investments"] = {"error": str(e)}

        try:
            from banking_core.models import SpendingForecaster
            sf = SpendingForecaster()
            ok, res, err = _run_model(sf, lambda: sf.predict(user_id, {
                "age": feats["age"], "income_bracket": feats["income_bracket"],
                "balance": account.balance}), sf.train)
            report["forecast"] = res if ok else {"error": err}
        except Exception as e:
            report["forecast"] = {"error": str(e)}

        try:
            from banking_core.data_analysis import DataAnalysis
            comparison = DataAnalysis().user_vs_industry({"bank": account.bank, "balance": account.balance,
                                                          "age_group": account.age_group})
            report["user_vs_industry"] = comparison
        except Exception as e:
            report["user_vs_industry"] = {"error": str(e)}

        try:
            suggestions, total_target, total_current = _savings_suggestions(user_id, account)
            report["savings"] = {
                "suggestions": suggestions,
                "total_target": round(total_target, 0),
                "total_current": round(total_current, 0),
            }
        except Exception:
            pass

        return _jsonable(report)
    except Exception:
        return _jsonable(report)


# ── Global (industry) report ─────────────────────────────────

def _decompose_components(ta, bank, metric):
    ok, res, err = _run_model(ta, lambda: ta.decompose(bank, metric))
    if not ok:
        return None, err
    comps = res
    return {
        "months": [d.strftime("%b") for d in comps.trend.index],
        "observed": [None if pd.isna(x) else round(float(x), 2) for x in comps.observed],
        "trend": [None if pd.isna(x) else round(float(x), 2) for x in comps.trend],
        "seasonal": [None if pd.isna(x) else round(float(x), 2) for x in comps.seasonal],
        "resid": [None if pd.isna(x) else round(float(x), 2) for x in comps.resid],
    }, None


def compute_global_report(top_banks_n=3, trend_metric="DC_Vol_Cash_ATM"):
    """Industry-wide report: clusters, anomalies, trends, migration, analytics."""
    report = {}
    try:
        df = _industry_df()
        report["summary"] = {
            "banks": int(df["Bank_Name"].nunique()) if "Bank_Name" in df.columns else 0,
            "months": int(df["Reporting_Month"].nunique()) if "Reporting_Month" in df.columns else 0,
            "rows": int(len(df)),
            "top_banks": df.groupby("Bank_Name")["DC_Vol_Cash_ATM"].sum().sort_values(ascending=False).head(10).index.tolist() if "Bank_Name" in df.columns else [],
        }
    except Exception as e:
        report["summary"] = {"error": str(e)}

    banks = report.get("summary", {}).get("top_banks", [])[:top_banks_n]

    try:
        from banking_core.models import BankClustering
        bc = BankClustering()
        try:
            optimal = bc.get_optimal_k(10)
        except Exception:
            optimal = None
        ok, res, err = _run_model(bc, lambda: bc.get_cluster_profiles(), lambda: bc.train(k=4))
        report["clustering"] = {"profiles": res if ok else None, "optimal_k": optimal,
                                "error": None if ok else err}
    except Exception as e:
        report["clustering"] = {"error": str(e)}

    try:
        from banking_core.models import AnomalyDetector
        ad = AnomalyDetector()
        ok, res, err = _run_model(ad, lambda: ad.get_flagged_banks(15),
                                  lambda: ad.train(contamination=0.05))
        flagged = res if ok else None
        monthly = None
        if ok:
            try:
                monthly = ad.get_monthly_anomalies()
            except Exception:
                monthly = None
        report["anomaly"] = {"flagged": flagged, "monthly": monthly, "error": None if ok else err}
    except Exception as e:
        report["anomaly"] = {"error": str(e)}

    trends = []
    try:
        from banking_core.models import TrendAnalyzer
        ta = TrendAnalyzer()
        for bank in banks:
            comps, err = _decompose_components(ta, bank, trend_metric)
            if comps:
                trends.append({"bank": bank, "metric": trend_metric, "components": comps})
    except Exception as e:
        report["trend_error"] = str(e)
    report["trend"] = trends

    migrations = []
    try:
        from banking_core.models import ChannelMigrationPredictor
        for bank in banks:
            cm = ChannelMigrationPredictor()
            ok, res, err = _run_model(cm, lambda: cm.predict(bank, 6), lambda: cm.train(bank))
            if ok:
                migrations.append({"bank": bank, "months": 6, "prediction": res})
    except Exception as e:
        report["migration_error"] = str(e)
    report["migration"] = migrations

    try:
        from banking_core.models import WhatIfSimulator
        ws = WhatIfSimulator()
        ok, res, err = _run_model(ws, lambda: ws.simulate({}), lambda: ws.train())
        report["whatif"] = res if ok else {"error": err}
    except Exception as e:
        report["whatif"] = {"error": str(e)}

    try:
        from banking_core.models import ATMReplenishmentOptimizer
        opt = ATMReplenishmentOptimizer()
        result = opt.optimize(100000, 300000, 500, 0.12)
        cmp = opt.compare_strategies(100000)
        report["replenishment"] = {
            "result": result, "comparison": cmp.get("strategies", []),
            "best_strategy": cmp.get("best_strategy"),
        }
    except Exception as e:
        report["replenishment"] = {"error": str(e)}

    try:
        from banking_core.data_analysis import DataAnalysis
        da = DataAnalysis()
        ms = da.market_share()
        ms = ms.head(8)
        rest = da.market_share()["Share_%"].iloc[8:].sum()
        report["market_share"] = {
            "labels": ms["Bank_Name"].tolist() + (["Others"] if rest > 0 else []),
            "values": ms["Share_%"].tolist() + ([round(float(rest), 2)] if rest > 0 else []),
        }
        cb = da.channel_breakdown()
        labels = list(cb.keys())
        report["channel_breakdown"] = {
            "labels": labels,
            "values": [int(cb[k]["Vol"]) for k in labels],
        }
        gr = da.growth_rate()
        report["growth"] = {
            "months": [str(m) for m in gr["Reporting_Month"].tolist()],
            "values": [None if pd.isna(x) else round(float(x), 2) for x in gr["MoM_Growth_%"].tolist()],
        }
        corr = da.correlation_matrix()
        labels_c = [str(c) for c in corr.columns]
        report["correlation"] = {
            "labels": labels_c,
            "matrix": [[None if str(c) != str(r) else round(float(corr.loc[r, c]), 2)
                        for c in corr.columns] for r in corr.index],
        }
        ms_df = da.market_share()
        report["market_share_records"] = ms_df.to_dict(orient="records")
        report["top_banks_records"] = [
            {"Bank_Name": k, "Total_Txn_Vol": v} for k, v in da.top_banks(metric="Total_Txn_Vol", n=10).items()
        ]
        cb = da.channel_breakdown()
        report["channel_records"] = [
            {"channel": k, "vol": v.get("Vol", 0), "val": v.get("Val", 0)} for k, v in cb.items()
        ]
        gr_df = da.growth_rate()
        report["growth_records"] = [
            {"Reporting_Month": r["Reporting_Month"],
             "MoM_Growth_%": None if pd.isna(r["MoM_Growth_%"]) else round(float(r["MoM_Growth_%"]), 2)}
            for r in gr_df.to_dict(orient="records")
        ]
        trend_df = da.monthly_trend()
        report["monthly_trend_records"] = [
            {"Reporting_Month": r["Reporting_Month"], "Total_Txn_Vol": int(r["Total_Txn_Vol"])}
            for r in trend_df.to_dict(orient="records")
        ]
        overviews = []
        for bank in da.get_banks():
            try:
                overviews.append(da.bank_overview(bank))
            except Exception:
                pass
        report["overviews"] = overviews
        compare_presets = {
            "PSU": ["STATE BANK OF INDIA", "BANK OF BARODA", "PUNJAB NATIONAL BANK", "CANARA BANK"],
            "Private": ["HDFC BANK LTD", "ICICI BANK LTD", "AXIS BANK LTD", "KOTAK MAHINDRA BANK LTD"],
            "Volume": ["STATE BANK OF INDIA", "HDFC BANK LTD", "ICICI BANK LTD", "AXIS BANK LTD"],
        }
        report["compare"] = {}
        for preset_name, preset_banks in compare_presets.items():
            try:
                cmp_df = da.compare_banks(preset_banks)
                report["compare"][preset_name] = {
                    "banks": preset_banks,
                    "result": cmp_df.to_dict(orient="records"),
                }
            except Exception:
                pass
    except Exception as e:
        report["analytics_error"] = str(e)

    report["generated_at"] = datetime.now(timezone.utc).isoformat()
    return _jsonable(report)


# ── Storage helpers ──────────────────────────────────────────

def _set(name, payload, bank=None, metric=None, kind="json"):
    from banking_core.data.postgres_adapter import set_ml_snapshot
    return set_ml_snapshot(name, payload, bank=bank, metric=metric, kind=kind)


def store_global_report(report, top_banks_n=3):
    """Persist granular snapshots (for the ML pages) + the combined report."""
    stored = []
    if report.get("clustering"):
        stored.append(_set("analysis_clustering", report["clustering"], kind="report"))
    if report.get("anomaly"):
        stored.append(_set("analysis_anomaly", report["anomaly"], kind="report"))
    if report.get("replenishment"):
        stored.append(_set("analysis_replenishment", report["replenishment"], kind="report"))
    if report.get("market_share"):
        stored.append(_set("analysis_marketshare", report["market_share"], kind="report"))
    if report.get("market_share_records"):
        stored.append(_set("analysis_marketshare", {
            "records": report["market_share_records"],
            "top_banks": report.get("top_banks_records", []),
        }, kind="report"))
    if report.get("channel_breakdown"):
        stored.append(_set("analysis_channel", report["channel_breakdown"], kind="report"))
    if report.get("channel_records"):
        stored.append(_set("analysis_channel", {"channels": report["channel_records"]}, kind="report"))
    if report.get("growth"):
        stored.append(_set("analysis_growth", report["growth"], kind="report"))
    if report.get("growth_records"):
        stored.append(_set("analysis_growth", {"records": report["growth_records"]}, kind="report"))
    if report.get("correlation"):
        stored.append(_set("analysis_correlation", report["correlation"], kind="report"))
    if report.get("monthly_trend_records"):
        stored.append(_set("analysis_monthly_trend", {"records": report["monthly_trend_records"]}, kind="report"))
    if report.get("overviews"):
        stored.append(_set("analysis_overviews", {"banks": report["overviews"]}, kind="report"))
    if report.get("compare"):
        stored.append(_set("analysis_compare", {"presets": report["compare"]}, kind="report"))
    if report.get("whatif"):
        stored.append(_set("analysis_whatif", report["whatif"], kind="baseline"))
    for t in report.get("trend", []):
        stored.append(_set("analysis_trend", t, bank=t.get("bank"), metric=t.get("metric"), kind="decompose"))
    for m in report.get("migration", []):
        stored.append(_set("analysis_migration", m, bank=m.get("bank"), kind="predict"))
    stored.append(_set("analysis_report", report, kind="report"))
    return sum(1 for s in stored if s)


def store_user_report(user_id, report):
    return _set(f"report_user_{user_id}", report, kind="report")
