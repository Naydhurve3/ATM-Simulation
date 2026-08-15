# V3 — Banking Web (`banking-web`)

Flask web application for the ATM & Banking ecosystem — a thin presentation
layer over `banking_core` services (V1). Includes the legacy dashboard merged
in as a unified **Monitoring** page.

## Install

```bash
pip install -e v1_banking_core   # dependency
pip install -e v3_web
```

## Run

```bash
python v3_web/run_web.py          # http://127.0.0.1:5000
```

Postgres/SQLAlchemy via `DATABASE_URL` env var is supported
(`scripts/migrate_database.py`); otherwise local SQLite is used.

## Pages

- Auth: login / register
- ATM: dashboard, deposit, withdraw, transfer, statement
- Profile & security: profile, change PIN, security centre
- Money: savings goals, loans, investment suggestions, credit score
- Analytics: monthly trend, channel breakdown, market share, growth rate,
  user vs industry + ML insights (credit prediction, churn, loan default,
  bank recommendation)
- Monitoring (merged legacy dashboard): model version / staleness status

## Layout

```
v3_web/
├── banking_web/       # __init__ (create_app), auth.py, routes.py, templates/, static/
├── tests/             # 13 route smoke tests
├── app.py, run_web.py # entries
├── vercel.json        # deploy config
├── scripts/           # migrate_database.py
└── pyproject.toml
```

## Testing

```bash
pytest v3_web/tests
```
