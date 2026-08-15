import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from banking_web import create_app


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
    resp = client.post("/auth/register", data={
        "name": "Route Test User", "email": f"route{stamp}@test.dev",
        "phone": f"98{stamp}", "pin": "1234", "confirm_pin": "1234",
    }, follow_redirects=True)
    assert resp.status_code == 200
    return {"email": f"route{stamp}@test.dev", "pin": "1234", "phone": f"98{stamp}"}


class TestAuth:
    def test_login_page(self, client):
        assert client.get("/auth/login").status_code == 200

    def test_register_page(self, client):
        assert client.get("/auth/register").status_code == 200

    def test_login_unknown_user(self, client):
        resp = client.post("/auth/login", data={"identifier": "nobody@nowhere.dev", "pin": "1234"})
        assert resp.status_code == 200
        assert b"Account not found" in resp.data

    def test_register_and_login_flow(self, client, registered_user):
        resp = client.post("/auth/login", data={
            "identifier": registered_user["email"], "pin": registered_user["pin"],
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b"Welcome back" in resp.data

    def test_logout(self, client, registered_user):
        client.post("/auth/login", data={
            "identifier": registered_user["email"], "pin": registered_user["pin"],
        })
        resp = client.get("/auth/logout", follow_redirects=True)
        assert resp.status_code == 200


class TestProtectedPages:
    def test_requires_login(self, client):
        resp = client.get("/dashboard")
        assert resp.status_code == 302

    def test_atm_pages(self, client, registered_user):
        client.post("/auth/login", data={
            "identifier": registered_user["email"], "pin": registered_user["pin"],
        })
        for path in ["/dashboard", "/deposit", "/withdraw", "/transfer", "/statement",
                     "/profile", "/change-pin", "/credit-score", "/savings", "/loans",
                     "/security", "/reports", "/investment-suggestions", "/bank-explorer",
                     "/analytics", "/insights", "/monitoring", "/feedback"]:
            resp = client.get(path)
            assert resp.status_code == 200, (path, resp.status_code)

    def test_ml_pages(self, client, registered_user):
        client.post("/auth/login", data={
            "identifier": registered_user["email"], "pin": registered_user["pin"],
        })
        for path in ["/ml/credit-prediction", "/ml/churn-analysis", "/ml/loan-default",
                     "/ml/bank-recommendation"]:
            resp = client.get(path)
            assert resp.status_code == 200, (path, resp.status_code)

    def test_analytics_subpages(self, client, registered_user):
        client.post("/auth/login", data={
            "identifier": registered_user["email"], "pin": registered_user["pin"],
        })
        for path in ["/analytics/monthly-trend", "/analytics/channel-breakdown",
                     "/analytics/market-share", "/analytics/growth-rate",
                     "/analytics/user-vs-industry"]:
            resp = client.get(path)
            assert resp.status_code == 200, (path, resp.status_code)


class TestATMOperations:
    def test_deposit(self, client, registered_user):
        client.post("/auth/login", data={
            "identifier": registered_user["email"], "pin": registered_user["pin"],
        })
        resp = client.post("/deposit", data={"amount": "1000"}, follow_redirects=True)
        assert resp.status_code == 200
        assert b"Deposited" in resp.data

    def test_withdraw(self, client, registered_user):
        client.post("/auth/login", data={
            "identifier": registered_user["email"], "pin": registered_user["pin"],
        })
        resp = client.post("/withdraw", data={"amount": "500"}, follow_redirects=True)
        assert resp.status_code == 200
        assert b"Withdrew" in resp.data

    def test_withdraw_invalid_amount(self, client, registered_user):
        client.post("/auth/login", data={
            "identifier": registered_user["email"], "pin": registered_user["pin"],
        })
        resp = client.post("/withdraw", data={"amount": "abc"})
        assert resp.status_code == 200
        assert b"Invalid amount" in resp.data

    def test_transfer(self, client, registered_user):
        client.post("/auth/login", data={
            "identifier": registered_user["email"], "pin": registered_user["pin"],
        })
        resp = client.post("/transfer", data={"amount": "100", "target_account": "999999999999"},
                           follow_redirects=True)
        assert resp.status_code == 200
