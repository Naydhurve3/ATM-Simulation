import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, Response
from functools import wraps

_USE_PG = os.environ.get("DATABASE_URL") is not None

routes_bp = Blueprint("routes", __name__)

# ── Helpers ─────────────────────────────────────────────────

def login_required(view):
    @wraps(view)
    def wrapped(**kwargs):
        if "user_id" not in session:
            flash("Please log in first", "warning")
            return redirect(url_for("auth.login"))
        return view(**kwargs)
    return wrapped


def _svc():
    from src.services.atm_service import ATMService
    return ATMService()


def _acct():
    return _svc().get_account(session["user_id"])


def _conn():
    if _USE_PG:
        from src.data.postgres_adapter import get_pg_connection
        return get_pg_connection()
    from src.data.db_manager import db
    return db.get_connection("ecosystem")


def _c():
    return _conn().cursor()


# ── Index ────────────────────────────────────────────────────

@routes_bp.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("routes.dashboard"))
    return redirect(url_for("auth.login"))


# ── Dashboard ────────────────────────────────────────────────

@routes_bp.route("/dashboard")
@login_required
def dashboard():
    account = _acct()
    if not account:
        flash("Account not found", "error")
        return redirect(url_for("auth.logout"))
    result = _svc().mini_statement(session["user_id"], limit=10)
    transactions = result.get("transactions", [])
    return render_template("dashboard.html", account=account, transactions=transactions)


# ── ATM Operations ───────────────────────────────────────────

@routes_bp.route("/deposit", methods=["GET", "POST"])
@login_required
def deposit():
    if request.method == "POST":
        try:
            amount = float(request.form.get("amount", "").strip())
        except (ValueError, TypeError):
            flash("Invalid amount", "error")
            return render_template("deposit.html")
        result = _svc().deposit(session["user_id"], amount, channel="web")
        if "error" in result:
            flash(result["error"], "error")
            return render_template("deposit.html")
        flash(f"Deposited ₹{amount:,.2f}. New balance: ₹{result['balance_after']:,.2f}", "success")
        return redirect(url_for("routes.dashboard"))
    return render_template("deposit.html")


@routes_bp.route("/withdraw", methods=["GET", "POST"])
@login_required
def withdraw():
    if request.method == "POST":
        try:
            amount = float(request.form.get("amount", "").strip())
        except (ValueError, TypeError):
            flash("Invalid amount", "error")
            return render_template("withdraw.html")
        result = _svc().withdraw(session["user_id"], amount, channel="web")
        if "error" in result:
            flash(result["error"], "error")
            return render_template("withdraw.html")
        flash(f"Withdrew ₹{amount:,.2f}. Remaining: ₹{result['balance_after']:,.2f}", "success")
        return redirect(url_for("routes.dashboard"))
    return render_template("withdraw.html")


@routes_bp.route("/transfer", methods=["GET", "POST"])
@login_required
def transfer():
    if request.method == "POST":
        try:
            amount = float(request.form.get("amount", "").strip())
        except (ValueError, TypeError):
            flash("Invalid amount", "error")
            return render_template("transfer.html")
        target = request.form.get("target_account", "").strip()
        via = request.form.get("via", "neft")
        if not target:
            flash("Target account is required", "error")
            return render_template("transfer.html")
        result = _svc().transfer(session["user_id"], target, amount, via=via, channel="web")
        if "error" in result:
            flash(result["error"], "error")
            return render_template("transfer.html")
        flash(f"Transferred ₹{amount:,.2f} to {target}", "success")
        return redirect(url_for("routes.dashboard"))
    return render_template("transfer.html")


@routes_bp.route("/statement")
@login_required
def statement():
    result = _svc().mini_statement(session["user_id"], limit=100)
    return render_template("statement.html", transactions=result.get("transactions", []))


# ── Profile & PIN ────────────────────────────────────────────

@routes_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    account = _acct()
    if not account:
        return redirect(url_for("auth.logout"))
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        if name and email and phone:
            conn = _conn()
            conn.execute("UPDATE users SET name=?, email=?, phone=? WHERE user_id=?",
                         (name, email, phone, session["user_id"]))
            conn.commit()
            session["user_name"] = name
            flash("Profile updated", "success")
        else:
            flash("All fields required", "error")
        return redirect(url_for("routes.profile"))
    return render_template("profile.html", account=account)


@routes_bp.route("/change-pin", methods=["GET", "POST"])
@login_required
def change_pin():
    if request.method == "POST":
        current = request.form.get("current_pin", "").strip()
        new_pin = request.form.get("new_pin", "").strip()
        confirm = request.form.get("confirm_pin", "").strip()
        if not current or not new_pin or not confirm:
            flash("All fields required", "error")
        elif new_pin != confirm:
            flash("New PINs do not match", "error")
        elif len(new_pin) != 4 or not new_pin.isdigit():
            flash("PIN must be exactly 4 digits", "error")
        else:
            from src.utils import hash_pin
            conn = _conn()
            c = conn.cursor()
            c.execute("SELECT pin_hash FROM users WHERE user_id=?", (session["user_id"],))
            row = c.fetchone()
            if not row or row[0] != hash_pin(current):
                flash("Current PIN is incorrect", "error")
            else:
                conn.execute("UPDATE users SET pin_hash=? WHERE user_id=?",
                             (hash_pin(new_pin), session["user_id"]))
                conn.commit()
                flash("PIN changed successfully", "success")
                return redirect(url_for("routes.profile"))
        return render_template("change_pin.html")
    return render_template("change_pin.html")


# ── Credit Score ─────────────────────────────────────────────

@routes_bp.route("/credit-score")
@login_required
def credit_score():
    account = _acct()
    if not account:
        return redirect(url_for("auth.logout"))
    c = _c()
    c.execute("SELECT * FROM credit_history WHERE user_id=? ORDER BY recorded_at DESC LIMIT 20",
              (session["user_id"],))
    cols = [d[0] for d in c.description]
    return render_template("credit_score.html", account=account, history=[dict(zip(cols, r)) for r in c.fetchall()])


# ── Savings Goals ────────────────────────────────────────────

@routes_bp.route("/savings", methods=["GET", "POST"])
@login_required
def savings():
    conn = _conn()
    if request.method == "POST":
        name = request.form.get("goal_name", "").strip()
        target = request.form.get("target_amount", "").strip()
        deadline = request.form.get("deadline", "").strip()
        if name and target:
            try:
                conn.execute(
                    "INSERT INTO savings_goals (user_id, goal_name, target_amount, deadline) VALUES (?,?,?,?)",
                    (session["user_id"], name, float(target), deadline),
                )
                conn.commit()
                flash("Savings goal created!", "success")
            except Exception as e:
                flash(f"Error: {e}", "error")
        return redirect(url_for("routes.savings"))
    c = conn.cursor()
    c.execute("SELECT * FROM savings_goals WHERE user_id=? ORDER BY created_at DESC", (session["user_id"],))
    cols = [d[0] for d in c.description]
    return render_template("savings.html", goals=[dict(zip(cols, r)) for r in c.fetchall()])


@routes_bp.route("/savings/<int:goal_id>/add", methods=["POST"])
@login_required
def savings_add(goal_id):
    amount = request.form.get("amount", "").strip()
    if amount:
        _conn().execute("UPDATE savings_goals SET current_amount = current_amount + ? WHERE goal_id=? AND user_id=?",
                        (float(amount), goal_id, session["user_id"]))
        _conn().commit()
        flash("Amount added to goal!", "success")
    return redirect(url_for("routes.savings"))


@routes_bp.route("/savings/<int:goal_id>/delete", methods=["POST"])
@login_required
def savings_delete(goal_id):
    _conn().execute("DELETE FROM savings_goals WHERE goal_id=? AND user_id=?", (goal_id, session["user_id"]))
    _conn().commit()
    flash("Goal deleted", "info")
    return redirect(url_for("routes.savings"))


@routes_bp.route("/savings/optimize")
@login_required
def savings_optimize():
    conn = _conn()
    c = conn.cursor()
    c.execute("SELECT * FROM savings_goals WHERE user_id=? AND is_completed=0", (session["user_id"],))
    cols = [d[0] for d in c.description]
    goals = [dict(zip(cols, r)) for r in c.fetchall()]
    account = _acct()
    suggestions = []
    if goals and account:
        total_target = sum(g["target_amount"] for g in goals)
        total_current = sum(g["current_amount"] for g in goals)
        remaining = total_target - total_current
        monthly_available = max(0, account.balance * 0.3)
        months_needed = int(remaining / monthly_available) + 1 if monthly_available > 0 else 99
        for g in goals:
            progress = (g["current_amount"] / g["target_amount"] * 100) if g["target_amount"] > 0 else 0
            alloc = monthly_available * (g["target_amount"] / total_target) if total_target > 0 else 0
            suggestions.append({**g, "progress": round(progress, 1), "suggested_monthly": round(alloc, 0)})
        suggestions.append({"months_needed": months_needed, "monthly_available": round(monthly_available, 0)})
    return render_template("savings_optimize.html", goals=goals, suggestions=suggestions)


# ── Loan Applications ────────────────────────────────────────

@routes_bp.route("/loans", methods=["GET", "POST"])
@login_required
def loans():
    conn = _conn()
    if request.method == "POST":
        loan_type = request.form.get("loan_type", "personal")
        amount = request.form.get("amount", "").strip()
        tenure = request.form.get("tenure", "12").strip()
        if amount:
            try:
                conn.execute(
                    """INSERT INTO loan_applications (user_id, loan_type, amount_requested, tenure_months, status)
                       VALUES (?,?,?,?,'pending')""",
                    (session["user_id"], loan_type, float(amount), int(tenure)),
                )
                conn.commit()
                flash("Loan application submitted!", "success")
            except Exception as e:
                flash(f"Error: {e}", "error")
        return redirect(url_for("routes.loans"))
    c = conn.cursor()
    c.execute("SELECT * FROM loan_applications WHERE user_id=? ORDER BY applied_at DESC", (session["user_id"],))
    cols = [d[0] for d in c.description]
    applications = [dict(zip(cols, r)) for r in c.fetchall()]
    account = _acct()
    loan_offers = []
    if account and account.credit_score >= 650 and account.age_group != "minor":
        loan_offers = [
            {"type": "Personal Loan", "rate": "10.5%", "max": 500000, "tenure": "1-5 years"},
            {"type": "Home Loan", "rate": "8.5%", "max": 5000000, "tenure": "5-20 years"},
            {"type": "Car Loan", "rate": "9.0%", "max": 1500000, "tenure": "1-7 years"},
            {"type": "Education Loan", "rate": "7.5%", "max": 2000000, "tenure": "1-10 years"},
        ]
    return render_template("loans.html", applications=applications, offers=loan_offers, account=account)


# ── Security / Fraud ─────────────────────────────────────────

@routes_bp.route("/security")
@login_required
def security():
    c = _c()
    c.execute("SELECT * FROM fraud_flags WHERE user_id=? ORDER BY flagged_at DESC LIMIT 20", (session["user_id"],))
    cols = [d[0] for d in c.description]
    flags = [dict(zip(cols, r)) for r in c.fetchall()]
    return render_template("security.html", flags=flags)


# ── Reports & Export ─────────────────────────────────────────

@routes_bp.route("/reports")
@login_required
def reports():
    account = _acct()
    result = _svc().mini_statement(session["user_id"], limit=100)
    return render_template("reports.html", account=account, transactions=result.get("transactions", []))


@routes_bp.route("/export/csv")
@login_required
def export_csv():
    import csv, io
    c = _c()
    c.execute("SELECT * FROM transactions WHERE user_id=? ORDER BY timestamp DESC", (session["user_id"],))
    cols = [d[0] for d in c.description]
    rows = c.fetchall()
    si = io.StringIO()
    w = csv.writer(si)
    w.writerow(cols)
    w.writerows(rows)
    return Response(si.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment;filename=transactions.csv"})


@routes_bp.route("/export/excel")
@login_required
def export_excel():
    import csv, io
    c = _c()
    c.execute("SELECT * FROM transactions WHERE user_id=? ORDER BY timestamp DESC", (session["user_id"],))
    cols = [d[0] for d in c.description]
    rows = c.fetchall()
    si = io.StringIO()
    w = csv.writer(si)
    w.writerow(cols)
    w.writerows(rows)
    return Response(si.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment;filename=transactions.csv"})


@routes_bp.route("/export/passbook")
@login_required
def export_passbook():
    try:
        from src.report_generator import ReportGenerator
        account = _acct()
        c = _c()
        c.execute("SELECT * FROM transactions WHERE user_id=? ORDER BY timestamp DESC", (session["user_id"],))
        cols = [d[0] for d in c.description]
        txns = [dict(zip(cols, r)) for r in c.fetchall()]
        from io import BytesIO
        pdf_buffer = BytesIO()
        rg = ReportGenerator()
        from src.utils import DATA_PROCESSED
        import tempfile, os
        os.makedirs(str(DATA_PROCESSED), exist_ok=True)
        user_data = {"user_id": account.user_id, "name": account.name, "email": account.email,
                     "phone": account.phone, "bank": account.bank, "account_no": account.account_number,
                     "card_no": account.card_number, "account_type": account.account_type,
                     "balance": account.balance, "credit_score": account.credit_score,
                     "age_group": account.age_group, "created_at": ""}
        pdf_path = rg.generate_passbook(user_data, txns=txns, prompt_open=False)
        if pdf_path and os.path.exists(str(pdf_path)):
            with open(str(pdf_path), "rb") as f:
                pdf_data = f.read()
            return Response(pdf_data, mimetype="application/pdf",
                            headers={"Content-Disposition": f"attachment;filename=passbook_{account.user_id}.pdf"})
        flash("Passbook generation failed", "error")
    except Exception as e:
        flash(f"Passbook error: {e}", "error")
    return redirect(url_for("routes.reports"))


# ── Investment Suggestions ───────────────────────────────────

@routes_bp.route("/investment-suggestions")
@login_required
def investment_suggestions():
    account = _acct()
    if not account:
        return redirect(url_for("auth.logout"))
    risk = request.args.get("risk", "moderate")
    suggestions = []
    try:
        from src.models.investment_recommender import InvestmentRecommender
        ir = InvestmentRecommender()
        result = ir.recommend(age=25, income_bracket="mid", balance=account.balance, risk_tolerance=risk)
        if isinstance(result, dict) and "products" in result:
            suggestions = [{"category": p.get("type", p.get("name", "Product")),
                            "products": [p],
                            "total_pct": p.get("allocation", p.get("pct", 0))}
                           for p in result["products"]]
        elif isinstance(result, list):
            suggestions = [{"category": p.get("type", p.get("name", "Product")),
                            "products": [p],
                            "total_pct": p.get("allocation", p.get("pct", 0))}
                           for p in result]
    except Exception:
        suggestions = [
            {"category": "Fixed Deposit", "products": [{"name": "FD (5.5% p.a.)", "allocation": 30, "reason": "Safe returns"}],
             "total_pct": 30},
            {"category": "Mutual Funds", "products": [{"name": "Index Fund", "allocation": 25, "reason": "Market growth"},
                                                       {"name": "Debt Fund", "allocation": 15, "reason": "Stability"}],
             "total_pct": 40},
            {"category": "Gold / Commodities", "products": [{"name": "Digital Gold", "allocation": 15, "reason": "Hedge"}],
             "total_pct": 15},
            {"category": "Cash / Savings", "products": [{"name": "Savings Account", "allocation": 15, "reason": "Liquidity"}],
             "total_pct": 15},
        ]
    return render_template("investment.html", suggestions=suggestions, account=account, risk=risk)


# ── Bank Explorer ────────────────────────────────────────────

@routes_bp.route("/bank-explorer")
@login_required
def bank_explorer():
    c = _c()
    c.execute("SELECT DISTINCT bank, COUNT(*) as cnt, AVG(balance) as avg_bal FROM users GROUP BY bank ORDER BY cnt DESC")
    cols = [d[0] for d in c.description]
    banks = [dict(zip(cols, r)) for r in c.fetchall()]

    bank_attrs = []
    try:
        from src.bank_attributes import get_bank_attrs
        for b in banks:
            try:
                attrs = get_bank_attrs(b["bank"])
                if attrs:
                    bank_attrs.append({"name": b["bank"], **attrs})
            except Exception:
                pass
    except Exception:
        pass
    return render_template("bank_explorer.html", banks=banks, bank_attrs=bank_attrs)


# ── Analytics ────────────────────────────────────────────────

@routes_bp.route("/analytics")
@login_required
def analytics():
    account = _acct()
    c = _c()
    c.execute("SELECT COUNT(*) as txn_count, SUM(amount) as total_spent FROM transactions WHERE user_id=? AND type IN ('withdraw','transfer')",
              (session["user_id"],))
    spending = dict(zip([d[0] for d in c.description], c.fetchone()))
    c.execute("SELECT COUNT(*) as txn_count, SUM(amount) as total_dep FROM transactions WHERE user_id=? AND type IN ('deposit','credit')",
              (session["user_id"],))
    income = dict(zip([d[0] for d in c.description], c.fetchone()))
    c.execute("SELECT type, COUNT(*) as cnt, SUM(amount) as tot FROM transactions WHERE user_id=? GROUP BY type ORDER BY cnt DESC",
              (session["user_id"],))
    cols = [d[0] for d in c.description]
    breakdown = [dict(zip(cols, r)) for r in c.fetchall()]
    return render_template("analytics.html", account=account, spending=spending, income=income, breakdown=breakdown)


@routes_bp.route("/analytics/monthly-trend")
@login_required
def monthly_trend():
    fig_loaded = False
    try:
        from src.data_analysis import DataAnalysis
        da = DataAnalysis()
        da.monthly_trend()
        fig_loaded = True
    except Exception:
        pass

    c = _c()
    date_sql = "TO_CHAR(timestamp, 'YYYY-MM')" if _USE_PG else "strftime('%Y-%m', timestamp)"
    c.execute(f"""SELECT {date_sql} as month, type, SUM(amount) as total, COUNT(*) as cnt
                 FROM transactions WHERE user_id=? GROUP BY month, type ORDER BY month""", (session["user_id"],))
    cols = [d[0] for d in c.description]
    user_trends = [dict(zip(cols, r)) for r in c.fetchall()]
    return render_template("monthly_trend.html", fig_loaded=fig_loaded, user_trends=user_trends)


@routes_bp.route("/analytics/channel-breakdown")
@login_required
def channel_breakdown():
    try:
        from src.data_analysis import DataAnalysis
        da = DataAnalysis()
        channels = da.channel_breakdown()
    except Exception:
        channels = None
    c = _c()
    c.execute("SELECT channel, COUNT(*) as cnt, SUM(amount) as tot FROM transactions WHERE user_id=? GROUP BY channel",
              (session["user_id"],))
    cols = [d[0] for d in c.description]
    user_channels = [dict(zip(cols, r)) for r in c.fetchall()]
    return render_template("channel_breakdown.html", channels=channels, user_channels=user_channels)


@routes_bp.route("/analytics/market-share")
@login_required
def market_share():
    ms = None
    tb = None
    try:
        from src.data_analysis import DataAnalysis
        da = DataAnalysis()
        ms_df = da.market_share()
        tb_df = da.top_banks()
        if ms_df is not None and hasattr(ms_df, 'to_dict'):
            ms = ms_df.to_dict(orient='records')
        if tb_df is not None and hasattr(tb_df, 'to_dict'):
            tb = tb_df.to_dict(orient='records')
    except Exception:
        pass
    return render_template("market_share.html", market_share=ms, top_banks=tb)


@routes_bp.route("/analytics/growth-rate")
@login_required
def growth_rate():
    gr = None
    try:
        from src.data_analysis import DataAnalysis
        da = DataAnalysis()
        result = da.growth_rate()
        if result is not None and hasattr(result, 'iloc') and "MoM_Growth_%" in result.columns:
            vals = result["MoM_Growth_%"].dropna()
            if len(vals) > 0:
                gr = float(vals.iloc[-1])
    except Exception:
        pass
    return render_template("growth_rate.html", growth_rate=gr)


@routes_bp.route("/analytics/user-vs-industry")
@login_required
def user_vs_industry():
    account = _acct()
    comparison = None
    try:
        from src.data_analysis import DataAnalysis
        da = DataAnalysis()
        user_data = {"bank": account.bank, "balance": account.balance, "age_group": account.age_group}
        comparison = da.user_vs_industry(user_data)
    except Exception:
        pass
    return render_template("user_vs_industry.html", account=account, comparison=comparison)


# ── ML Insights ──────────────────────────────────────────────

@routes_bp.route("/insights")
@login_required
def insights():
    account = _acct()
    if not account:
        return redirect(url_for("auth.logout"))
    return render_template("insights.html", account=account)


@routes_bp.route("/ml/credit-prediction")
@login_required
def ml_credit_prediction():
    account = _acct()
    prediction = {}
    try:
        from src.models.credit_scorer import CreditScorer
        cs = CreditScorer()
        score = cs.predict({"age": 25, "income": 50000, "balance": account.balance, "txn_count": 50})
        prediction = {"predicted_score": score}
    except Exception as e:
        prediction = {"error": str(e), "fallback": account.credit_score if account else 700}
    return render_template("ml_credit.html", account=account, prediction=prediction)


@routes_bp.route("/ml/churn-analysis")
@login_required
def ml_churn_analysis():
    account = _acct()
    churn = None
    try:
        from src.models.churn_predictor import ChurnPredictor
        cp = ChurnPredictor()
        churn = cp.predict({"age": 25, "balance": account.balance, "txn_count": 50, "days_inactive": 2})
    except Exception as e:
        churn = {"error": str(e)}
    return render_template("ml_churn.html", account=account, churn=churn)


@routes_bp.route("/ml/loan-default")
@login_required
def ml_loan_default():
    account = _acct()
    default_risk = None
    try:
        from src.models.loan_default_model import LoanDefaultModel
        lm = LoanDefaultModel()
        default_risk = lm.predict({"credit_score": account.credit_score, "balance": account.balance, "age": 25}, 50000, 10.0, 12)
    except Exception as e:
        default_risk = {"error": str(e)}
    return render_template("ml_loan_default.html", account=account, default_risk=default_risk)


@routes_bp.route("/ml/bank-recommendation")
@login_required
def ml_bank_recommendation():
    account = _acct()
    recommendation = {}
    try:
        from src.models.bank_recommender import BankRecommender
        br = BankRecommender()
        result = br.recommend({"age": 25, "balance": account.balance, "bank": account.bank})
        recommendation = {"banks": result}
    except Exception as e:
        recommendation = {"error": str(e)}
    return render_template("ml_bank_rec.html", account=account, recommendation=recommendation)


# ── Feedback ─────────────────────────────────────────────────

@routes_bp.route("/feedback", methods=["GET", "POST"])
@login_required
def feedback():
    if request.method == "POST":
        rating = request.form.get("rating", "").strip()
        comments = request.form.get("comments", "").strip()
        category = request.form.get("category", "general").strip()
        if rating and rating.isdigit():
            _conn().execute("INSERT INTO feedback (user_id, rating, comments, category) VALUES (?,?,?,?)",
                            (session["user_id"], int(rating), comments, category))
            _conn().commit()
            flash("Thank you for your feedback!", "success")
        else:
            flash("Rating is required", "error")
        return redirect(url_for("routes.dashboard"))
    return render_template("feedback.html")
