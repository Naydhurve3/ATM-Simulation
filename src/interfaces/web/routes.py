from flask import Blueprint, render_template, request, redirect, url_for, flash, session

routes_bp = Blueprint("routes", __name__)


def login_required(view):
    from functools import wraps
    @wraps(view)
    def wrapped(**kwargs):
        if "user_id" not in session:
            flash("Please log in first", "warning")
            return redirect(url_for("auth.login"))
        return view(**kwargs)
    return wrapped


def _get_service():
    from src.services.atm_service import ATMService
    return ATMService()


def _get_account():
    svc = _get_service()
    return svc.get_account(session["user_id"])


# ── Core Pages ───────────────────────────────────────────────

@routes_bp.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("routes.dashboard"))
    return redirect(url_for("auth.login"))


@routes_bp.route("/dashboard")
@login_required
def dashboard():
    account = _get_account()
    if not account:
        flash("Account not found", "error")
        return redirect(url_for("auth.logout"))
    result = _get_service().mini_statement(session["user_id"], limit=10)
    transactions = result.get("transactions", [])
    return render_template("dashboard.html", account=account, transactions=transactions)


# ── ATM Operations ───────────────────────────────────────────

@routes_bp.route("/deposit", methods=["GET", "POST"])
@login_required
def deposit():
    if request.method == "GET":
        return render_template("deposit.html")
    try:
        amount = float(request.form.get("amount", "").strip())
    except (ValueError, TypeError):
        flash("Invalid amount", "error")
        return render_template("deposit.html")
    result = _get_service().deposit(session["user_id"], amount, channel="web")
    if "error" in result:
        flash(result["error"], "error")
        return render_template("deposit.html")
    flash(f"Deposited ₹{amount:,.2f}. New balance: ₹{result['balance_after']:,.2f}", "success")
    return redirect(url_for("routes.dashboard"))


@routes_bp.route("/withdraw", methods=["GET", "POST"])
@login_required
def withdraw():
    if request.method == "GET":
        return render_template("withdraw.html")
    try:
        amount = float(request.form.get("amount", "").strip())
    except (ValueError, TypeError):
        flash("Invalid amount", "error")
        return render_template("withdraw.html")
    result = _get_service().withdraw(session["user_id"], amount, channel="web")
    if "error" in result:
        flash(result["error"], "error")
        return render_template("withdraw.html")
    flash(f"Withdrew ₹{amount:,.2f}. Remaining: ₹{result['balance_after']:,.2f}", "success")
    return redirect(url_for("routes.dashboard"))


@routes_bp.route("/transfer", methods=["GET", "POST"])
@login_required
def transfer():
    if request.method == "GET":
        return render_template("transfer.html")
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
    result = _get_service().transfer(session["user_id"], target, amount, via=via, channel="web")
    if "error" in result:
        flash(result["error"], "error")
        return render_template("transfer.html")
    flash(f"Transferred ₹{amount:,.2f} to {target}", "success")
    return redirect(url_for("routes.dashboard"))


@routes_bp.route("/statement")
@login_required
def statement():
    result = _get_service().mini_statement(session["user_id"], limit=50)
    transactions = result.get("transactions", [])
    return render_template("statement.html", transactions=transactions)


# ── Profile & Settings ───────────────────────────────────────

@routes_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    account = _get_account()
    if not account:
        flash("Account not found", "error")
        return redirect(url_for("auth.logout"))
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        if name and email and phone:
            from src.data.db_manager import db
            conn = db.get_connection("ecosystem")
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
    if request.method == "GET":
        return render_template("change_pin.html")
    current = request.form.get("current_pin", "").strip()
    new_pin = request.form.get("new_pin", "").strip()
    confirm = request.form.get("confirm_pin", "").strip()
    if not current or not new_pin or not confirm:
        flash("All fields required", "error")
        return render_template("change_pin.html")
    if new_pin != confirm:
        flash("New PINs do not match", "error")
        return render_template("change_pin.html")
    if len(new_pin) != 4 or not new_pin.isdigit():
        flash("PIN must be exactly 4 digits", "error")
        return render_template("change_pin.html")
    from src.utils import hash_pin
    from src.data.db_manager import db
    conn = db.get_connection("ecosystem")
    c = conn.cursor()
    c.execute("SELECT pin_hash FROM users WHERE user_id=?", (session["user_id"],))
    row = c.fetchone()
    if not row or row[0] != hash_pin(current):
        flash("Current PIN is incorrect", "error")
        return render_template("change_pin.html")
    conn.execute("UPDATE users SET pin_hash=? WHERE user_id=?",
                 (hash_pin(new_pin), session["user_id"]))
    conn.commit()
    flash("PIN changed successfully", "success")
    return redirect(url_for("routes.profile"))


# ── Credit Score ─────────────────────────────────────────────

@routes_bp.route("/credit-score")
@login_required
def credit_score():
    account = _get_account()
    if not account:
        return redirect(url_for("auth.logout"))
    from src.data.db_manager import db
    conn = db.get_connection("ecosystem")
    c = conn.cursor()
    c.execute("SELECT * FROM credit_history WHERE user_id=? ORDER BY recorded_at DESC LIMIT 20",
              (session["user_id"],))
    cols = [d[0] for d in c.description]
    history = [dict(zip(cols, row)) for row in c.fetchall()]
    return render_template("credit_score.html", account=account, history=history)


# ── Savings Goals ────────────────────────────────────────────

@routes_bp.route("/savings", methods=["GET", "POST"])
@login_required
def savings():
    from src.data.db_manager import db
    conn = db.get_connection("ecosystem")
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
    c.execute("SELECT * FROM savings_goals WHERE user_id=? ORDER BY created_at DESC",
              (session["user_id"],))
    cols = [d[0] for d in c.description]
    goals = [dict(zip(cols, row)) for row in c.fetchall()]
    return render_template("savings.html", goals=goals)


@routes_bp.route("/savings/<int:goal_id>/add", methods=["POST"])
@login_required
def savings_add(goal_id):
    amount = request.form.get("amount", "").strip()
    if amount:
        from src.data.db_manager import db
        conn = db.get_connection("ecosystem")
        conn.execute("UPDATE savings_goals SET current_amount = current_amount + ? WHERE goal_id=? AND user_id=?",
                     (float(amount), goal_id, session["user_id"]))
        conn.commit()
        flash("Amount added to goal!", "success")
    return redirect(url_for("routes.savings"))


# ── Loan Applications ────────────────────────────────────────

@routes_bp.route("/loans", methods=["GET", "POST"])
@login_required
def loans():
    from src.data.db_manager import db
    conn = db.get_connection("ecosystem")
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
    c.execute("SELECT * FROM loan_applications WHERE user_id=? ORDER BY applied_at DESC",
              (session["user_id"],))
    cols = [d[0] for d in c.description]
    applications = [dict(zip(cols, row)) for row in c.fetchall()]
    return render_template("loans.html", applications=applications)


# ── Security / Fraud Alerts ──────────────────────────────────

@routes_bp.route("/security")
@login_required
def security():
    from src.data.db_manager import db
    conn = db.get_connection("ecosystem")
    c = conn.cursor()
    c.execute("SELECT * FROM fraud_flags WHERE user_id=? ORDER BY flagged_at DESC LIMIT 20",
              (session["user_id"],))
    cols = [d[0] for d in c.description]
    flags = [dict(zip(cols, row)) for row in c.fetchall()]
    return render_template("security.html", flags=flags)


# ── Reports & Export ─────────────────────────────────────────

@routes_bp.route("/reports")
@login_required
def reports():
    result = _get_service().mini_statement(session["user_id"], limit=100)
    transactions = result.get("transactions", [])
    account = _get_account()
    return render_template("reports.html", transactions=transactions, account=account)


@routes_bp.route("/export/csv")
@login_required
def export_csv():
    import csv, io
    from src.data.db_manager import db
    conn = db.get_connection("ecosystem")
    c = conn.cursor()
    c.execute("SELECT * FROM transactions WHERE user_id=? ORDER BY timestamp DESC", (session["user_id"],))
    cols = [d[0] for d in c.description]
    rows = c.fetchall()
    si = io.StringIO()
    w = csv.writer(si)
    w.writerow(cols)
    w.writerows(rows)
    from flask import Response
    return Response(si.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment;filename=transactions.csv"})


# ── Bank Explorer ────────────────────────────────────────────

@routes_bp.route("/bank-explorer")
@login_required
def bank_explorer():
    from src.data.db_manager import db
    conn = db.get_connection("ecosystem")
    c = conn.cursor()
    c.execute("SELECT DISTINCT bank, COUNT(*) as cnt, AVG(balance) as avg_bal FROM users GROUP BY bank ORDER BY cnt DESC")
    cols = [d[0] for d in c.description]
    banks = [dict(zip(cols, row)) for row in c.fetchall()]
    return render_template("bank_explorer.html", banks=banks)


# ── ML Insights ──────────────────────────────────────────────

@routes_bp.route("/insights")
@login_required
def insights():
    account = _get_account()
    if not account:
        return redirect(url_for("auth.logout"))
    return render_template("insights.html", account=account)
