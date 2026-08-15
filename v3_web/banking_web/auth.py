import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, session

from banking_core.services import UserService

_USE_PG = os.environ.get("DATABASE_URL") is not None

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


def _svc():
    return UserService()


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    identifier = request.form.get("identifier", "").strip()
    pin = request.form.get("pin", "").strip()

    result = _svc().authenticate(identifier, pin)
    if isinstance(result, str):
        flash(result, "error")
        return render_template("login.html")

    session["user_id"] = result["user_id"]
    session["user_name"] = result["name"]
    flash(f"Welcome back, {result['name']}!", "success")
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

    result = _svc().register({
        "name": name, "phone": phone, "email": email, "age": 25,
        "income_status": "not_earning_student", "income_bracket": "not_earning_student",
        "bank": "STATE BANK OF INDIA", "pin": pin,
    })
    if isinstance(result, str):
        flash(result, "error")
        return render_template("register.html")

    session["user_id"] = result["user_id"]
    session["user_name"] = result["name"]
    flash(f"Account created! Welcome, {result['name']}!", "success")
    return redirect(url_for("routes.dashboard"))
