from flask import Blueprint, render_template, request, redirect, url_for, flash, session

from src.data.db_manager import db
from src.utils import hash_pin

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    identifier = request.form.get("identifier", "").strip()
    pin = request.form.get("pin", "").strip()

    conn = db.get_connection("ecosystem")
    c = conn.cursor()

    if "@" in identifier:
        c.execute("SELECT * FROM users WHERE email = ?", (identifier,))
    elif identifier.isdigit() and len(identifier) == 10:
        c.execute("SELECT * FROM users WHERE phone = ?", (identifier,))
    elif identifier.isdigit():
        c.execute("SELECT * FROM users WHERE account_no = ?", (identifier,))
    else:
        c.execute("SELECT * FROM users WHERE card_no = ?", (identifier,))

    row = c.fetchone()
    if not row:
        flash("Account not found", "error")
        return render_template("login.html")

    cols = [d[0] for d in c.description]
    user = dict(zip(cols, row))

    if hash_pin(pin) != user["pin_hash"]:
        flash("Incorrect PIN", "error")
        return render_template("login.html")

    session["user_id"] = user["user_id"]
    session["user_name"] = user["name"]
    flash(f"Welcome back, {user['name']}!", "success")
    return redirect(url_for("routes.dashboard"))


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    phone = request.form.get("phone", "").strip()
    pin = request.form.get("pin", "").strip()
    confirm_pin = request.form.get("confirm_pin", "").strip()

    errors = []
    if not name:
        errors.append("Name is required")
    if not email or "@" not in email:
        errors.append("Valid email is required")
    if not phone or not phone.isdigit() or len(phone) != 10:
        errors.append("Valid 10-digit phone is required")
    if not pin or not pin.isdigit() or len(pin) != 4:
        errors.append("PIN must be exactly 4 digits")
    if pin != confirm_pin:
        errors.append("PINs do not match")

    if errors:
        for e in errors:
            flash(e, "error")
        return render_template("register.html")

    conn = db.get_connection("ecosystem")
    c = conn.cursor()
    c.execute("SELECT user_id FROM users WHERE email = ? OR phone = ?", (email, phone))
    if c.fetchone():
        flash("Email or phone already registered", "error")
        return render_template("register.html")

    import random
    account_no = "".join([str(random.randint(0, 9)) for _ in range(12)])
    card_no = "-".join(["".join([str(random.randint(0, 9)) for _ in range(4)]) for _ in range(4)])

    c.execute(
        """INSERT INTO users (name, email, phone, pin_hash, account_no, card_no, balance,
            account_type, bank, age, age_group, credit_score, is_minor, atm_daily_limit,
            atm_used_today, last_active)
           VALUES (?,?,?,?,?,?,0,'savings','SBI',25,'adult',700,0,100000,0,CURRENT_TIMESTAMP)""",
        (name, email, phone, hash_pin(pin), account_no, card_no),
    )
    conn.commit()
    user_id = c.lastrowid

    session["user_id"] = user_id
    session["user_name"] = name
    flash(f"Account created! Welcome, {name}!", "success")
    return redirect(url_for("routes.dashboard"))
