# CLI Menu Structure & Workflow

## Entry Point

```
run.py
  |
  +--> BankingAnalyticsSuite().run()
         |
         +--> initialize()
         |      +--> DataAnalysis()  # loads RBI data
         |      +--> DataVisualization(da)
         |      +--> ReportGenerator(da)
         |
         +--> login_gate()
         |      +--> show_banner()
         |      +--> UserManager.login_or_register()
         |      |      +--> Login (existing user)
         |      |      +--> Register (new user)
         |      |             +--> Adult (age >= 18)
         |      |             +--> Minor (age < 18, needs guardian)
         |      |      +--> Forgot Card Number
         |      |      +--> Forgot PIN
         |      |      +--> Recovery Code
         |      +--> Returns user dict
         |
         +--> main_menu()
```

## Main Menu (11 Options)

```
+==================================================+
|  ATM & Banking Ecosystem v3.0                    |
|  [User: name] | [Account: ACCT-XXXX] | Balance   |
+==================================================+
| Option | Feature                                  |
+--------+------------------------------------------+
| 1      | [ATM] ATM Simulator (Your Account)        |
| 2      | [Data] Data Analysis & Insights           |
| 3      | [ML] ML/DL Predictions & Modeling         |
| 4      | [Profile] My Profile & Portfolio          |
| 5      | [Banks] Bank Explorer & Compare           |
| 6      | [Web] Web Dashboard                       |
| 7      | [Reports] Reports, Exports & Training Data|
| 8      | [Demo] Demo / Tour                        |
| 9      | [Retrain] Model Freshness & Auto-Retrain  |
| 10     | [Settings] Settings & Data Management     |
| 11     | [Exit] Logout / Exit                      |
+--------+------------------------------------------+
```

## Sub-Menus Navigation Map

```
MAIN MENU
  |
  +--- 1: ATM Simulator
  |      +--> PIN check (3 attempts)
  |      +--> Balance Inquiry
  |      +--> Cash Withdrawal (daily limit: 50000)
  |      +--> Cash Deposit
  |      +--> Fund Transfer (to phone/account)
  |      +--> Mini Statement (last 10 txns)
  |      +--> Change PIN
  |      +--> Savings Goals
  |      +--> Loan Offers (personal/education/home/vehicle)
  |      +--> Fraud check on every txn
  |      +--> SMS + Receipt simulation
  |
  +--- 2: Data Analysis (10 options)
  |      +--> Bank Overview & KPIs
  |      +--> Compare Banks Side-by-Side
  |      +--> Monthly Trend Analysis
  |      +--> Market Share Analysis
  |      +--> Channel-wise Transaction Breakdown
  |      +--> Correlation Heatmap
  |      +--> Growth Rate (MoM)
  |      +--> My Personal Analytics
  |      +--> Demo Walkthrough
  |      +--> Back
  |
  +--- 3: ML/DL Predictions (16 options)
  |      +--> Cash Demand Forecast (Prophet)
  |      +--> Transaction Volume Prediction (XGBoost)
  |      +--> Bank Clustering (K-Means + PCA)
  |      +--> Anomaly / Fraud Detection
  |      +--> Trend Decomposition
  |      +--> Channel Migration Prediction
  |      +--> What-If Scenario Simulator
  |      +--> Credit Score Prediction
  |      +--> Churn Risk Analysis
  |      +--> Loan Default Risk Assessment
  |      +--> Bank Recommendation
  |      +--> Retrain All Models & Compare
  |      +--> Replenishment Optimizer
  |      +--> LSTM vs Prophet Comparison
  |      +--> Demo Walkthrough
  |      +--> Back
  |
  +--- 4: My Profile (12 options)
  |      +--> Account Dashboard
  |      +--> Spending Analysis
  |      +--> Credit Score Breakdown
  |      +--> Transaction History
  |      +--> Loan Offers
  |      +--> Savings Goals
  |      +--> Investment Suggestions
  |      +--> RFM Analysis
  |      +--> Savings Goal Optimizer
  |      +--> Download Passbook
  |      +--> Edit Profile
  |      +--> Back
  |
  +--- 5: Bank Explorer (7 options)
  |      +--> Browse All 65 Banks (paginated, filtered)
  |      +--> Compare Banks Side-by-Side
  |      +--> Bank Attributes Table (Rates & Fees)
  |      +--> Best Bank For Me (Recommendation)
  |      +--> Random Bank / Surprise Me
  |      +--> Your Bank vs Industry
  |      +--> Back
  |
  +--- 6: Web Dashboard (launches Flask)
  |      +--> Opens http://127.0.0.1:5000 in browser
  |      +--> 5 pages: Home, Analysis, ML, Personal, Monitoring
  |      +--> Threaded (CLI remains usable)
  |
  +--- 7: Reports (9 options)
  |      +--> Generate PDF Report (Global)
  |      +--> Generate Portfolio Report (Personal)
  |      +--> Export Data to CSV
  |      +--> Export to Excel
  |      +--> Save All Charts
  |      +--> View Dataset Summary
  |      +--> Export ML Training Datasets
  |      +--> View Training Data Info
  |      +--> Back
  |
  +--- 8: Demo / Tour (6 options)
  |      +--> Data Analysis Walkthrough
  |      +--> ML Models Explained
  |      +--> ATM Simulator Demo
  |      +--> Profile & Portfolio Tour
  |      +--> Bank Explorer Guide
  |      +--> Back
  |
  +--- 9: Model Freshness
  |      +--> View freshness report (color-coded)
  |      +--> View model metrics summary
  |      +--> Run scheduled retrain
  |
  +--- 10: Settings (7 options)
  |      +--> Refresh RBI Data (from CSV)
  |      +--> View Database Statistics
  |      +--> Reset ATM Daily Usage
  |      +--> Export ML Training Datasets
  |      +--> View Training Data Info
  |      +--> Feedback Sentiment Analysis
  |      +--> Back
  |
  +--- 11: Logout / Exit
         +--> End session
         +--> Close connections
         +--> Exit app
```

## Interaction Flow

```
User Input → Prompt.ask() → choice routing → handler method
                                                    |
                                           +--------+--------+
                                           |                 |
                                    console.status()    Rich Table
                                    (spinner / progress)  output
                                           |                 |
                                    Operation runs     Results shown
                                           |                 |
                                    console.print()    plotext chart
                                    (result/error)     (inline)

                                    [Optional] Chart PNG saved
                                               ↓
                                    Auto-open chart (os.startfile)
```

## Key Design Decisions

1. **No emoji in menus**: All menu icons use text labels (`[ATM]`, `[Data]`, `[ML]`) for cross-terminal compatibility (Windows PowerShell 5.1 cannot render multi-byte emoji)
2. **Rupee sign preserved**: `₹` (`\xe2\x82\xb9`) renders correctly on all terminals and is kept for monetary values
3. **Loop-based menus**: Each sub-menu runs in a `while True:` loop with explicit "Back" option — user returns to parent menu on exit
4. **Rich library throughout**: Tables use `box.ROUNDED` style, colored output with markup, progress bars for long operations
5. **Chart auto-open**: Charts are saved to `outputs/charts/` and auto-opened via `os.startfile` (Windows) or `webbrowser.open`
