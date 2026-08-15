# V1 — Banking Core (`banking-core`)

Research-heavy core of the ATM & Banking ecosystem. **No UI** — everything the
CLI (V2) and web app (V3) need lives here: data layers, business rules, ML
models, reports, and the shared data store.

## Install

```bash
pip install -e v1_banking_core
```

Requires Python 3.10+. Optional heavy ML deps (xgboost, prophet, tensorflow)
are lazy-loaded — the system degrades gracefully without them.

## Layout

```
v1_banking_core/
├── banking_core/          # the package
│   ├── services/          # unified services (UserService, ATMService)
│   ├── models/            # ML: fraud, credit, churn, recommendations, monitor
│   ├── data/              # DB layer: db_manager, model_registry, feature_store
│   ├── utils.py           # validation, hashing, helpers
│   ├── data_analysis.py   # analytics engine
│   └── report_generator.py# PDF/Excel report generation
├── data/                  # shared data (gitignored): raw/, processed/, models/
├── docs/research/         # RESEARCH HUB: architecture docs (01–08) + domain
│                          #   knowledge (10–19): banks, ATMs, transactions,
│                          #   inter-bank, loans, KYC/AML, rates, fraud, scoring
├── scripts/               # download_rbi_data.py + validation tooling
├── tests/                 # 75 tests
└── pyproject.toml
```

## Documentation

Start at [`docs/research/README.md`](docs/research/README.md) — the research hub:

- **Domain knowledge (10–19):** how banks actually work — balance sheets, fractional
  reserves, ATM operations & networks, NEFT/RTGS/IMPS/UPI lifecycle, inter-bank settlement
  (nostro/vostro, NPCI, CCIL), loans & eligibility (RBI norms, LTV, documents), KYC/AML/Basel,
  interest-rate transmission, fraud taxonomy, credit scoring, and real RBI data validation —
  every doc has Mermaid workflows/diagrams
- **Architecture (01–08):** system, database, ML, CLI and web blueprints of this codebase

## Testing

```bash
pytest v1_banking_core/tests
```

## Key entry points

- `banking_core.services.UserService` — accounts, KYC, auth, sessions, fraud flags
- `banking_core.services.ATMService` — deposit/withdraw/transfer/statement rules
- `banking_core.data_analysis.DataAnalysis` — analytics for CLI/web dashboards
- `banking_core.models.*` — model training + inference + monitoring
