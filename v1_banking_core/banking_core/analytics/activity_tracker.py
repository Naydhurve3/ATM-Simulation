"""Lightweight user-activity tracking + snapshot-based churn risk (serverless-friendly).

Design: every meaningful user action is appended to the `user_activity` table with a
single cheap INSERT. Prediction views read a STORED snapshot; the snapshot is only
recomputed on demand (refresh button) or right after a banking action — never during
a page view. No model code (sklearn/joblib) is loaded here at all.
"""

from datetime import date, datetime

from banking_core.data.postgres_adapter import (
    get_ecosystem_conn,
    get_ml_snapshot,
    is_enabled,
    set_ml_snapshot,
)

_ACTIVITY_DDL = """
CREATE TABLE IF NOT EXISTS user_activity (
    activity_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    activity TEXT NOT NULL,
    amount DOUBLE PRECISION DEFAULT 0,
    channel TEXT DEFAULT 'web',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""

_TRACKED_ACTIVITIES = ("deposit", "withdraw", "transfer")

_SNAPSHOT_KIND = "report"


def ensure_activity_table(conn):
    """Dialect-neutral DDL: SERIAL/DOUBLE PRECISION work on PG and sqlite alike."""
    try:
        conn.execute(_ACTIVITY_DDL)
        conn.commit()
        return True
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        return False


def log_activity(conn, user_id, activity, amount=0.0, channel="web"):
    """Append one activity row (single INSERT, never raises)."""
    try:
        ensure_activity_table(conn)
        conn.execute(
            "INSERT INTO user_activity (user_id, activity, amount, channel) "
            "VALUES (?, ?, ?, ?)",
            (user_id, activity, amount, channel),
        )
        conn.commit()
        return True
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        return False


def activity_features(conn, user_id):
    """Summarise the stored activity log for one user (pure SQL + math)."""
    feats = {
        "txn_count": 0, "total_volume": 0.0, "avg_txn": 0.0,
        "days_inactive": 0, "activity_count": 0, "by_type": {},
    }
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT activity, COUNT(*), COALESCE(SUM(amount),0) "
            "FROM user_activity WHERE user_id=? GROUP BY activity",
            (user_id,),
        )
        rows = cur.fetchall()
        if rows:
            total = 0.0
            counts = {}
            for act, cnt, amt in rows:
                counts[str(act)] = int(cnt)
                if str(act) in _TRACKED_ACTIVITIES:
                    total += float(amt or 0)
                    feats["txn_count"] += int(cnt)
            feats["by_type"] = counts
            feats["activity_count"] = sum(counts.values())
            feats["total_volume"] = round(total, 2)
            feats["avg_txn"] = round(total / feats["txn_count"], 2) if feats["txn_count"] else 0.0
        cur.execute("SELECT MAX(created_at) FROM user_activity WHERE user_id=?", (user_id,))
        last = cur.fetchone()[0]
        if last:
            try:
                days = (date.today() - datetime.strptime(str(last)[:10], "%Y-%m-%d").date()).days
                feats["days_inactive"] = max(0, days)
            except Exception:
                pass
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
    return feats


def churn_risk(feats):
    """Rule-based churn score from activity features (no sklearn, no model files)."""
    days = feats.get("days_inactive", 0)
    base = min(days / 90, 1.0) if days > 30 else 0.05
    if feats.get("txn_count", 0) >= 10 and days <= 7:
        base = min(base, 0.10)
    score = round(min(max(base, 0.0), 1.0), 3)
    level = "HIGH" if score > 0.5 else "MEDIUM" if score > 0.25 else "LOW"
    return score, level


def build_churn_snapshot(conn, user_id, balance=0.0):
    """Compute the full churn snapshot dict from stored activity."""
    feats = activity_features(conn, user_id)
    score, level = churn_risk(feats)
    return {
        "risk_score": score,
        "risk_level": level,
        "method": "rule-based",
        "features": feats,
        "balance": round(balance or 0, 2),
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def get_churn_snapshot(user_id):
    """Read the stored snapshot (PG only; sqlite mode always recomputes)."""
    if is_enabled():
        try:
            return get_ml_snapshot(f"churn_snapshot_user_{user_id}", kind=_SNAPSHOT_KIND)
        except Exception:
            return None
    return None


def store_churn_snapshot(user_id, payload):
    if is_enabled():
        try:
            return set_ml_snapshot(f"churn_snapshot_user_{user_id}", payload, kind=_SNAPSHOT_KIND)
        except Exception:
            return False
    return False
