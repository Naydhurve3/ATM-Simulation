# System Architecture Overview

## High-Level Component Diagram

```
+============================================================================+
|                        ATM & BANKING ECOSYSTEM v3.0                        |
+============================================================================+
|                                                                             |
|  +------------------+  +------------------+  +--------------------------+   |
|  |   CLI Interface  |  |  Web Dashboard   |  |    Data Pipeline         |   |
|  |  (run.py/main.py)|  | (Flask/Plotly)   |  | (DataIngestion/Analysis) |   |
|  +--------+---------+  +--------+---------+  +------------+-------------+   |
|           |                     |                          |                |
|           |                     |                          |                |
|  +--------v---------------------v--------------------------v-------------+   |
|  |                        Database Layer                                  |   |
|  |  +----------------+  +------------------+  +------------------------+ |   |
|  |  | DatabaseManager |  |   FeatureStore   |  |     ModelRegistry     | |   |
|  |  |   (Singleton)   |  | (21 features)    |  | (versioned tracking)  | |   |
|  |  +--------+--------+  +--------+---------+  +----------+-------------+ |   |
|  |           |                     |                         |           |   |
|  |  +--------v---------------------v-------------------------v----------+ |   |
|  |  |  Databases: atm_data.db  |  ecosystem.db  |  feature_store.db  |  | |   |
|  |  +------------------------------------------------------------------+ |   |
|  +------------------------------------------------------------------------+   |
|           |                     |                          |                |
|  +--------v---------+  +-------v----------+  +------------v-------------+   |
|  |  ML/DL Models    |  |  User System    |  |  Reports & Exports       |   |
|  |  (20 models)     |  |  (Auth/KYC)     |  |  (PDF/CSV/Excel/Passbook)|   |
|  +------------------+  +------------------+  +--------------------------+   |
|                                                                             |
+============================================================================+
```

## Layer Breakdown

### 1. Presentation Layer
- **CLI Interface** (`run.py` → `src/main.py`): Rich-powered terminal UI with 11-option main menu, 6 sub-menus, progress spinners, formatted tables, and plotext inline charts
- **Web Dashboard** (`src/dashboard/`): Flask app with 5 pages launched from CLI option 6, served on `http://127.0.0.1:5000`

### 2. Data Layer
- **DatabaseManager** (`src/data/db_manager.py`): Singleton managing 3 SQLite databases (`atm_data`, `ecosystem`, `feature_store`) with auto-reconnect, connection pooling, and query logging
- **FeatureStore** (`src/data/feature_store.py`): 21 pre-registered features across 5 sets, snapshot management, compute methods
- **ModelRegistry** (`src/data/model_registry.py`): Versioned model tracking, A/B comparison, production promotion flags
- **DataCatalog** (`src/data/data_catalog.py`): Schema versioning, export lineage tracking, change detection

### 3. Business Logic Layer
- **Data Ingestion/Analysis**: CSV → cleaning → feature engineering → SQLite storage
- **User System**: Login/register (adult + minor), forgot card/pin, recovery flows, KYC, profile management
- **ATM Simulator**: Withdraw, deposit, transfer, mini-statement, fraud detection, loan offers
- **Auto-Retrain Scheduler**: Monitors txn/user thresholds, triggers model retraining

### 4. ML/DL Models Layer
- 20 models including: Prophet, XGBoost, K-Means, Isolation Forest, Gradient Boosting, LSTM (optional), and rule-based recommenders
- Unified `BaseModel` interface with `train()`, `predict()`, `save()`, `load()`, `metrics`

### 5. Output Layer
- Reports: PDF (fpdf2), CSV, Excel (openpyxl)
- Passbook: PDF/PNG with multi-account aggregation
- Charts: matplotlib/seaborn PNGs in `outputs/charts/`

## Key Design Patterns

- **Singleton**: `DatabaseManager` — single connection source for all consumers
- **Property-based connection**: 7 key classes use `@property conn` to re-fetch from `DatabaseManager` on every access
- **Strategy pattern**: Models implement common `BaseModel` interface, interchangeable
- **Observer**: `AutoRetrainScheduler` monitors DB state and triggers retraining
- **Factory**: `models/__init__.py` provides unified model imports

## Data Flow Summary

```
RBI CSV → DataIngestion.load_csv() → clean_data() → save_to_sqlite()
                                                          |
                     DataAnalysis ← DataIngestion ← DatabaseManager
                          |
               +----------+-----------+
               |                      |
         DataVisualization      ReportGenerator
               |                      |
         Charts (PNG)         PDF/CSV/Excel/Passbook
```

## Filesystem Layout

```
ATM-Simulation-main/
  run.py                          # Entry point
  requirements.txt                # Python dependencies
  data/
    raw/                          # RBI CSV data source
    processed/                    # Analytics DBs
  outputs/
    charts/                       # Generated visualizations
    reports/                      # PDF reports & passbooks
    training_data/                # ML training datasets (CSV)
  src/
    main.py                       # CLI application (1520 lines)
    data_ingestion.py             # CSV → SQLite pipeline
    data_analysis.py              # Query & analysis layer
    data_visualization.py         # Chart generation (14 methods)
    data_generator.py             # Training data exports
    atm_simulator.py              # ATM operations
    user_manager.py               # User auth & management
    user_analytics.py             # User-specific analytics
    report_generator.py           # PDF/CSV/Excel reports, passbook
    demo_manager.py               # Educational walkthroughs
    ui_helpers.py                 # BankSelector, paginated browse
    auto_retrain.py               # Scheduled retraining
    bank_attributes.py            # Bank metadata & comparison
    utils.py                      # Shared utilities & paths
    data/
      db_manager.py               # DatabaseManager singleton
      feature_store.py            # Feature definitions
      model_registry.py           # Model version tracking
      data_catalog.py             # Export lineage
      generate_diagrams.py        # Architecture diagram generator
    models/
      __init__.py                 # Unified model imports
      base_model.py               # Abstract base class
      cash_demand_forecaster.py   # Prophet model
      transaction_predictor.py    # XGBoost model
      bank_clustering.py          # K-Means + PCA
      anomaly_detector.py         # Isolation Forest
      trend_analyzer.py           # Statistical decomposition
      channel_migration.py        # Digital share prediction
      what_if_simulator.py        # Scenario simulation
      credit_scorer.py            # Gradient Boosting
      churn_predictor.py          # Churn risk
      loan_default_model.py       # Loan risk assessment
      bank_recommender.py         # Bank matching
      spending_forecaster.py      # Spend prediction
      lstm_forecaster.py          # Deep learning (optional)
      real_time_fraud_detector.py # Rule-based fraud scoring
      investment_recommender.py   # Portfolio allocation
      atm_replenishment.py        # Cash refill optimization
      rfm_segmenter.py            # Customer segmentation
      savings_optimizer.py        # Goal planning
      sentiment_analyzer.py       # Feedback analysis
      model_monitor.py            # Performance tracking
    dashboard/
      app.py                      # Flask application
      templates/                  # HTML templates (6)
  tests/                          # 60 test cases
  docs/architecture/              # This folder
```
