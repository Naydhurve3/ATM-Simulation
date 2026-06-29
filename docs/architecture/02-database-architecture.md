# Database Architecture

## Overview

The system uses **three SQLite databases** managed by the `DatabaseManager` singleton (`src/data/db_manager.py`). All connections flow through this single manager to prevent connection leaks and ensure consistency.

```
+=========================================================+
|                  DatabaseManager                         |
|  Singleton — auto-reconnect via SELECT 1 probe          |
|  All consumers call db.get_connection(db_name)           |
+=========================================================+
         |                    |                    |
         v                    v                    v
+------------------+  +------------------+  +------------------+
|   atm_data.db    |  |  ecosystem.db    |  | feature_store.db |
|  (RBI Statistics)|  | (User & Activity) |  | (Analytics)      |
+------------------+  +------------------+  +------------------+
```

---

## 1. atm_data.db (Read-Only RBI Data)

**Path**: `data/atm_data.db` (via `DB_PATH` from `src/utils.py`)

**Populated by**: `DataIngestion.run_pipeline()` which reads `data/raw/RBI_ATM_Card_Statistics.csv`

### Tables

### atm_card_stats
The main fact table — one row per bank per month.

| Column | Type | Description |
|--------|------|-------------|
| Bank_Name | TEXT | Bank name (normalized: UPPER, stripped) |
| Reporting_Month | TEXT | Month string (e.g., "Apr-2023") |
| Month_Num | INTEGER | Derived numeric month (0, 1, 2, ...) |
| Bank_Type | TEXT | Public/Private/Foreign/Payment/Small Finance |
| ATMs_On_Site | REAL | On-site ATMs |
| ATMs_Off_Site | REAL | Off-site ATMs |
| PoS | REAL | Point of Sale terminals |
| Micro_ATMs | REAL | Micro ATM devices |
| Bharat_QR_Codes | REAL | Bharat QR codes |
| UPI_QR_Codes | REAL | UPI QR codes |
| Credit_Cards_Outstanding | REAL | Outstanding credit cards |
| Debit_Cards_Outstanding | REAL | Outstanding debit cards |
| CC_Vol_* / CC_Val_* | REAL | Credit card volume/value by channel |
| DC_Vol_* / DC_Val_* | REAL | Debit card volume/value by channel |
| Total_ATMs | REAL | Computed: ATMs_On_Site + ATMs_Off_Site |
| Total_Cards | REAL | Computed: Credit + Debit |
| CC_Total_Vol / CC_Total_Val | REAL | Computed credit card totals |
| DC_Total_Vol / DC_Total_Val | REAL | Computed debit card totals |
| Total_Txn_Vol | REAL | Computed: CC_Total_Vol + DC_Total_Vol |
| Total_Txn_Val | REAL | Computed: CC_Total_Val + DC_Total_Val |
| Digital_QR_Codes | REAL | Computed: Bharat_QR + UPI_QR |
| Digital_Vol | REAL | Online + PoS volume |
| Cash_Vol | REAL | Cash ATM + Cash PoS volume |
| Digital_Share | REAL | % Digital: (Digital_Vol / Total_Txn_Vol) * 100 |
| Cash_Share | REAL | % Cash: (Cash_Vol / Total_Txn_Vol) * 100 |

### bank_summary
Aggregated per-bank statistics (grouped by Bank_Name).

| Column | Type | Description |
|--------|------|-------------|
| Bank_Name | TEXT | Bank name |
| Total_ATMs | REAL | Mean ATMs |
| Total_Cards | REAL | Mean cards |
| Total_Txn_Vol | REAL | Sum of transaction volume |
| Total_Txn_Val | REAL | Sum of transaction value |
| Digital_Share | REAL | Mean digital share % |

### monthly_aggregate
Monthly industry totals (grouped by Reporting_Month).

| Column | Type | Description |
|--------|------|-------------|
| Reporting_Month | TEXT | Month string |
| Month_Num | INTEGER | Numeric month |
| Total_ATMs | REAL | Sum of all bank ATMs |
| Total_Cards | REAL | Sum of all cards |
| Total_Txn_Vol | REAL | Sum of all transaction volume |
| Total_Txn_Val | REAL | Sum of all transaction value |
| Digital_Share | REAL | Mean digital share |

---

## 2. ecosystem.db (User & Activity Data)

**Path**: `data/ecosystem.db` (via `ECOSYSTEM_DB` from `src/utils.py`)

**Populated by**: `UserManager` and `ATMSimulator` at runtime

### Tables

### users
| Column | Type | Description |
|--------|------|-------------|
| user_id | INTEGER PK | Auto-increment |
| name | TEXT | Full name |
| age | INTEGER | Age |
| is_minor | BOOLEAN | True if age < 18 |
| guardian_name | TEXT | Guardian name (minors only) |
| guardian_phone | TEXT | Guardian phone (minors only) |
| guardian_relation | TEXT | Relation (minors only) |
| phone | TEXT | Phone number |
| email | TEXT | Email address |
| bank | TEXT | Selected bank name |
| account_no | TEXT | Unique account number (format: ACCT-XXXXXXXXXX) |
| card_no | TEXT | Debit card number (format: XXXX-XXXX-XXXX-XXXX) |
| pin | TEXT | 4-digit PIN (hashed) |
| balance | REAL | Current account balance |
| credit_score | INTEGER | 300-900 |
| atm_daily_usage | REAL | Today's ATM usage counter |
| atm_last_used | TEXT | Last ATM usage timestamp |
| income_bracket | TEXT | Income category |
| is_active | BOOLEAN | Account active flag |
| created_at | TEXT | Registration timestamp |
| updated_at | TEXT | Last update timestamp |

### transactions
| Column | Type | Description |
|--------|------|-------------|
| txn_id | INTEGER PK | Auto-increment |
| user_id | INTEGER FK | References users.user_id |
| type | TEXT | withdraw / deposit / transfer / fee / credit |
| amount | REAL | Transaction amount |
| balance_before | REAL | Balance before txn |
| balance_after | REAL | Balance after txn |
| timestamp | TEXT | Transaction time |
| description | TEXT | Optional note |
| is_fraud | BOOLEAN | Fraud flag |
| channel | TEXT | ATM / Online / Branch |

### feedback
| Column | Type | Description |
|--------|------|-------------|
| feedback_id | INTEGER PK | Auto-increment |
| user_id | INTEGER FK | References users.user_id |
| text | TEXT | Feedback content |
| rating | INTEGER | 1-5 rating |
| created_at | TEXT | Submission timestamp |

### atm_sessions
| Column | Type | Description |
|--------|------|-------------|
| session_id | INTEGER PK | Auto-increment |
| user_id | INTEGER FK | References users.user_id |
| login_time | TEXT | Session start |
| logout_time | TEXT | Session end |
| actions_count | INTEGER | Operations performed |

### user_milestones
| Column | Type | Description |
|--------|------|-------------|
| milestone_id | INTEGER PK | Auto-increment |
| user_id | INTEGER FK | References users.user_id |
| milestone_type | TEXT | first_deposit / savings_goal / etc. |
| achieved_at | TEXT | Achievement timestamp |

### savings_goals
| Column | Type | Description |
|--------|------|-------------|
| goal_id | INTEGER PK | Auto-increment |
| user_id | INTEGER FK | References users.user_id |
| goal_name | TEXT | Goal description |
| target_amount | REAL | Target amount |
| current_amount | REAL | Current savings |
| deadline | TEXT | Target date |
| status | TEXT | active / completed / abandoned |

### retrain_log
| Column | Type | Description |
|--------|------|-------------|
| log_id | INTEGER PK | Auto-increment |
| model_name | TEXT | Model that was retrained |
| triggered_by | TEXT | Trigger reason |
| version | INTEGER | Model version after retrain |
| txn_count | INTEGER | Transactions at retrain time |
| user_count | INTEGER | Users at retrain time |
| trained_at | TEXT | Retrain timestamp |

### model_metrics
| Column | Type | Description |
|--------|------|-------------|
| metric_id | INTEGER PK | Auto-increment |
| model_name | TEXT | Model name |
| version | INTEGER | Model version |
| metrics_summary | TEXT | JSON blob of metrics |
| trained_at | TEXT | Training timestamp |

---

## 3. feature_store.db (Analytics Metadata)

**Path**: `data/processed/analytics/feature_store.db`

**Populated by**: `FeatureStore`, `ModelRegistry`, `DataCatalog`

### Tables

### feature_definitions
| Column | Type | Description |
|--------|------|-------------|
| feature_id | INTEGER PK | Auto-increment |
| feature_name | TEXT UNIQUE | Feature name |
| feature_set | TEXT | Set name (e.g., "spending", "profile") |
| description | TEXT | Human-readable description |
| sql_expression | TEXT | SQL for computing the feature |
| data_type | TEXT | Feature data type |
| created_at | TIMESTAMP | Creation time |

### feature_snapshots
| Column | Type | Description |
|--------|------|-------------|
| snapshot_id | INTEGER PK | Auto-increment |
| feature_set | TEXT | Set name |
| snapshot_label | TEXT | Snapshot identifier |
| row_count | INTEGER | Number of rows |
| created_at | TIMESTAMP | Snapshot time |

### training_datasets
| Column | Type | Description |
|--------|------|-------------|
| dataset_id | INTEGER PK | Auto-increment |
| scenario | TEXT | Export scenario name |
| export_timestamp | TEXT | When exported |
| tables_exported | TEXT | Tables included |
| row_counts | TEXT | Row counts per table |
| file_paths | TEXT | CSV file paths |
| schema_snapshot | TEXT | Schema at export time |
| created_at | TIMESTAMP | Creation time |

### model_registry / model_versions
| Column | Type | Description |
|--------|------|-------------|
| model_id | INTEGER PK | Auto-increment |
| model_name | TEXT | Model name |
| version_id | INTEGER PK | Version ID |
| version | INTEGER | Version number |
| hyperparameters | TEXT | JSON hyperparams |
| metrics | TEXT | JSON evaluation metrics |
| training_dataset_id | INTEGER FK | Dataset used |
| feature_snapshot_id | INTEGER FK | Features used |
| model_path | TEXT | Saved model path |
| training_duration_ms | REAL | Training time |
| is_production | BOOLEAN | Production flag |
| trained_at | TIMESTAMP | Training timestamp |

---

## Inter-Database Relationships

```
atm_data.db                          ecosystem.db
+-------------+                     +-------------+
| atm_card_stats|----Bank_Name---->| users.bank  |
| bank_summary |----Bank_Name---->| users.bank  |
| monthly_agg  |                     +------+------+
+-------------+                            |
        |                                  |
        v                                  v
   DataAnalysis                     UserManager / ATMSimulator
        |                                  |
        +----------+   ReportGenerator   +-+
                   |                       |
              charts/PDFs              passbook/
```

## Connection Architecture

All connections flow through `DatabaseManager`:

```
src/                              Connection Source
─────────────────────────────────────────────────────
data_ingestion.py              db.get_connection("atm_data")
data_analysis.py               via DataIngestion (same connection)
user_manager.py                db.get_connection("ecosystem")
user_analytics.py              db.get_connection("ecosystem")
data_generator.py              db.get_connection("ecosystem")
auto_retrain.py                db.get_connection("ecosystem")
report_generator.py            db.get_connection("ecosystem")
model_monitor.py               db.get_connection("ecosystem")
credit_scorer.py               db.get_connection("ecosystem")
churn_predictor.py             db.get_connection("ecosystem")
loan_default_model.py          db.get_connection("ecosystem")
spending_forecaster.py         db.get_connection("ecosystem")
feature_store.py               db.get_connection("feature_store")
model_registry.py              db.get_connection("feature_store")
data_catalog.py                db.get_connection("feature_store")
```

### Auto-Reconnect Mechanism

The `DatabaseManager.get_connection()` method probes each connection with `SELECT 1` before returning it. If the probe fails (stale/closed connection), it creates a new connection automatically. This eliminates the "cannot operate on a closed database" error that plagued earlier versions.
