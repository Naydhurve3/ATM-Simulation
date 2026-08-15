# ATM & Banking Ecosystem v4.0 — Monorepo

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="MIT License">
  <img src="https://img.shields.io/badge/Flask-2.3+-000000?style=for-the-badge&logo=flask&logoColor=white" alt="Flask">
</p>

A complete ATM & banking research ecosystem built as a 3-project monorepo.
All business logic, ML models, and research live in **V1**; the CLI (**V2**) and
web app (**V3**) are thin presentation layers over it.

## Projects

| Version | Path | Package | What it is |
|---|---|---|---|
| **V1 — Banking Core** | [`v1_banking_core/`](v1_banking_core/) | `banking-core` | All banking logic, DB, ML models, research, reports, data |
| **V2 — CLI** | [`v2_cli/`](v2_cli/) | `atm-cli` | Rich terminal ATM simulator + analytics dashboard |
| **V3 — Web** | [`v3_web/`](v3_web/) | `banking-web` | Flask web app (accounts, ATM ops, ML insights, monitoring) |

## Quick Start

Each project is an installable Python package with its own README.

```bash
# V1 (required by V2 and V3)
pip install -e v1_banking_core

# V2
pip install -e v2_cli
atm-cli

# V3
pip install -e v3_web
python v3_web/run_web.py
```

## Running Tests

```bash
pytest v1_banking_core/tests   # core: 75 tests
pytest v2_cli/tests            # CLI:   6 tests
pytest v3_web/tests            # web:  13 tests
```

## Architecture

- **V1** owns all shared data (`data/`, `outputs/`, `logs/`), the SQLite/Postgres
  layers, ML models (fraud, credit, churn, recommendations) and report generation.
- **V2 / V3** never duplicate business logic; they call
  `banking_core.services.UserService` / `ATMService`.
- Detailed design docs: `v1_banking_core/docs/research/`

## Project Roadmap

| Phase | Status |
|---|---|
| V1 core extracted + unified services | ✅ |
| V2 CLI refactored over V1 services | ✅ |
| V3 web refactored over V1 services | ✅ |
| Legacy dashboard merged into V3 (monitoring) | ✅ |
| Research docs + READMEs | ✅ |
| CI pipeline for all 3 versions | ✅ |

## License

MIT
