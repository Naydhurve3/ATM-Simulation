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


@routes_bp.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("routes.dashboard"))
    return redirect(url_for("auth.login"))


@routes_bp.route("/dashboard")
@login_required
def dashboard():
    from src.services.atm_service import ATMService
    svc = ATMService()
    account = svc.get_account(session["user_id"])
    if not account:
        flash("Account not found", "error")
        return redirect(url_for("auth.logout"))
    transactions = svc.mini_statement(session["user_id"], limit=10)
    return render_template("dashboard.html", account=account, transactions=transactions)


@routes_bp.route("/deposit", methods=["GET", "POST"])
@login_required
def deposit():
    if request.method == "GET":
        return render_template("deposit.html")

    amount_str = request.form.get("amount", "").strip()
    try:
        amount = float(amount_str)
    except (ValueError, TypeError):
        flash("Invalid amount", "error")
        return render_template("deposit.html")

    from src.services.atm_service import ATMService
    svc = ATMService()
    result = svc.deposit(session["user_id"], amount, channel="web")
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

    amount_str = request.form.get("amount", "").strip()
    try:
        amount = float(amount_str)
    except (ValueError, TypeError):
        flash("Invalid amount", "error")
        return render_template("withdraw.html")

    from src.services.atm_service import ATMService
    svc = ATMService()
    result = svc.withdraw(session["user_id"], amount, channel="web")
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

    amount_str = request.form.get("amount", "").strip()
    target = request.form.get("target_account", "").strip()
    ifsc = request.form.get("ifsc", "").strip()
    via = request.form.get("via", "neft")

    try:
        amount = float(amount_str)
    except (ValueError, TypeError):
        flash("Invalid amount", "error")
        return render_template("transfer.html")

    if not target:
        flash("Target account is required", "error")
        return render_template("transfer.html")

    from src.services.atm_service import ATMService
    svc = ATMService()
    result = svc.transfer(session["user_id"], target, amount, via=via, channel="web")
    if "error" in result:
        flash(result["error"], "error")
        return render_template("transfer.html")

    flash(f"Transferred ₹{amount:,.2f} to {target}. Balance: ₹{result['balance_after']:,.2f}", "success")
    return redirect(url_for("routes.dashboard"))


@routes_bp.route("/statement")
@login_required
def statement():
    from src.services.atm_service import ATMService
    svc = ATMService()
    transactions = svc.mini_statement(session["user_id"], limit=50)
    return render_template("statement.html", transactions=transactions)
