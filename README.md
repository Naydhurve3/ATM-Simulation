# ATM & Banking Ecosystem v3.0

A comprehensive ATM and banking analytics ecosystem powered by real RBI (Reserve Bank of India) data, featuring 20 ML/DL models, a full user system with KYC, ATM simulation, passbook generation, web dashboard, and educational demos.

> **Built with**: Python, Rich CLI, Flask, Scikit-learn, Prophet, XGBoost, TensorFlow, Matplotlib, Plotly

---

## Project Purpose

This project simulates a **realistic banking ecosystem** that combines:

- **Real RBI data** — Monthly ATM/card statistics from 65 Indian banks, ingested and analyzed
- **Working ATM simulator** — Withdraw, deposit, transfer, fraud detection, loan offers with amortization schedules
- **20 ML/DL models** — From Prophet forecasting to LSTM deep learning, covering clustering, anomaly detection, credit scoring, churn prediction, and more
- **Full user system** — Adult/minor registration, KYC with guardian support, forgot card/PIN recovery, session management
- **Multi-account passbook** — Auto-detects linked accounts, generates dynamic passbooks (PNG/PDF) with charts and ML insights
- **Web dashboard** — Flask/Plotly dashboard with 5 pages, auto-launched from CLI
- **Auto-retraining** — Scheduled model retraining based on transaction/user thresholds

---

## Key Features

### Realism & Authenticity

| Feature | Detail |
|---------|--------|
| **RBI Data** | Real monthly ATM/card statistics from 65 Indian banks across all categories (Public, Private, Foreign, Payment, Small Finance) |
| **Bank Explorer** | Browse all 65 banks with attributes (savings rates, ATM limits, digital ratings, fees) |
| **User System** | Registration with age-aware KYC — minors require guardian consent, have capped credit scores, cannot take loans |
| **ATM Limits** | Daily withdrawal limit of Rs 50,000, fraud detection on every transaction, SMS/receipt simulation |
| **Loan Offers** | Personal, Education, Home, Vehicle loans with full amortization schedules (EMI, interest, balance) |
| **Credit Scoring** | Gradient Boosting model with 300-900 range, rule-based for minors (max 600) |
| **Churn Prediction** | Random Forest model with recency/frequency features, days-inactive tracking |
| **Fraud Detection** | Real-time scoring: amount anomalies, odd-hour transactions, rapid succession, high velocity |

### Data Analysis

- Bank overview with KPIs (ATMs, cards, transaction volume/value, digital share)
- Side-by-side bank comparison (multi-metric)
- Monthly trend analysis with interactive charts
- Market share analysis with concentration metrics
- Channel-wise transaction breakdown (PoS, Online, Cash ATM)
- Correlation heatmaps across banking metrics
- Month-over-month growth rate calculation
- Your bank vs industry comparison
- Personal analytics (spending trends, credit breakdown, RFM segmentation)

### ML/DL Models (20 Total)

**Phase 1 — Core Models (13)**

| Model | Algorithm | Use Case |
|-------|-----------|----------|
| Cash Demand Forecaster | Prophet | Predict ATM cash demand |
| Transaction Predictor | XGBoost | Forecast transaction volume/value |
| Bank Clustering | K-Means + PCA | Segment 65 banks into clusters |
| Anomaly Detector | Isolation Forest | Flag unusual bank behavior |
| Trend Analyzer | StatsModels | Decompose time series (trend/seasonal/residual) |
| Channel Migration Predictor | Linear/Prophet | Forecast digital adoption shift |
| What-If Simulator | Linear Regression | Simulate scenario impacts |
| Credit Scorer | Gradient Boosting | Predict credit score (300-900) |
| Churn Predictor | Random Forest | Assess user churn risk |
| Loan Default Model | Rule-based | Evaluate loan eligibility & risk |
| Bank Recommender | Weighted scoring | Top-5 personalized bank picks |
| Spending Forecaster | Prophet/Linear | Predict future spending |
| LSTM Forecaster | TensorFlow LSTM | Deep learning time series forecast |

**Phase 2 — Enhanced Models (7)**

| Model | Algorithm | Use Case |
|-------|-----------|----------|
| Real-Time Fraud Detector | Rule-based | Score transaction fraud risk (0-100) |
| Investment Recommender | Portfolio Theory | Suggest FD, MF, PPF, Gold allocation |
| ATM Replenishment Optimizer | EOQ Model | Optimal cash refill amount & frequency |
| RFM Segmenter | Recency/Frequency/Monetary | Customer segmentation (6 segments) |
| Savings Goal Optimizer | Financial Calc | Monthly deposit & product recommendation |
| Sentiment Analyzer | VADER | Analyze user feedback sentiment |
| Model Monitor | Stats Tracking | Track model staleness & performance |

### Architecture

```
+============================================================================+
|                      ATM & BANKING ECOSYSTEM v3.0                          |
+============================================================================+
|                                                                             |
|  +------------------+  +------------------+  +--------------------------+   |
|  |   CLI Interface  |  |  Web Dashboard   |  |    Data Pipeline          |  |
|  |  (Rich/Tables)   |  | (Flask/Plotly)   |  | (CSV → SQLite → Analysis) |  |
|  +--------+---------+  +--------+---------+  +------------+-------------+   |
|           |                     |                          |                |
|  +--------v---------------------v--------------------------v-------------+   |
|  |                        Database Layer                                  |   |
|  |  +------------------+  +--------------------+  +-------------------+   |   |
|  |  | DatabaseManager   |  |   FeatureStore     |  |  ModelRegistry    |   |   |
|  |  |   (Singleton)     |  | (21 features)      |  | (versioned)       |   |   |
|  |  +---------+---------+  +---------+----------+  +--------+----------+   |   |
|  |            |                       |                       |            |   |
|  |  +---------v-----------------------v-----------------------v----------+  |   |
|  |  |  Databases:  atm_data.db  |  ecosystem.db  |  feature_store.db   |  |   |
|  |  +-------------------------------------------------------------------+  |   |
|  +------------------------------------------------------------------------+   |
|           |                     |                          |                |
|  +--------v---------+  +-------v----------+  +------------v-------------+   |
|  |  ML/DL Models    |  |  User System    |  |  Reports & Exports       |   |
|  |  (20 models)     |  |  (Auth/KYC)     |  |  (PDF/CSV/Excel/Passbook)|   |
|  +------------------+  +------------------+  +--------------------------+   |
+============================================================================+
```

> See full architecture in [`docs/architecture/`](docs/architecture/) — 6 PNG diagrams + 8 markdown documents covering system architecture, database ERD, ML models, data pipeline, CLI menu structure, and user system flow.

---

## Quick Start

### Prerequisites

- Python 3.10+
- pip

### Installation

```bash
# Clone the repository
git clone https://github.com/Naydhurve3/ATM-Simulation.git
cd ATM-Simulation

# Install dependencies
pip install -r requirements.txt

# Run the application
python run.py
```

### First Run

On first run, the application will:
1. Automatically load and process the RBI CSV data from `data/raw/`
2. Create all necessary SQLite databases
3. Prompt you to login or register
4. Present the main menu with 11 options

---

## Usage Guide

### Login / Register

```
┌─────────────────────────────────────────────────────────────┐
│  [L] Login — Enter user_id + PIN                            │
│  [R] Register — Create new account                           │
│       • Adult (18+): Full access                             │
│       • Minor (<18): Guardian KYC required                   │
│  [F] Forgot Card Number — Recover via phone + email          │
│  [P] Forgot PIN — Reset via recovery code                    │
└─────────────────────────────────────────────────────────────┘
```

### Main Menu (11 Options)

| Option | Feature | Description |
|--------|---------|-------------|
| 1 | ATM Simulator | Withdraw, deposit, transfer, mini-statement, loan offers |
| 2 | Data Analysis | Bank KPIs, trends, market share, correlations |
| 3 | ML/DL Predictions | All 20 models — forecast, cluster, score, detect |
| 4 | My Profile | Dashboard, spending, credit score, passbook |
| 5 | Bank Explorer | Browse 65 banks, compare, recommend, attributes |
| 6 | Web Dashboard | Launch Flask dashboard in browser (5 pages) |
| 7 | Reports | PDF, CSV, Excel exports, training data |
| 8 | Demo / Tour | 5 educational walkthroughs |
| 9 | Model Freshness | Auto-retrain status, model health report |
| 10 | Settings | Refresh data, DB stats, export training datasets |
| 11 | Exit | Logout and close |

### Web Dashboard

From the CLI, select option 6 to launch the web dashboard at `http://127.0.0.1:5000`:

- **Home** — KPIs, gauges, top banks, monthly trends
- **Analysis** — RBI data charts and tables
- **ML** — Model results with Plotly visualizations
- **Personal** — User portfolio and analytics
- **Monitoring** — Model health and freshness

---

## Database Structure

The system uses **3 SQLite databases** managed by a singleton `DatabaseManager`:

| Database | Contents | Size |
|----------|----------|------|
| `atm_data.db` | RBI ATM/card statistics (3 tables, 65 banks × 24 months) | Read-only |
| `ecosystem.db` | Users, transactions, feedback, sessions, goals, metrics | Read-write |
| `feature_store.db` | Feature definitions, model registry, training datasets, snapshots | Append-only |

> See [`docs/architecture/02-database-architecture.md`](docs/architecture/02-database-architecture.md) for complete schema with all table columns and relationships.

---

## Technical Stack

| Category | Technologies |
|----------|-------------|
| **Language** | Python 3.13 |
| **CLI** | Rich (tables, panels, progress bars, markup) |
| **Web** | Flask, Plotly, Jinja2 |
| **Data** | Pandas, NumPy, SQLite |
| **ML/DL** | Scikit-learn, XGBoost, Prophet, TensorFlow/Keras, StatsModels |
| **Visualization** | Matplotlib, Seaborn, Plotext, Plotly |
| **Reports** | fpdf2, OpenPyXL, PyMuPDF, Pillow |
| **NLP** | VADER Sentiment |
| **Testing** | Pytest (60 tests) |

---

## Project Structure

```
ATM-Simulation-main/
├── run.py                     # Entry point
├── requirements.txt           # Dependencies
├── .gitignore
├── README.md
├── docs/architecture/         # Architecture documentation
│   ├── README.md
│   ├── 00-system-architecture.png
│   ├── 01-database-erd.png
│   ├── 02-ml-architecture.png
│   ├── 03-data-pipeline.png
│   ├── 04-cli-menu-structure.png
│   ├── 05-user-system-flow.png
│   └── *.md (8 documents)
├── data/
│   ├── raw/                   # RBI CSV data (auto-loaded)
│   └── processed/             # Analytics databases
├── src/
│   ├── main.py                # CLI application
│   ├── data_ingestion.py      # CSV → SQLite pipeline
│   ├── data_analysis.py       # Query & analysis
│   ├── data_visualization.py  # Chart generation (14 methods)
│   ├── data_generator.py      # Training data export
│   ├── atm_simulator.py       # ATM operations
│   ├── user_manager.py        # User auth & management
│   ├── user_analytics.py      # Personal analytics
│   ├── report_generator.py    # PDF/CSV/Excel/Passbook
│   ├── demo_manager.py        # Educational tours
│   ├── ui_helpers.py          # Bank selector UI
│   ├── auto_retrain.py        # Scheduled retraining
│   ├── bank_attributes.py     # 65 bank metadata
│   ├── utils.py               # Shared utilities
│   ├── data/
│   │   ├── db_manager.py      # DatabaseManager singleton
│   │   ├── feature_store.py   # Feature definitions
│   │   ├── model_registry.py   # Version tracking
│   │   ├── data_catalog.py    # Export lineage
│   │   └── generate_diagrams.py
│   ├── models/                # 20 ML/DL models
│   │   ├── base_model.py
│   │   ├── cash_demand_forecaster.py
│   │   ├── transaction_predictor.py
│   │   ├── bank_clustering.py
│   │   ├── anomaly_detector.py
│   │   ├── trend_analyzer.py
│   │   ├── channel_migration.py
│   │   ├── what_if_simulator.py
│   │   ├── credit_scorer.py
│   │   ├── churn_predictor.py
│   │   ├── loan_default_model.py
│   │   ├── bank_recommender.py
│   │   ├── spending_forecaster.py
│   │   ├── lstm_forecaster.py
│   │   ├── real_time_fraud_detector.py
│   │   ├── investment_recommender.py
│   │   ├── atm_replenishment.py
│   │   ├── rfm_segmenter.py
│   │   ├── savings_optimizer.py
│   │   ├── sentiment_analyzer.py
│   │   └── model_monitor.py
│   └── dashboard/
│       ├── app.py
│       └── templates/         # 6 HTML templates
├── tests/                     # 60 test cases
└── outputs/                   # Generated files
    ├── charts/
    ├── reports/
    └── training_data/
```

---

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_ml.py -v

# Run with coverage
pytest tests/ --cov=src
```

Currently **60 tests** covering:
- ML model training and prediction (7 tests)
- Phase 2 models (fraud, investment, replenishment, RFM, savings, sentiment, monitoring)
- User validation (name, phone, email, age)
- Demo manager content verification
- Credit scoring, churn, loan, recommendation

---

## Architecture Documentation

The [`docs/architecture/`](docs/architecture/) folder contains complete blueprints for the entire system:

| Document | What it covers |
|----------|----------------|
| `01-system-architecture.md` | High-level component diagram, layer breakdown, design patterns |
| `02-database-architecture.md` | All 3 databases with complete table schemas and relationships |
| `03-data-workflow.md` | End-to-end pipeline from CSV ingestion to output generation |
| `04-ml-model-architecture.md` | All 20 models with algorithms, inputs, outputs, and training flow |
| `05-cli-workflow.md` | Menu navigation map with all 11+6 sub-menu options |
| `06-user-system.md` | Registration flows (adult/minor), KYC, passbook generation |
| `07-web-dashboard.md` | Flask routes, template structure, data flow |
| `08-roadmap.md` | Project evolution, known limitations, future plans |

Plus 6 comprehensive PNG diagrams:
- `00-system-architecture.png` — Full layered system
- `01-database-erd.png` — ER diagram across all databases
- `02-ml-architecture.png` — All models with connections
- `03-data-pipeline.png` — Data flow visualization
- `04-cli-menu-structure.png` — Menu navigation map
- `05-user-system-flow.png` — User registration & auth flows

---

## License

This project is developed for educational and demonstration purposes. RBI data is publicly available and used for analysis only.
