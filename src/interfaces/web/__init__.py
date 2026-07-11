from flask import Flask
import os


def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key-change-in-production")

    from src.interfaces.web.auth import auth_bp
    from src.interfaces.web.routes import routes_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(routes_bp)

    return app
