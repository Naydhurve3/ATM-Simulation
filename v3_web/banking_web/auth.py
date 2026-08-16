import os
import secrets
from flask import Blueprint, render_template, request, redirect, url_for, flash, session

from banking_core.services import UserService
from banking_core.utils import (
    validate_name, validate_phone, validate_email, validate_age,
    get_age_group, income_bracket_options,
)
from banking_core.bank_attributes import get_all_bank_prefixes, get_bank_attrs

_USE_PG = os.environ.get("DATABASE_URL") is not None

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

LOGIN_ATTEMPTS_KEY = "_login_attempts"
MAX_ATTEMPTS = 5


def _svc():
    return UserService()


def _bank_names():
    try:
        from banking_core.utils import BANK_ALIASES
        names = sorted(BANK_ALIASES.values())
        names = sorted(set(names), key=lambda n: (get_bank_attrs(n).get("type", "PVT"), n))
        return names
    except Exception:
        return sorted(set(get_all_bank_prefixes().values()))


def _render_errors(errors):
    for e in errors:
        flash(e, "error")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("routes.dashboard"))

    if request.method == "GET":
        return render_template("login.html")

    identifier = request.form.get("identifier", "").strip()
    pin = request.form.get("pin", "").strip()
    token = secrets.token_hex(16)

    attempts = session.get(LOGIN_ATTEMPTS_KEY, 0)
    if attempts >= MAX_ATTEMPTS:
        flash(f"Too many failed attempts. Session locked — log in again later or clear your session.", "error")
        return render_template("login.html")

    result = _svc().authenticate(identifier, pin, token)
    if isinstance(result, str):
        attempts += 1
        session[LOGIN_ATTEMPTS_KEY] = attempts
        remaining = MAX_ATTEMPTS - attempts
        flash(f"{result}. Attempts left: {remaining}", "error")
        return render_template("login.html")

    session.pop(LOGIN_ATTEMPTS_KEY, None)
    session["user_id"] = result["user_id"]
    session["user_name"] = result["name"]
    session["user_bank"] = result.get("bank", "Banking")
    session["is_minor"] = bool(result.get("is_minor", False))
    session["age_group"] = result.get("age_group", "Adult")
    session["session_token"] = token
    try:
        from banking_core.analytics.activity_tracker import log_activity
        from banking_core.data.postgres_adapter import get_ecosystem_conn
        log_activity(get_ecosystem_conn(), result["user_id"], "login")
    except Exception:
        pass
    flash(f"Welcome back, {result['name']}!", "success")
    return redirect(url_for("routes.dashboard"))


@auth_bp.route("/logout", methods=["GET", "POST"])
def logout():
    _svc().end_session(session.get("user_id"), session.get("session_token"))
    session.clear()
    flash("Logged out successfully", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("routes.dashboard"))

    if request.method == "GET":
        return render_template("register.html", banks=_bank_names(), income_options=income_bracket_options())

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    phone = request.form.get("phone", "").strip()
    age_raw = request.form.get("age", "").strip()
    pin = request.form.get("pin", "").strip()
    confirm_pin = request.form.get("confirm_pin", "").strip()
    bank = request.form.get("bank", "").strip()
    income_bracket = request.form.get("income_bracket", "not_earning_student").strip()
    income_status = "earning" if income_bracket.startswith("earning") else "not_earning"

    errors = []
    ok, name = validate_name(name)
    if not ok:
        errors.append(name)
    ok, phone = validate_phone(phone)
    if not ok:
        errors.append(phone)
    ok, email = validate_email(email)
    if not ok:
        errors.append(email)
    ok, age = validate_age(age_raw)
    if not ok:
        errors.append(age)
    if not pin or not pin.isdigit() or len(pin) != 4:
        errors.append("PIN must be exactly 4 digits")
    if pin != confirm_pin:
        errors.append("PINs do not match")
    if bank not in _bank_names():
        errors.append("Please select a valid bank")

    age_group, is_minor = get_age_group(age) if ok else ("Unknown", False)

    guardian = {}
    if is_minor:
        g_name = request.form.get("guardian_name", "").strip()
        g_phone = request.form.get("guardian_phone", "").strip()
        g_relation = request.form.get("guardian_relation", "Father").strip()
        g_aadhaar = request.form.get("guardian_aadhaar", "").strip()
        c_aadhaar = request.form.get("child_aadhaar", "").strip()
        child_surname = request.form.get("child_surname", "").strip().upper()
        guardian_surname = g_name.split()[-1].upper() if g_name else ""
        surname_match = bool(child_surname and guardian_surname and child_surname == guardian_surname)
        address_match = request.form.get("address_match", "true").lower() != "false"

        g_ok, g_name = validate_name(g_name)
        if not g_ok:
            errors.append(f"Guardian: {g_name}")
        ok, g_phone = validate_phone(g_phone)
        if not ok:
            errors.append(f"Guardian: {g_phone}")
        if g_relation not in ("Father", "Mother", "Legal Guardian"):
            errors.append("Guardian relation must be Father, Mother or Legal Guardian")
        if not (g_aadhaar.isdigit() and len(g_aadhaar) == 4):
            errors.append("Guardian's Aadhaar last 4 digits required")
        if not (c_aadhaar.isdigit() and len(c_aadhaar) == 4):
            errors.append("Child's Aadhaar last 4 digits required")

        guardian = {
            "name": g_name, "phone": g_phone, "relation": g_relation,
            "child_aadhaar": c_aadhaar, "guardian_aadhaar": g_aadhaar,
            "surname_match": surname_match, "address_match": address_match,
        }

    if errors:
        _render_errors(errors)
        return render_template("register.html", banks=_bank_names(),
                               income_options=income_bracket_options(),
                               form=request.form)

    result = _svc().register({
        "name": name, "phone": phone, "email": email, "age": age,
        "income_status": income_status, "income_bracket": income_bracket,
        "guardian": guardian, "bank": bank, "pin": pin,
    })
    if isinstance(result, str):
        flash(result, "error")
        return render_template("register.html", banks=_bank_names(),
                               income_options=income_bracket_options(),
                               form=request.form)

    token = secrets.token_hex(16)
    _svc().log_session(result["user_id"], token)
    session["user_id"] = result["user_id"]
    session["user_name"] = result["name"]
    session["user_bank"] = result.get("bank", "Banking")
    session["is_minor"] = bool(result.get("is_minor", False))
    session["age_group"] = result.get("age_group", "Adult")
    session["session_token"] = token
    try:
        from banking_core.analytics.activity_tracker import log_activity
        from banking_core.data.postgres_adapter import get_ecosystem_conn
        log_activity(get_ecosystem_conn(), result["user_id"], "register")
    except Exception:
        pass
    flash(f"Account created! Welcome, {result['name']}! Your account number is {result.get('account_no', '')}.", "success")
    return redirect(url_for("routes.dashboard"))
