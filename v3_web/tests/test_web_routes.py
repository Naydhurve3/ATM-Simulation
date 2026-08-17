import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "v1_banking_core"))

import pytest
from banking_web import create_app

TOKEN_RE = re.compile(rb'name="csrf_token" value="([a-f0-9]+)"')


def get_token(client, path):
    resp = client.get(path)
    m = TOKEN_RE.search(resp.data)
    assert m, f"no csrf token found on {path} (status {resp.status_code})"
    return m.group(1).decode()


def post_form(client, path, data, follow_redirects=True):
    data = dict(data)
    if "csrf_token" not in data:
        data["csrf_token"] = get_token(client, path)
    return client.post(path, data=data, follow_redirects=follow_redirects)


def login(client, identifier, pin="1234"):
    return post_form(client, "/auth/login", {"identifier": identifier, "pin": pin})


@pytest.fixture()
def app():
    app = create_app()
    app.testing = True
    return app


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def registered_user(client):
    stamp = str(int(time.time() * 1000))[-8:]
    data = {
        "name": "Route Test User", "email": f"route{stamp}@test.dev",
        "phone": f"98{stamp}", "age": "26", "income_bracket": "earning_5L_10L",
        "bank": "HDFC BANK LTD", "pin": "1234", "confirm_pin": "1234",
    }
    resp = post_form(client, "/auth/register", data)
    assert resp.status_code == 200
    client.get("/auth/logout")
    return {"email": f"route{stamp}@test.dev", "pin": "1234", "phone": f"98{stamp}"}


@pytest.fixture()
def logged_in(client, registered_user):
    resp = login(client, registered_user["email"])
    assert resp.status_code == 200
    assert b"Welcome back" in resp.data
    return registered_user


class TestAuth:
    def test_login_page(self, client):
        assert client.get("/auth/login").status_code == 200

    def test_register_page(self, client):
        assert client.get("/auth/register").status_code == 200

    def test_login_unknown_user(self, client):
        resp = post_form(client, "/auth/login", {"identifier": "nobody@nowhere.dev", "pin": "1234"})
        assert resp.status_code == 200
        assert b"Account not found" in resp.data

    def test_login_wrong_pin(self, client, registered_user):
        resp = post_form(client, "/auth/login", {"identifier": registered_user["email"], "pin": "9999"})
        assert resp.status_code == 200
        assert b"Incorrect PIN" in resp.data

    def test_register_and_login_flow(self, client, registered_user):
        resp = login(client, registered_user["email"])
        assert resp.status_code == 200
        assert b"Welcome back" in resp.data

    def test_register_duplicate_email(self, client, registered_user):
        stamp = str(int(time.time() * 1000))[-8:]
        resp = post_form(client, "/auth/register", {
            "name": "Other User", "email": registered_user["email"],
            "phone": f"97{stamp}", "age": "30", "income_bracket": "earning_2.5L_5L",
            "bank": "ICICI BANK LTD", "pin": "1234", "confirm_pin": "1234",
        })
        assert resp.status_code == 200
        assert b"already registered" in resp.data

    def test_register_minor_requires_guardian(self, client):
        stamp = str(int(time.time() * 1000))[-8:]
        resp = post_form(client, "/auth/register", {
            "name": "Child Test", "email": f"child{stamp}@test.dev",
            "phone": f"96{stamp}", "age": "12", "income_bracket": "not_earning_student",
            "bank": "STATE BANK OF INDIA", "pin": "1234", "confirm_pin": "1234",
        })
        assert resp.status_code == 200
        assert b"Guardian" in resp.data

    def test_register_minor_with_guardian(self, client):
        stamp = str(int(time.time() * 1000))[-8:]
        resp = post_form(client, "/auth/register", {
            "name": "Child Test", "email": f"child{stamp}@test.dev",
            "phone": f"96{stamp}", "age": "12", "income_bracket": "not_earning_student",
            "bank": "STATE BANK OF INDIA", "pin": "1234", "confirm_pin": "1234",
            "guardian_name": "Parent User", "guardian_phone": "9500000000",
            "guardian_relation": "Father", "child_surname": "Test",
            "child_aadhaar": "1234", "guardian_aadhaar": "5678",
        })
        assert resp.status_code == 200
        assert b"Welcome" in resp.data

    def test_logout(self, client, logged_in):
        resp = client.get("/auth/logout", follow_redirects=True)
        assert resp.status_code == 200
        assert client.get("/dashboard").status_code == 302

    def test_csrf_rejection(self, client, logged_in):
        resp = client.post("/deposit", data={"amount": "100"})
        assert resp.status_code == 400


class TestProtectedPages:
    def test_requires_login(self, client):
        resp = client.get("/dashboard")
        assert resp.status_code == 302

    def test_all_pages_render(self, client, logged_in):
        paths = [
            "/dashboard", "/balance", "/deposit", "/withdraw", "/transfer", "/statement",
            "/profile", "/change-pin", "/credit-score", "/savings", "/savings/optimize",
            "/loans", "/security", "/reports", "/investment-suggestions", "/rfm",
            "/bank-explorer", "/analytics",
            "/analytics/monthly-trend", "/analytics/channel-breakdown",
            "/analytics/market-share", "/analytics/growth-rate",
            "/analytics/user-vs-industry", "/analytics/bank-overview",
            "/analytics/compare", "/analytics/correlation", "/analytics/personal",
            "/insights", "/monitoring", "/feedback", "/settings", "/demo",
            "/ml/credit-prediction", "/ml/churn-analysis", "/ml/loan-default",
            "/ml/bank-recommendation", "/ml/cash-demand", "/ml/txn-volume",
            "/ml/bank-clustering", "/ml/anomaly-detection", "/ml/trend-decomposition",
            "/ml/channel-migration", "/ml/what-if", "/ml/replenishment",
            "/ml/lstm-vs-prophet", "/ml/retrain-all",
            "/analysis-report",
        ]
        for path in paths:
            resp = client.get(path)
            assert resp.status_code == 200, (path, resp.status_code)

    def test_404_page(self, client, logged_in):
        resp = client.get("/definitely-not-a-page")
        assert resp.status_code == 404
        assert b"Page not found" in resp.data


class TestATMOperations:
    def test_deposit(self, client, logged_in):
        resp = post_form(client, "/deposit", {"amount": "1000"})
        assert resp.status_code == 200
        assert b"Deposited" in resp.data

    def test_deposit_invalid_amount(self, client, logged_in):
        resp = post_form(client, "/deposit", {"amount": "abc"})
        assert resp.status_code == 200
        assert b"Invalid amount" in resp.data

    def test_withdraw(self, client, logged_in):
        resp = post_form(client, "/withdraw", {"amount": "500"})
        assert resp.status_code == 200
        assert b"Withdrew" in resp.data

    def test_withdraw_invalid_amount(self, client, logged_in):
        resp = post_form(client, "/withdraw", {"amount": "abc"})
        assert resp.status_code == 200
        assert b"Invalid amount" in resp.data

    def test_transfer(self, client, logged_in):
        resp = post_form(client, "/transfer", {"amount": "100", "target_account": "999999999999", "mode": "upi"})
        assert resp.status_code == 200
        assert b"Transferred" in resp.data

    def test_statement(self, client, logged_in):
        resp = client.get("/statement")
        assert resp.status_code == 200

    def test_balance(self, client, logged_in):
        resp = client.get("/balance")
        assert resp.status_code == 200


class TestFeatureFlows:
    def test_change_pin(self, client, logged_in):
        resp = post_form(client, "/change-pin",
                         {"current_pin": "1234", "new_pin": "5678", "confirm_pin": "5678"})
        assert resp.status_code == 200
        assert b"PIN changed" in resp.data

    def test_change_pin_mismatch(self, client, logged_in):
        resp = post_form(client, "/change-pin",
                         {"current_pin": "1234", "new_pin": "5678", "confirm_pin": "9999"})
        assert resp.status_code == 200
        assert b"do not match" in resp.data

    def test_profile_update(self, client, logged_in):
        resp = post_form(client, "/profile",
                         {"name": "Updated Name", "email": logged_in["email"], "phone": logged_in["phone"]})
        assert resp.status_code == 200
        assert b"Profile updated" in resp.data

    def test_create_savings_goal(self, client, logged_in):
        resp = post_form(client, "/savings",
                         {"goal_name": "Holiday", "target_amount": "50000", "deadline": "2027-01-01"})
        assert resp.status_code == 200
        assert b"created" in resp.data

    def test_savings_optimizer(self, client, logged_in):
        resp = post_form(client, "/savings/optimize",
                         {"target_amount": "100000", "deadline_months": "12"})
        assert resp.status_code == 200

    def test_apply_loan(self, client, logged_in):
        resp = post_form(client, "/loans",
                         {"loan_type": "personal", "amount": "25000", "tenure": "12"})
        assert resp.status_code == 200

    def test_feedback_with_sentiment(self, client, logged_in):
        resp = post_form(client, "/feedback",
                         {"rating": "5", "comments": "Great app, love it!", "category": "ui"})
        assert resp.status_code == 200

    def test_monitoring_retrain(self, client, logged_in):
        resp = post_form(client, "/monitoring", {"model_name": "credit_scorer"})
        assert resp.status_code == 200

    def test_retrain_all(self, client, logged_in):
        resp = post_form(client, "/ml/retrain-all", {})
        assert resp.status_code == 200
        assert b"Trained" in resp.data or b"Failed" in resp.data or b"Skipped" in resp.data

    def test_what_if_simulate(self, client, logged_in):
        resp = post_form(client, "/ml/what-if",
                         {"Total_ATMs": "1500", "Digital_Share": "60"})
        assert resp.status_code == 200


class TestAnalysisReport:
    def test_requires_login(self, client):
        resp = client.get("/analysis-report")
        assert resp.status_code == 302

    def test_renders(self, client, logged_in):
        resp = client.get("/analysis-report")
        assert resp.status_code == 200
        assert b"Analysis Report" in resp.data
        assert b"Instant Intelligence" in resp.data

    def test_json_export(self, client, logged_in):
        resp = client.get("/analysis-report?format=json")
        assert resp.status_code == 200
        assert resp.mimetype == "application/json"


class TestExports:
    def test_export_csv(self, client, logged_in):
        resp = client.get("/export/csv")
        assert resp.status_code == 200
        assert resp.mimetype == "text/csv"

    def test_export_excel(self, client, logged_in):
        resp = client.get("/export/excel")
        assert resp.status_code == 200
        assert "spreadsheetml" in resp.mimetype

    def test_export_training_data_zip(self, client, logged_in):
        resp = client.get("/export/training-data")
        assert resp.status_code in (200, 302)


class TestClickDriven:
    def test_dashboard_has_report_button_and_no_stale_banner(self, client, logged_in):
        resp = client.get("/dashboard")
        assert resp.status_code == 200
        assert b"Analysis report" in resp.data
        assert b"Collapse all" in resp.data
        assert b"model(s) stale" not in resp.data

    def test_report_page_shows_analyse_button(self, client, logged_in):
        resp = client.get("/analysis-report")
        assert resp.status_code == 200
        assert b"Analyse my account" in resp.data
        assert b"Download JSON" in resp.data

    def test_report_run_starts_background_job(self, client, logged_in):
        token = get_token(client, "/analysis-report")
        resp = client.post("/analysis-report/run", data={"csrf_token": token},
                           follow_redirects=True)
        assert resp.status_code == 200
        assert b"Analysis started" in resp.data

    def test_report_status_endpoint(self, client, logged_in):
        resp = client.get("/analysis-report/status")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] in ("none", "running", "done", "failed")
        assert "has_report" in data

    def test_analytics_pages_render(self, client, logged_in):
        for path in ("/analytics/monthly-trend", "/analytics/channel-breakdown",
                     "/analytics/market-share", "/analytics/growth-rate",
                     "/analytics/correlation", "/analytics/bank-overview",
                     "/analytics/compare", "/analytics/compare?preset=PSU"):
            resp = client.get(path)
            assert resp.status_code == 200, f"{path} -> {resp.status_code}"

    def test_analytics_refresh_route(self, client, logged_in):
        token = get_token(client, "/analytics/market-share")
        resp = client.post("/analytics/refresh", data={"csrf_token": token, "page": "market-share"},
                           follow_redirects=True)
        assert resp.status_code == 200
        assert b"refreshed" in resp.data or b"Could not refresh" in resp.data


class TestChurnSnapshot:
    def test_dashboard_shows_churn_card(self, client, logged_in):
        resp = client.get("/dashboard")
        assert resp.status_code == 200
        assert b"Churn Risk Snapshot" in resp.data
        assert b"actions tracked" in resp.data
        assert b"Refresh now" in resp.data

    def test_churn_refresh_route(self, client, logged_in):
        token = get_token(client, "/dashboard")
        resp = client.post("/dashboard/churn-refresh", data={"csrf_token": token},
                           follow_redirects=True)
        assert resp.status_code == 200
        assert b"Churn snapshot refreshed" in resp.data

    def test_activity_logged_on_deposit(self, client, logged_in):
        post_form(client, "/deposit", {"amount": "1000"})
        from banking_core.analytics.activity_tracker import activity_features
        from banking_core.data.postgres_adapter import get_ecosystem_conn
        uid = _session_user_id(client)
        feats = activity_features(get_ecosystem_conn(), uid)
        assert feats["activity_count"] >= 1
        assert feats["txn_count"] >= 1

    def test_churn_features_refresh_after_action(self, client, logged_in):
        post_form(client, "/deposit", {"amount": "2000"})
        token = get_token(client, "/dashboard")
        client.post("/dashboard/churn-refresh", data={"csrf_token": token})
        resp = client.get("/dashboard")
        assert b"Churn Risk Snapshot" in resp.data
        assert b"txn_count" not in resp.data  # raw features not dumped into HTML


def _session_user_id(client):
    with client.session_transaction() as sess:
        return sess.get("user_id")
