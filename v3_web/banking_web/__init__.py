import os
import secrets

from flask import Flask, g, request, session, abort, render_template, redirect, url_for, flash
from functools import wraps


def generate_csrf_token():
    if "_csrf_token" not in session:
        session["_csrf_token"] = secrets.token_hex(32)
    return session["_csrf_token"]


def csrf_token():
    """Template helper — exposes the per-session CSRF token."""
    return generate_csrf_token()


def _session_valid(user_id, token):
    try:
        from banking_core.services import UserService
        return UserService().is_session_valid(user_id, token)
    except Exception:
        return True


def csrf_required(view):
    """Decorator: reject unsafe requests without a valid CSRF token."""

    @wraps(view)
    def wrapped(*args, **kwargs):
        if request.method in ("POST", "PUT", "PATCH", "DELETE"):
            token = request.form.get("csrf_token", "") or request.headers.get("X-CSRF-Token", "")
            if not token or not secrets.compare_digest(token, generate_csrf_token()):
                abort(400, description="Invalid or missing CSRF token")
        return view(*args, **kwargs)

    return wrapped


def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key-change-in-production")

    app.jinja_env.globals["csrf_token"] = csrf_token

    @app.template_filter("bank_cat")
    def bank_cat(bank_name):
        try:
            from banking_core.bank_attributes import get_bank_attrs
            return get_bank_attrs(bank_name).get("type", "PVT")
        except Exception:
            return "PVT"

    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.environ.get("SESSION_COOKIE_SECURE", "").lower()
        in ("1", "true", "yes"),
        PERMANENT_SESSION_LIFETIME=1800,
        MAX_CONTENT_LENGTH=2 * 1024 * 1024,
    )

    from banking_web.auth import auth_bp
    from banking_web.routes import routes_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(routes_bp)

    @app.before_request
    def csrf_protect():
        if request.method in ("POST", "PUT", "PATCH", "DELETE"):
            token = request.form.get("csrf_token", "") or request.headers.get("X-CSRF-Token", "")
            if not token or not secrets.compare_digest(token, generate_csrf_token()):
                abort(400, description="Invalid or missing CSRF token")

    @app.before_request
    def refresh_session():
        if "user_id" in session:
            session.permanent = True
            if session.get("session_token") and not _session_valid(session["user_id"],
                                                                  session["session_token"]):
                session.clear()
                flash("Session expired — please log in again.", "info")
                return redirect(url_for("auth.login"))

    @app.errorhandler(404)
    def not_found(e):
        if request.path.startswith("/static/"):
            return e
        return render_template("error.html", code=404,
                               title="Page not found",
                               message="The page you are looking for doesn't exist or was moved."), 404

    @app.errorhandler(400)
    def bad_request(e):
        return render_template("error.html", code=400,
                               title="Bad request",
                               message=getattr(e, "description", "The request could not be processed.")), 400

    @app.errorhandler(500)
    def server_error(e):
        return render_template("error.html", code=500,
                               title="Something went wrong",
                               message="An internal error occurred. Please try again later."), 500

    return app
