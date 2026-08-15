# V2 — ATM CLI (`atm-cli`)

Rich terminal ATM simulator built with Rich. A thin presentation layer over
`banking_core` — all logic is delegated to V1 services.

## Install

```bash
pip install -e v1_banking_core   # dependency
pip install -e v2_cli
```

## Run

```bash
atm-cli          # or: python v2_cli/run.py
```

## Features

- Account registration with KYC (minors need guardian, per RBI guidelines)
- Login: card / email / phone / account + forgot card / forgot PIN / full recovery
- ATM operations: withdraw, deposit, transfer (with fee & limit rules), balance
- Analytics dashboard (Rich tables + plotext charts)
- `Launch Web App` menu item boots V3 (`v3_web/run_web.py`) in a subprocess

## Layout

```
v2_cli/
├── atm_cli/           # app.py (main), atm_simulator, user_manager, user_analytics, demo_manager, ui_helpers
├── tests/             # 6 tests
├── run.py             # entry
└── pyproject.toml
```

## Testing

```bash
pytest v2_cli/tests
```
