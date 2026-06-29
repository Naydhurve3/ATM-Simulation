# ML / DL Model Architecture

## Model Inventory (20 Models)

```
PHASE 1 — Core Models (13)
+============================================================+
| Model                 | Algorithm       | Data Source       |
+============================================================+
| CashDemandForecaster  | Prophet         | atm_card_stats    |
| TransactionPredictor  | XGBoost         | atm_card_stats    |
| BankClustering        | K-Means + PCA   | bank_summary      |
| AnomalyDetector       | Isolation Forest| atm_card_stats    |
| TrendAnalyzer         | StatsModels     | atm_card_stats    |
| ChannelMigrationPred  | Linear/Prophet  | atm_card_stats    |
| WhatIfSimulator       | Linear Regression| atm_card_stats   |
| CreditScorer          | GradientBoost   | users + txns      |
| ChurnPredictor        | RandomForest    | users + txns      |
| LoanDefaultModel      | Rule-based      | users profile     |
| BankRecommender       | Rule-based      | bank_attributes   |
| SpendingForecaster    | Linear/Prophet  | transactions      |
| LSTMForecaster        | TensorFlow LSTM | atm_card_stats    |
+============================================================+

PHASE 2 — Enhanced Models (7)
+============================================================+
| Model                 | Algorithm       | Data Source       |
+============================================================+
| RealTimeFraudDetector | Rule-based      | transactions      |
| InvestmentRecommender | Portfolio Theory| user profile      |
| ATMReplenishmentOptim| EOQ Model       | demand forecast   |
| RFMSegmenter          | RFM Scoring    | transaction history|
| SavingsGoalOptimizer  | Financial Calc  | user inputs       |
| SentimentAnalyzer     | VADER          | feedback table    |
| ModelMonitor          | Stats Tracking | model_metrics     |
+============================================================+
```

---

## Model Architecture Diagram

```
                       ATM CARD STATISTICS (atm_card_stats)
                                  |
          +-----------------------+------------------------+
          |                       |                        |
          v                       v                        v
+-------------------+  +-------------------+  +--------------------+
| CashDemandForecast|  | TransactionPred   |  | BankClustering     |
| - Prophet()       |  | - XGBRegressor()  |  | - KMeans()         |
| - train(bank,met) |  | - train(target)   |  | - PCA(2)           |
| - predict(b,p)    |  | - predict(feats)  |  | - train(k)         |
| metrics: MAE,RMSE |  | metrics: MAE,R2   |  | metrics: silhouette |
+--------+----------+  +--------+----------+  +----------+---------+
         |                       |                       |
         v                       v                       v
+-------------------+  +-------------------+  +--------------------+
| AnomalyDetector   |  | TrendAnalyzer     |  | ChannelMigration   |
| - IsolationForest |  | - seasonal_decom  |  | - LinearReg        |
| - train(contam)   |  | - decompose(b,m)  |  | - train(bank)      |
| - predict()       |  |                   |  | - predict(b,months)|
| metrics: anomaly% |  | Obs/Trend/Seasonal|  | digital_share_pred |
+-------------------+  +-------------------+  +--------------------+
         |
         v
+-------------------+
| WhatIfSimulator   |
| - LinearReg       |
| - train(target)   |
| - simulate(changes)|
| impact estimation |
+-------------------+

                       USER DATA (ecosystem.db)
                              |
          +-------------------+-------------------+
          |                   |                   |
          v                   v                   v
+------------------+  +----------------+  +-------------------+
| CreditScorer     |  | ChurnPredictor |  | LoanDefaultModel  |
| - GradientBoost  |  | - RandomForest|  | - Rule-based      |
| - train()        |  | - train()     |  | - predict(usr,amt)|
| - predict(user)  |  | - predict()  |  | risk_score/elig   |
| score: 300-900   |  | risk: H/M/L  |  | amort_schedule    |
+------------------+  +----------------+  +--------+----------+
         |                   |                      |
         +-------------------+----------------------+
                             |
                             v
                  +-------------------+
                  | BankRecommender   |
                  | - Rule-based      |
                  | - recommend(prefs)|
                  | top-5 banks       |
                  +-------------------+

                  TRANSACTIONS (ecosystem.db)
                          |
          +---------------+---------------+
          |               |               |
          v               v               v
+-----------------+ +--------------+ +----------------+
| SpendingForecast| | RFMSegmenter | | SavingsGoal    |
| - Prophet/LinReg| | - R/F/M calc | | Optimizer      |
| - predict()     | | - segment()  | | - optimize()   |
+-----------------+ +--------------+ +----------------+
          |               |               |
          +---------------+---------------+
                          |
                          v
                +-------------------+
                | SavingsGoalOptim  |
                | - Financial Calc  |
                | - monthly deposit |
                | - interest proj   |
                +-------------------+

         REAL-TIME & SPECIALIZED MODELS
          +--------------------+
          | RealTimeFraudDetect|
          | - Rule-based       |
          | - score(txn) 0-100 |
          | - threshold > 70   |
          +--------------------+
          +--------------------+
          | InvestmentRecomm   |
          | - Portfolio Theory |
          | - 4 risk profiles  |
          | - 6 product types  |
          +--------------------+
          +--------------------+
          | ATMReplenishment   |
          | - EOQ Model        |
          | - optimize(demand) |
          | - compare_strats   |
          +--------------------+
          +--------------------+
          | SentimentAnalyzer  |
          | - VADER Sentiment  |
          | - analyze_feedback |
          | - Positive/Neg/Neu |
          +--------------------+
```

---

## Model Details

### 1. CashDemandForecaster
- **File**: `src/models/cash_demand_forecaster.py`
- **Algorithm**: Facebook Prophet
- **Input**: Bank name, metric name (e.g., "DC_Vol_Cash_ATM")
- **Output**: Predicted value with lower/upper bounds
- **Training**: Lazy — trains on first `predict()` call if not pre-loaded
- **Metrics**: MAE, RMSE, MAPE

### 2. TransactionPredictor
- **File**: `src/models/transaction_predictor.py`
- **Algorithm**: XGBoost Regressor
- **Input**: Feature matrix from atm_card_stats
- **Output**: Predicted transaction volume/value
- **Training**: Optional pre-trained model, can retrain on demand
- **Metrics**: MAE, RMSE, R2
- **Extras**: Feature importance plot, model comparison (pre-trained vs retrained)

### 3. BankClustering
- **File**: `src/models/bank_clustering.py`
- **Algorithm**: K-Means (k=4 default) + PCA 2D projection
- **Input**: bank_summary table (Total_ATMs, Total_Cards, Total_Txn_Vol, Total_Txn_Val, Digital_Share)
- **Output**: Cluster labels + PCA coordinates
- **Metrics**: Silhouette score, PCA explained variance ratio
- **Extras**: Optimal K search (2..8), cluster profiles

### 4. AnomalyDetector
- **File**: `src/models/anomaly_detector.py`
- **Algorithm**: Isolation Forest
- **Input**: atm_card_stats numeric columns
- **Output**: Per-bank anomaly scores, flagged months
- **Parameters**: Contamination rate (default 0.05)
- **Metrics**: Flagged count, anomaly score stats

### 5. TrendAnalyzer
- **File**: `src/models/trend_analyzer.py`
- **Algorithm**: StatsModels seasonal_decompose
- **Output**: Observed, Trend, Seasonal, Residual components
- **Requires**: 4+ data points

### 6. ChannelMigrationPredictor
- **File**: `src/models/channel_migration.py`
- **Algorithm**: Linear Regression + Prophet hybrid
- **Input**: Historical digital share by bank
- **Output**: Predicted digital share N months ahead
- **Metrics**: Shift percentage, current vs predicted

### 7. WhatIfSimulator
- **File**: `src/models/what_if_simulator.py`
- **Algorithm**: Linear Regression
- **Input**: User-defined feature changes (e.g., "ATMs_On_Site=1000")
- **Output**: Estimated impact on target metric
- **Metrics**: R2 of underlying model

### 8. CreditScorer
- **File**: `src/models/credit_scorer.py`
- **Algorithm**: Gradient Boosting (sklearn)
- **Input**: User features (age, balance, txn_count, fraud_count, income_bracket)
- **Output**: Credit score (300-900)
- **Special**: Minor users get rule-based score (max 600)

### 9. ChurnPredictor
- **File**: `src/models/churn_predictor.py`
- **Algorithm**: Random Forest (sklearn)
- **Input**: User features + recency metrics
- **Output**: Risk score (0-1) + risk level (HIGH/MEDIUM/LOW)
- **Metrics**: Accuracy, Precision, Recall, F1

### 10. LoanDefaultModel
- **File**: `src/models/loan_default_model.py`
- **Algorithm**: Rule-based scoring + eligibility checks
- **Input**: User profile + requested loan amount/rate/tenure
- **Output**: Eligibility, risk score, recommended max, amortization schedule
- **Special**: Minors automatically ineligible

### 11. BankRecommender
- **File**: `src/models/bank_recommender.py`
- **Algorithm**: Rule-based weighted scoring
- **Input**: User preferences (risk, network, fees, limits)
- **Output**: Top-5 ranked banks with match scores and explanations

### 12. SpendingForecaster
- **File**: `src/models/spending_forecaster.py`
- **Algorithm**: Linear Regression / Prophet
- **Input**: User transaction history
- **Output**: Predicted future spending

### 13. LSTMForecaster
- **File**: `src/models/lstm_forecaster.py`
- **Algorithm**: TensorFlow LSTM (2 layers, 50 units each)
- **Input**: Historical time series from atm_card_stats
- **Output**: Predicted value with confidence bounds
- **Status**: Falls back to dummy class if TensorFlow unavailable (Windows protobuf issue)

### Phase 2 Models

### 14. RealTimeFraudDetector
- **Algorithm**: Rule-based scoring
- **Features**: Amount > 3x avg, hour (2-5 AM flagged), rapid succession, high-velocity
- **Output**: Fraud score (0-100), flagged if > 70

### 15. InvestmentRecommender
- **Algorithm**: Modern Portfolio Theory allocation
- **Products**: FD, Equity MF, Debt MF, PPF, Gold, Cash
- **Risk profiles**: Conservative (20/80 eq/debt) → Aggressive (80/20)

### 16. ATMReplenishmentOptimizer
- **Algorithm**: Economic Order Quantity (EOQ) model
- **Input**: Predicted monthly demand
- **Output**: Optimal refill amount, frequency, cost breakdown
- **Extras**: Strategy comparison (weekly/bi-weekly/monthly)

### 17. RFMSegmenter
- **Algorithm**: Recency/Frequency/Monetary scoring (1-5 each)
- **Segments**: Champions, Loyal, At Risk, Needs Attention, Hibernating, Lost

### 18. SavingsGoalOptimizer
- **Algorithm**: Financial goal calculation
- **Input**: Target amount, deadline, income, expenses
- **Output**: Required monthly deposit, recommended product, maturity value

### 19. SentimentAnalyzer
- **Algorithm**: VADER (Valence Aware Dictionary and sEntiment Reasoner)
- **Input**: Feedback text from ecosystem.db
- **Output**: Positive/Neutral/Negative labels + compound score

### 20. ModelMonitor
- **Algorithm**: Metrics tracking and staleness detection
- **Input**: model_metrics table from ecosystem.db
- **Output**: Per-model health status, staleness in days

---

## Unified BaseModel Interface

All models extend `BaseModel` (`src/models/base_model.py`):

```python
class BaseModel:
    def __init__(self, name):
        self.model_name = name
        self.is_trained = False
        self.metrics = {}
        self.version = 1

    def train(self, *args, **kwargs): ...
    def predict(self, *args, **kwargs): ...
    def save(self, model_dir=None): ...
    def load(self, model_dir=None): ...
```

Models can be:
- **Saved/loaded** via joblib to `data/models/`
- **Versioned** in `ModelRegistry` (optional)
- **Monitored** via `ModelMonitor` for staleness and metrics drift
- **Auto-retrained** by `AutoRetrainScheduler` on trigger conditions
