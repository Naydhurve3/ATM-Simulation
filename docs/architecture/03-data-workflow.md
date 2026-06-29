# Data Workflow & Pipeline

## End-to-End Data Flow

```
                         RBI ATM CARD STATISTICS (CSV)
                                   |
                                   v
                  +-------------------------------+
                  |   DataIngestion.load_csv()    |
                  |   - Reads data/raw/*.csv      |
                  |   - Replaces inf/nan          |
                  +-------------------------------+
                                   |
                                   v
                  +-------------------------------+
                  |   DataIngestion.clean_data()   |
                  |   - Normalizes bank names      |
                  |   - Converts numeric fields    |
                  |   - Computes derived columns:  |
                  |     * Total_ATMs               |
                  |     * Total_Cards              |
                  |     * CC_Total_Vol/Val         |
                  |     * DC_Total_Vol/Val         |
                  |     * Total_Txn_Vol/Val        |
                  |     * Digital_Share/Cash_Share |
                  |   - Adds Bank_Type, Month_Num  |
                  +-------------------------------+
                                   |
                                   v
                  +-------------------------------+
                  |  DataIngestion.save_to_sqlite()|
                  |   - Creates 3 tables:          |
                  |     * atm_card_stats (detailed)|
                  |     * bank_summary (per bank)  |
                  |     * monthly_agg (per month)  |
                  |   - Uses DatabaseManager       |
                  +-------------------------------+
                                   |
                                   v
                 +--------------------------------+
                 |       atm_data.db               |
                 |  3 tables (see DB schema doc)   |
                 +--------------------------------+
                                   |
                    +--------------+--------------+
                    |                             |
                    v                             v
     +---------------------------+   +----------------------------+
     |     DataAnalysis          |   |  Models (via _get_data)    |
     |   - bank_overview()       |   |  - CashDemandForecaster    |
     |   - compare_banks()       |   |  - TransactionPredictor    |
     |   - monthly_trend()       |   |  - BankClustering          |
     |   - market_share()        |   |  - AnomalyDetector         |
     |   - channel_breakdown()   |   |  - TrendAnalyzer           |
     |   - growth_rate()         |   |  - ChannelMigration        |
     |   - correlation_matrix()  |   |  - WhatIfSimulator         |
     |   - user_vs_industry()    |   |  - BankRecommender         |
     +---------------------------+   +----------------------------+
                    |                             |
                    v                             v
     +---------------------------+   +----------------------------+
     |   DataVisualization       |   |  Model Registry            |
     |   - 14 chart methods      |   |  - Version tracking        |
     |   - matplotlib/seaborn    |   |  - Metrics storage         |
     |   - outputs/charts/*.png  |   |  - Production promotion    |
     +---------------------------+   +----------------------------+
```

## User Data Pipeline

```
                    User Registration
                           |
                           v
            +----------------------------+
            |   UserManager.register()   |
            |   - Validates name/age/    |
            |     phone/email            |
            |   - Creates account_no     |
            |   - Creates card_no + PIN  |
            |   - Sets credit_score      |
            |   - Generates passbook     |
            +----------------------------+
                           |
                           v
            +----------------------------+
            |    ecosystem.db / users    |
            +----------------------------+
                           |
            +--------------+--------------+
            |                             |
            v                             v
  +-----------------------+    +-------------------------+
  |   ATMSimulator        |    |   UserAnalytics          |
  |   - cash_with()       |    |   - show_dashboard()     |
  |   - cash_dep()        |    |   - show_spending()      |
  |   - fund_transfer()   |    |   - credit_breakdown()   |
  |   - mini_statement()  |    |   - transaction_history()|
  |   - fraud_check()     |    |   - savings_goals()      |
  |   - loan_offers()     |    +-------------------------+
  +-----------------------+                |
           |                               v
           v                  +-------------------------+
  +-----------------------+    |   ReportGenerator       |
  |  ecosystem.db /       |    |   - generate_passbook() |
  |  transactions         |    |   - account_summary()   |
  +-----------------------+    |   - JSON export()       |
                               +-------------------------+
```

## Training Data Export Pipeline

```
DataGenerator.export_all(scenario)
  |
  +--> _export_user_profiles()    --> outputs/training_data/users_*.csv
  +--> _export_transactions()     --> outputs/training_data/transactions_*.csv
  +--> _export_fraud_training()   --> outputs/training_data/fraud_training_*.csv
  +--> _export_credit_scoring()   --> outputs/training_data/credit_scoring_*.csv
  +--> _export_loan_risk()        --> outputs/training_data/loan_risk_*.csv
  +--> _export_churn_analysis()   --> outputs/training_data/churn_analysis_*.csv
  +--> _export_spending_patterns()-> outputs/training_data/spending_*.csv
  +--> _export_bank_preferences() --> outputs/training_data/bank_prefs_*.csv
  +--> _export_user_milestones()  --> outputs/training_data/milestones_*.csv
  +--> _export_engagement()       --> outputs/training_data/engagement_*.csv
  |
  +--> DataCatalog.log_export()   --> feature_store.db / training_datasets
```

Triggered by:
- Manual: Settings menu → Export ML Training Datasets
- Automated: `AutoRetrainScheduler` on model retrain events
- Scenario: `MODEL_RETRAIN`, `MANUAL_EXPORT`, `SCHEDULED`

## Auto-Retrain Cycle

```
AutoRetrainScheduler.retrain_if_needed()
  |
  +--> check_triggers()
  |      * txn_count > threshold (default: 50)
  |      * user_count > threshold (default: 5)
  |      * days_since_last > threshold (default: 7)
  |
  +--> [if triggered]
  |      * Export training data via DataGenerator
  |      * Retrain stale models
  |      * Log to retrain_log table
  |      * Update model_metrics table
  |      * Log to DataCatalog
  |
  +--> get_freshness_report()
         * Compares model age vs threshold
         * Color-coded: green (<7d), yellow (7-14d), red (>14d)
```

## Monitoring & Observability

```
ModelMonitor
  +--> log_metrics(model_name, version, metrics_dict)
  +--> get_latest_metrics(model_name) -> dict
  +--> get_staleness(model_name, max_days) -> int (days stale)
  +--> get_all_model_status() -> list of model summaries
  +--> is_stale(model_name, max_days) -> bool
```

## Key Design Decisions

1. **Single DB connection source**: All modules use `db.get_connection()` from the `DatabaseManager` singleton — eliminates connection leaks and stale connection errors
2. **Computed columns at ingestion**: Derived fields like `Digital_Share`, `Total_Txn_Vol` are computed once during `clean_data()` and stored, rather than recalculated on every query
3. **Dual database segregation**: `atm_data.db` is read-only RBI data; `ecosystem.db` is read-write user data. This prevents accidental corruption of source data
4. **Feature store as metadata DB**: `feature_store.db` tracks what was computed, when, and with which features — enabling reproducibility
5. **Training data export with lineage**: Every export is timestamped, scenario-tagged, and logged in DataCatalog with schema snapshots for reproducibility
