"""Generate comprehensive architecture PNG diagrams for documentation."""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np
from pathlib import Path

OUTPUT = Path(__file__).parent
plt.rcParams["figure.dpi"] = 200
plt.rcParams["font.size"] = 10
plt.rcParams["font.family"] = "sans-serif"

# Color palette
C = {
    "bg": "#1a1a2e",
    "layer1": "#16213e",
    "layer2": "#0f3460",
    "accent": "#e94560",
    "green": "#22c55e",
    "blue": "#3b82f6",
    "amber": "#f59e0b",
    "purple": "#8b5cf6",
    "teal": "#14b8a6",
    "pink": "#ec4899",
    "orange": "#f97316",
    "white": "#f8fafc",
    "gray": "#94a3b8",
    "dark": "#0f172a",
}


def draw_box(ax, x, y, w, h, color, text, text_color="white", fontsize=9, alpha=0.9):
    """Draw a rounded box with text."""
    box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.1",
                          facecolor=color, edgecolor="white", linewidth=1.5, alpha=alpha)
    ax.add_patch(box)
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
            fontsize=fontsize, color=text_color, fontweight="bold")
    return box


def draw_arrow(ax, x1, y1, x2, y2, color="white", lw=1.5, style="->"):
    """Draw an arrow between two points."""
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle=style, color=color, lw=lw, alpha=0.7))


def draw_title(ax, text, y=0.95, fontsize=14):
    """Draw a title at the top of the figure."""
    ax.text(0.5, y, text, ha="center", va="center", fontsize=fontsize,
            fontweight="bold", color=C["white"], transform=ax.transAxes)


def draw_legend(ax, items, loc="lower center", ncol=3):
    """Draw a custom legend."""
    patches = [mpatches.Patch(color=c, label=l, alpha=0.8) for l, c in items]
    legend = ax.legend(handles=patches, loc=loc, ncol=ncol,
                       framealpha=0.3, facecolor=C["dark"],
                       edgecolor=C["gray"], fontsize=8,
                       labelcolor=C["white"])
    return legend


# ======================================================================
# Diagram 1: Full System Architecture
# ======================================================================
def generate_system_architecture():
    fig, ax = plt.subplots(figsize=(18, 12))
    ax.set_xlim(0, 18)
    ax.set_ylim(0, 12)
    ax.set_facecolor(C["bg"])
    fig.patch.set_facecolor(C["bg"])
    ax.axis("off")

    draw_title(ax, "ATM & Banking Ecosystem v3.0 — System Architecture", y=0.97, fontsize=16)

    # Layer backgrounds
    layers = [
        (0.3, 9.5, 17.4, 2.0, C["layer1"], "PRESENTATION LAYER"),
        (0.3, 7.2, 17.4, 2.0, C["layer2"], "DATA LAYER"),
        (0.3, 4.6, 17.4, 2.3, C["layer1"], "BUSINESS LOGIC LAYER"),
        (0.3, 1.8, 17.4, 2.5, C["layer2"], "ML / DL MODELS LAYER"),
        (0.3, 0.2, 17.4, 1.3, C["layer1"], "OUTPUT LAYER"),
    ]
    for x, y, w, h, color, label in layers:
        box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.15",
                              facecolor=color, edgecolor=C["gray"], linewidth=1, alpha=0.5)
        ax.add_patch(box)
        ax.text(x + 0.5, y + h - 0.3, label, fontsize=8, color=C["gray"],
                fontweight="bold", alpha=0.7)

    # Presentation layer boxes
    box_specs = [
        (1.5, 10.0, 3.5, 1.0, C["blue"], "CLI Interface\n(run.py / main.py)"),
        (6.0, 10.0, 3.5, 1.0, C["teal"], "Web Dashboard\n(Flask / Plotly)"),
        (10.5, 10.0, 3.5, 1.0, C["purple"], "Demo / Tour\n(5 walkthroughs)"),
        (14.5, 10.0, 2.5, 1.0, C["amber"], "Bank Explorer\n(65 banks)"),
    ]
    for x, y, w, h, c, t in box_specs:
        draw_box(ax, x, y, w, h, c, t, fontsize=8)

    # Data layer
    box_specs = [
        (1.0, 7.8, 3.0, 1.0, C["blue"], "DatabaseManager\n(Singleton)"),
        (4.5, 7.8, 3.0, 1.0, C["teal"], "FeatureStore\n(21 features)"),
        (8.0, 7.8, 3.0, 1.0, C["purple"], "ModelRegistry\n(Versioned)"),
        (11.5, 7.8, 3.0, 1.0, C["amber"], "DataCatalog\n(Lineage)"),
        (1.0, 6.5, 14.0, 0.8, C["green"], "Databases:  atm_data.db  |  ecosystem.db  |  feature_store.db"),
    ]
    for x, y, w, h, c, t in box_specs:
        draw_box(ax, x, y, w, h, c, t, fontsize=8)

    # Business logic layer
    box_specs = [
        (0.8, 5.0, 3.0, 1.0, C["blue"], "DataIngestion\n(CSV → SQLite)"),
        (4.2, 5.0, 3.0, 1.0, C["teal"], "DataAnalysis\n(Query Layer)"),
        (7.6, 5.0, 3.0, 1.0, C["purple"], "ATMSimulator\n(Withdraw/Deposit)"),
        (11.0, 5.0, 3.0, 1.0, C["amber"], "UserManager\n(Auth/KYC)"),
        (14.4, 5.0, 2.8, 1.0, C["pink"], "AutoRetrain\n(Scheduler)"),
        (0.8, 3.8, 3.0, 0.7, C["green"], "DataVisualization (14 chart methods)"),
        (4.2, 3.8, 3.0, 0.7, C["orange"], "ReportGenerator (PDF/CSV/Excel)"),
        (7.6, 3.8, 3.0, 0.7, C["pink"], "UserAnalytics (Spending/RFM)"),
        (11.0, 3.8, 3.0, 0.7, C["blue"], "DataGenerator (Training exports)"),
    ]
    for x, y, w, h, c, t in box_specs:
        draw_box(ax, x, y, w, h, c, t, fontsize=7)

    # ML models layer
    models_phase1 = [
        (0.5, 2.2, 2.2, 0.8, C["blue"], "Forecasters\n(Prophet/XGBoost)"),
        (3.0, 2.2, 2.2, 0.8, C["teal"], "Cluster/Anomaly\n(K-Means/IForest)"),
        (5.5, 2.2, 2.2, 0.8, C["purple"], "Trend/Channel\n(Stats/Linear)"),
        (8.0, 2.2, 2.2, 0.8, C["amber"], "Credit/Churn/Loan\n(GradBoost/RF/Rule)"),
        (10.5, 2.2, 2.2, 0.8, C["pink"], "Recommender/WhatIf\n(Rule/Linear)"),
        (13.0, 2.2, 2.2, 0.8, C["orange"], "LSTM Forecaster\n(TensorFlow)"),
        (15.7, 2.2, 1.8, 0.8, C["green"], "Spending\nForecast"),
    ]
    for x, y, w, h, c, t in models_phase1:
        draw_box(ax, x, y, w, h, c, t, fontsize=6.5)

    # Phase 2 models
    p2 = [
        (0.5, 1.2, 2.5, 0.7, C["teal"], "FraudDetect / InvestmentRecommend"),
        (3.3, 1.2, 2.5, 0.7, C["purple"], "Replenish / RFM / SavingsGoal"),
        (6.1, 1.2, 2.5, 0.7, C["amber"], "Sentiment / ModelMonitor"),
    ]
    for x, y, w, h, c, t in p2:
        draw_box(ax, x, y, w, h, c, t, fontsize=6.5)

    # Output layer
    box_specs = [
        (1.5, 0.4, 3.0, 0.7, C["blue"], "Charts PNG\n(matplotlib)"),
        (5.5, 0.4, 3.0, 0.7, C["teal"], "Reports PDF\n(fpdf2)"),
        (9.5, 0.4, 3.0, 0.7, C["purple"], "Passbook PNG/PDF\n(PyMuPDF)"),
        (13.5, 0.4, 3.0, 0.7, C["amber"], "Training CSVs\n(10 datasets)"),
    ]
    for x, y, w, h, c, t in box_specs:
        draw_box(ax, x, y, w, h, c, t, fontsize=7)

    # Arrows between layers
    # Presentation -> Data layer
    draw_arrow(ax, 3.25, 10.0, 3.25, 8.8, C["gray"])
    draw_arrow(ax, 8.5, 10.0, 8.5, 8.8, C["gray"])
    # Data -> Business logic
    draw_arrow(ax, 2.5, 7.8, 2.5, 6.0, C["gray"])
    draw_arrow(ax, 8.5, 7.8, 8.5, 6.0, C["gray"])
    # Business -> ML
    draw_arrow(ax, 5.5, 4.6, 5.5, 3.0, C["gray"])
    draw_arrow(ax, 11.0, 4.6, 11.0, 3.0, C["gray"])
    # ML -> Output
    draw_arrow(ax, 3.0, 2.2, 3.0, 1.1, C["gray"])
    draw_arrow(ax, 9.0, 2.2, 9.0, 1.1, C["gray"])

    # Legend
    draw_legend(ax, [
        ("CLI / Web", C["blue"]), ("Data Layer", C["teal"]),
        ("Business Logic", C["amber"]), ("ML Models", C["purple"]),
        ("Output", C["green"]),
    ], loc="lower center", ncol=5)

    path = OUTPUT / "00-system-architecture.png"
    plt.savefig(path, bbox_inches="tight", facecolor=C["bg"])
    plt.close()
    print(f"Generated {path.name}")


# ======================================================================
# Diagram 2: Database ERD
# ======================================================================
def generate_database_erd():
    fig, ax = plt.subplots(figsize=(16, 11))
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 11)
    ax.set_facecolor(C["bg"])
    fig.patch.set_facecolor(C["bg"])
    ax.axis("off")

    draw_title(ax, "Database Architecture — Entity Relationship Diagram", y=0.97, fontsize=15)

    # Database boundaries
    db_colors = {"atm_data": C["blue"], "ecosystem": C["teal"], "feature_store": C["purple"]}
    databases = [
        (0.3, 5.5, 5.0, 5.0, "atm_data.db\n(RBI Statistics)"),
        (5.6, 5.5, 5.5, 5.0, "ecosystem.db\n(User & Activity)"),
        (11.4, 5.5, 4.3, 5.0, "feature_store.db\n(Analytics Metadata)"),
    ]
    for x, y, w, h, label in databases:
        db_name = label.split("\n")[0].replace(".db", "")
        box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.15",
                              facecolor=db_colors.get(db_name, C["gray"]),
                              edgecolor="white", linewidth=2, alpha=0.15)
        ax.add_patch(box)
        ax.text(x + w / 2, y + h - 0.3, label, ha="center", va="top",
                fontsize=9, color="white", fontweight="bold")

    # atm_data tables
    tables_ad = [
        (0.5, 8.5, 4.6, 0.7, "atm_card_stats", ["Bank_Name (PK)", "Reporting_Month (PK)", "ATMs_On/Off_Site",
                                                   "PoS", "QR Codes", "Cards Outstanding",
                                                   "CC/DC Vol/Val", "Total_Txn_Vol/Val",
                                                   "Digital_Share %"]),
        (0.5, 7.0, 4.6, 0.7, "bank_summary", ["Bank_Name (PK)", "Total_ATMs (mean)",
                                                 "Total_Cards (mean)", "Total_Txn_Vol (sum)",
                                                 "Digital_Share (mean)"]),
        (0.5, 5.8, 4.6, 0.6, "monthly_aggregate", ["Reporting_Month (PK)", "Month_Num",
                                                      "Summed metrics across all banks"]),
    ]
    for x, y, w, h, name, fields in tables_ad:
        draw_box(ax, x, y, w, h, C["blue"], f"{name}", fontsize=7)
        for i, f in enumerate(fields):
            ax.text(x + 0.3, y - 0.25 - i * 0.22, f"  {f}", fontsize=5.5, color=C["gray"])

    # ecosystem tables
    tables_eco = [
        (5.8, 8.8, 5.0, 0.6, "users", ["user_id (PK)", "name", "age", "is_minor",
                                          "guardian_name", "phone", "email", "bank",
                                          "account_no", "card_no", "pin (hashed)",
                                          "balance", "credit_score", "income_bracket"]),
        (5.8, 7.2, 5.0, 0.6, "transactions", ["txn_id (PK)", "user_id (FK → users)",
                                                 "type", "amount", "balance_before/after",
                                                 "timestamp", "is_fraud", "channel"]),
        (5.8, 6.0, 2.3, 0.5, "feedback", ["feedback_id (PK)", "user_id (FK)", "text"]),
        (8.3, 6.0, 2.5, 0.5, "savings_goals", ["goal_id (PK)", "user_id (FK)", "target"]),
        (5.8, 5.0, 2.3, 0.5, "atm_sessions", ["session_id (PK)", "user_id (FK)"]),
        (8.3, 5.0, 2.5, 0.5, "user_milestones", ["milestone_id (PK)", "user_id (FK)"]),
        (5.8, 4.0, 5.0, 0.5, "retrain_log", ["log_id (PK)", "model_name", "version",
                                                "triggered_by", "trained_at"]),
        (5.8, 3.2, 5.0, 0.5, "model_metrics", ["metric_id (PK)", "model_name", "version",
                                                  "metrics_summary (JSON)"]),
    ]
    for x, y, w, h, name, fields in tables_eco:
        color = C["teal"] if "user_id (FK)" in str(fields) else C["teal"]
        draw_box(ax, x, y, w, h, C["teal"], f"{name}", fontsize=6.5)
        for i, f in enumerate(fields[:5]):
            ax.text(x + 0.2, y - 0.2 - i * 0.2, f"  {f}", fontsize=5, color=C["gray"])

    # feature_store tables
    tables_fs = [
        (11.6, 8.8, 3.8, 0.5, "feature_definitions", ["feature_id (PK)", "feature_name",
                                                         "feature_set", "sql_expression"]),
        (11.6, 7.5, 3.8, 0.5, "feature_snapshots", ["snapshot_id (PK)", "feature_set",
                                                       "row_count", "snapshot_label"]),
        (11.6, 6.2, 3.8, 0.5, "training_datasets", ["dataset_id (PK)", "scenario",
                                                       "tables_exported", "file_paths"]),
        (11.6, 4.9, 3.8, 0.5, "model_registry", ["model_id (PK)", "model_name", "description"]),
        (11.6, 3.6, 3.8, 0.5, "model_versions", ["version_id (PK)", "model_id (FK)",
                                                    "version", "metrics", "is_production"]),
    ]
    for x, y, w, h, name, fields in tables_fs:
        draw_box(ax, x, y, w, h, C["purple"], f"{name}", fontsize=6.5)
        for i, f in enumerate(fields[:4]):
            ax.text(x + 0.2, y - 0.2 - i * 0.2, f"  {f}", fontsize=5, color=C["gray"])

    # Relationships
    # users -> transactions
    draw_arrow(ax, 8.3, 8.8, 8.3, 7.8, C["green"], lw=1)
    # users -> feedback
    draw_arrow(ax, 7.0, 8.8, 7.0, 6.5, C["green"], lw=1)
    # users -> savings_goals
    draw_arrow(ax, 9.5, 8.8, 9.5, 6.5, C["green"], lw=1)
    # users -> atm_sessions
    draw_arrow(ax, 7.0, 8.8, 7.0, 5.5, C["green"], lw=1)
    # bank_summary -> users (via bank name)
    draw_arrow(ax, 4.5, 7.0, 6.0, 8.8, C["amber"], lw=0.8, style="->")

    # Legend
    draw_legend(ax, [
        ("atm_data.db (RBI)", C["blue"]),
        ("ecosystem.db (Users)", C["teal"]),
        ("feature_store.db (Analytics)", C["purple"]),
        ("FK Relationships", C["green"]),
        ("Cross-DB Reference", C["amber"]),
    ], loc="lower center", ncol=5)

    path = OUTPUT / "01-database-erd.png"
    plt.savefig(path, bbox_inches="tight", facecolor=C["bg"])
    plt.close()
    print(f"Generated {path.name}")


# ======================================================================
# Diagram 3: ML Model Architecture
# ======================================================================
def generate_ml_architecture():
    fig, ax = plt.subplots(figsize=(18, 12))
    ax.set_xlim(0, 18)
    ax.set_ylim(0, 12)
    ax.set_facecolor(C["bg"])
    fig.patch.set_facecolor(C["bg"])
    ax.axis("off")

    draw_title(ax, "ML/DL Model Architecture — 20 Models", y=0.97, fontsize=16)

    # Data source boxes
    draw_box(ax, 0.5, 9.5, 4.0, 1.0, C["blue"],
             "atm_card_stats\n(RBI Transaction Data)", fontsize=8)
    draw_box(ax, 5.5, 9.5, 4.0, 1.0, C["teal"],
             "ecosystem.db — users\n(User Profiles)", fontsize=8)
    draw_box(ax, 10.5, 9.5, 4.0, 1.0, C["purple"],
             "ecosystem.db — transactions\n(Activity History)", fontsize=8)
    draw_box(ax, 15.5, 9.5, 2.0, 1.0, C["amber"],
             "bank_attrs\n(65 banks)", fontsize=8)

    # Phase 1 models row
    p1_y = 7.0
    models_p1 = [
        (0.3, p1_y, 2.8, 1.5, C["blue"],
         "CashDemand\nForecaster\nProphet\nMAE/RMSE/MAPE"),
        (3.3, p1_y, 2.8, 1.5, C["teal"],
         "Transaction\nPredictor\nXGBoost\nMAE/R2/RMSE"),
        (6.3, p1_y, 2.8, 1.5, C["purple"],
         "BankClustering\nK-Means + PCA\nSilhouette\nk=4 optimal"),
        (9.3, p1_y, 2.8, 1.5, C["amber"],
         "AnomalyDetector\nIsolation Forest\nContamination\nFlagged banks"),
        (12.3, p1_y, 2.8, 1.5, C["pink"],
         "TrendAnalyzer\nStatsModels\nSeasonal Decomp\nObs/Trend/Resid"),
        (15.3, p1_y, 2.5, 1.5, C["orange"],
         "ChannelMigration\nLinear/Prophet\nDigital Share\nN-month forecast"),
    ]
    for x, y, w, h, c, t in models_p1:
        draw_box(ax, x, y, w, h, c, t, fontsize=6)

    # More Phase 1 models
    p1b_y = 5.0
    models_p1b = [
        (0.3, p1b_y, 2.8, 1.5, C["green"],
         "WhatIfSimulator\nLinear Regression\nScenario changes\nImpact estimation"),
        (3.3, p1b_y, 2.8, 1.5, C["blue"],
         "CreditScorer\nGradient Boosting\nScore 300-900\nRule-based minors"),
        (6.3, p1b_y, 2.8, 1.5, C["teal"],
         "ChurnPredictor\nRandom Forest\nRisk H/M/L\nRecency features"),
        (9.3, p1b_y, 2.8, 1.5, C["purple"],
         "LoanDefaultModel\nRule-based scoring\nEligibility check\nAmort schedule"),
        (12.3, p1b_y, 2.8, 1.5, C["amber"],
         "BankRecommender\nWeighted scoring\nTop-5 banks\nExplanation"),
        (15.3, p1b_y, 2.5, 1.5, C["pink"],
         "LSTMForecaster\nTensorFlow LSTM\n2-layer 50 units\nFallback dummy"),
    ]
    for x, y, w, h, c, t in models_p1b:
        draw_box(ax, x, y, w, h, c, t, fontsize=6)

    # Phase 2 models
    p2_y = 3.0
    draw_box(ax, 0.3, p2_y, 4.0, 1.8, C["teal"],
             "PHASE 2 — Enhanced Models\n\n"
             "FraudDetector (Rule)\nInvestmentRecommender (Portfolio)\n"
             "ATMReplenishment (EOQ)\nRFMSegmenter (R/F/M)",
             fontsize=7)
    draw_box(ax, 5.0, p2_y, 4.0, 1.8, C["purple"],
             "PHASE 2 — Enhanced Models (cont.)\n\n"
             "SavingsGoalOptimizer (Financial)\n"
             "SentimentAnalyzer (VADER)\n"
             "ModelMonitor (Stats Tracking)",
             fontsize=7)
    draw_box(ax, 10.0, p2_y, 4.0, 1.8, C["amber"],
             "SUPPORT SYSTEMS\n\n"
             "AutoRetrainScheduler\n"
             "DataGenerator (10 export types)\n"
             "FeatureStore (21 features)\n"
             "ModelRegistry (Versioned)",
             fontsize=7)

    # Output / Metrics
    draw_box(ax, 0.3, 1.0, 17.0, 1.0, C["green"],
             "OUTPUTS:  Score 300-900  |  Risk H/M/L  |  Predicted Value  |  Cluster Labels  |  "
             "Anomaly Flags  |  Top-5 Recommendations  |  Amortization Schedule  |  Churn %",
             fontsize=7)

    # Data source arrows
    draw_arrow(ax, 2.5, 9.5, 2.5, 8.5, C["gray"])
    draw_arrow(ax, 7.5, 9.5, 7.5, 8.5, C["gray"])
    draw_arrow(ax, 12.5, 9.5, 12.5, 8.5, C["gray"])
    draw_arrow(ax, 16.5, 9.5, 16.5, 8.5, C["gray"])

    # Legend
    draw_legend(ax, [
        ("Prophet/XGBoost Models", C["blue"]),
        ("Tree/RF Models", C["teal"]),
        ("Clustering/Stats", C["purple"]),
        ("Rule-based", C["amber"]),
        ("Deep Learning", C["pink"]),
    ], loc="lower center", ncol=5)

    path = OUTPUT / "02-ml-architecture.png"
    plt.savefig(path, bbox_inches="tight", facecolor=C["bg"])
    plt.close()
    print(f"Generated {path.name}")


# ======================================================================
# Diagram 4: Data Pipeline
# ======================================================================
def generate_data_pipeline():
    fig, ax = plt.subplots(figsize=(16, 8))
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 8)
    ax.set_facecolor(C["bg"])
    fig.patch.set_facecolor(C["bg"])
    ax.axis("off")

    draw_title(ax, "End-to-End Data Pipeline Flow", y=0.95, fontsize=15)

    # Row 1: Input
    boxes_r1 = [
        (0.5, 6.0, 3.0, 1.2, C["blue"], "RBI CSV\n(data/raw/*.csv)\nMonthly bank stats"),
        (4.0, 6.0, 3.0, 1.2, C["teal"], "DataIngestion\nload_csv() → clean_data()\n→ save_to_sqlite()"),
        (7.5, 6.0, 3.0, 1.2, C["purple"], "atm_data.db\n3 tables\n(atm_card_stats /\nbank_summary / monthly_agg)"),
        (11.0, 6.0, 4.5, 1.2, C["amber"], "DatabaseManager (Singleton)\nAuto-reconnect | Query logging\nUnified connection source"),
    ]
    for x, y, w, h, c, t in boxes_r1:
        draw_box(ax, x, y, w, h, c, t, fontsize=7)

    # Row 1 arrows
    draw_arrow(ax, 3.5, 6.6, 4.0, 6.6, C["gray"])
    draw_arrow(ax, 7.0, 6.6, 7.5, 6.6, C["gray"])
    draw_arrow(ax, 10.5, 6.6, 11.0, 6.6, C["gray"])

    # Row 2: Processing
    boxes_r2 = [
        (0.5, 4.0, 3.0, 1.2, C["teal"], "DataAnalysis\nQuery Layer\nbank_overview / compare_banks\nmonthly_trend / market_share"),
        (4.0, 4.0, 3.0, 1.2, C["green"], "DataVisualization\n14 chart methods\nmatplotlib / seaborn\noutputs/charts/*.png"),
        (7.5, 4.0, 3.0, 1.2, C["purple"], "ML Models\n20 models\nBaseModel interface\ntrain() / predict()"),
        (11.0, 4.0, 4.5, 1.2, C["pink"], "User System\nUserManager / ATMSimulator\nRegistration / Login / KYC\nWithdraw / Deposit / Transfer"),
    ]
    for x, y, w, h, c, t in boxes_r2:
        draw_box(ax, x, y, w, h, c, t, fontsize=7)

    # Row 1 -> Row 2 arrows
    draw_arrow(ax, 2.0, 6.0, 2.0, 5.2, C["gray"])
    draw_arrow(ax, 5.5, 6.0, 5.5, 5.2, C["gray"])
    draw_arrow(ax, 9.0, 6.0, 9.0, 5.2, C["gray"])
    draw_arrow(ax, 13.5, 6.0, 13.5, 5.2, C["gray"])

    # Row 3: Output
    boxes_r3 = [
        (0.5, 2.0, 2.5, 1.2, C["blue"], "Charts PNG\n(matplotlib)\nInteractive (Plotly)"),
        (3.5, 2.0, 2.5, 1.2, C["teal"], "Reports PDF\n(fpdf2)\nGlobal + Portfolio"),
        (6.5, 2.0, 2.5, 1.2, C["purple"], "Passbook PNG/PDF\n(PyMuPDF)\nMulti-account"),
        (9.5, 2.0, 2.5, 1.2, C["amber"], "Training CSVs\n(DataGenerator)\n10 dataset types"),
        (12.5, 2.0, 3.0, 1.2, C["green"], "Web Dashboard\n(Flask / Plotly)\n5 pages"),
    ]
    for x, y, w, h, c, t in boxes_r3:
        draw_box(ax, x, y, w, h, c, t, fontsize=7)

    # Row 2 -> Row 3 arrows
    draw_arrow(ax, 2.0, 4.0, 2.0, 3.2, C["gray"])
    draw_arrow(ax, 5.5, 4.0, 5.5, 3.2, C["gray"])
    draw_arrow(ax, 9.0, 4.0, 9.0, 3.2, C["gray"])
    draw_arrow(ax, 13.5, 4.0, 13.5, 3.2, C["gray"])

    # Legend
    draw_legend(ax, [
        ("Input Layer", C["blue"]), ("Processing", C["teal"]),
        ("Data Storage", C["purple"]), ("User System", C["pink"]),
        ("Output Layer", C["green"]),
    ], loc="lower center", ncol=5)

    path = OUTPUT / "03-data-pipeline.png"
    plt.savefig(path, bbox_inches="tight", facecolor=C["bg"])
    plt.close()
    print(f"Generated {path.name}")


# ======================================================================
# Diagram 5: CLI Menu Structure
# ======================================================================
def generate_menu_structure():
    fig, ax = plt.subplots(figsize=(16, 14))
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 14)
    ax.set_facecolor(C["bg"])
    fig.patch.set_facecolor(C["bg"])
    ax.axis("off")

    draw_title(ax, "CLI Menu Navigation Map", y=0.97, fontsize=15)

    # Main menu (center)
    draw_box(ax, 5.5, 11.5, 5.0, 1.8, C["blue"],
             "MAIN MENU\n[1] ATM  [2] Data  [3] ML  [4] Profile\n"
             "[5] Banks  [6] Web  [7] Reports  [8] Demo\n"
             "[9] Retrain  [10] Settings  [11] Exit",
             fontsize=7)

    # Sub-menus (top row)
    submenus_top = [
        (0.2, 9.0, 3.0, 2.0, C["teal"],
         "1. ATM SIMULATOR\n- Balance Inquiry\n- Cash Withdraw\n- Cash Deposit\n"
         "- Fund Transfer\n- Mini Statement\n- Change PIN\n- Savings Goals\n- Loan Offers"),
        (3.6, 9.0, 3.0, 2.0, C["purple"],
         "2. DATA ANALYSIS\n- Bank Overview\n- Compare Banks\n- Monthly Trend\n"
         "- Market Share\n- Channel Breakdown\n- Correlation\n- Growth Rate\n- Personal"),
        (7.0, 9.0, 3.0, 2.0, C["amber"],
         "3. ML/DL MODELS\n- Forecast (Prophet)\n- Txn Predict (XGB)\n- Clustering\n"
         "- Anomaly Detection\n- Trend Decompose\n- Channel Migration\n- What-If\n- Credit/Churn"),
        (10.4, 9.0, 3.0, 2.0, C["pink"],
         "3. ML (cont.)\n- Loan Default\n- Bank Recommend\n- Retrain All\n- Replenish\n"
         "- LSTM vs Prophet\n- Demo Walkthrough"),
        (13.7, 9.0, 2.0, 2.0, C["orange"],
         "4. PROFILE\n- Dashboard\n- Spending\n- Credit Score\n- Transactions\n"
         "- Loan Offers\n- Savings Goals\n- Investments\n- RFM\n- Passbook"),
    ]
    for x, y, w, h, c, t in submenus_top:
        draw_box(ax, x, y, w, h, c, t, fontsize=6)

    # Sub-menus (bottom row)
    submenus_bottom = [
        (0.2, 6.0, 3.0, 2.2, C["green"],
         "5. BANK EXPLORER\n- Browse 65 Banks\n- Compare Banks\n- Bank Attributes\n"
         "- Best Bank For Me\n- Random Bank\n- Your Bank vs Industry"),
        (3.6, 6.0, 3.0, 2.2, C["blue"],
         "6. WEB DASHBOARD\nLaunches Flask app\nhttp://127.0.0.1:5000\n"
         "5 pages in browser\nThreaded (CLI stays up)"),
        (7.0, 6.0, 3.0, 2.2, C["teal"],
         "7. REPORTS\n- PDF Report (Global)\n- Portfolio Report\n- Export CSV\n"
         "- Export Excel\n- Save All Charts\n- Dataset Summary\n- Training Data"),
        (10.4, 6.0, 3.0, 2.2, C["purple"],
         "8. DEMO / TOUR\n- Analysis Walkthrough\n- ML Explained\n"
         "- ATM Sim Demo\n- Profile Tour\n- Explorer Guide"),
        (13.7, 6.0, 2.0, 2.2, C["amber"],
         "9. FRESHNESS\n10. SETTINGS\n- Refresh Data\n- DB Stats\n- Reset ATM\n"
         "- Export Training\n- Dataset Info\n- Sentiment"),
    ]
    for x, y, w, h, c, t in submenus_bottom:
        draw_box(ax, x, y, w, h, c, t, fontsize=6)

    # Entry point
    draw_box(ax, 6.5, 13.0, 3.0, 0.6, C["accent"], "ENTRY POINT:  run.py  →  BankingAnalyticsSuite", fontsize=8)

    # Arrows from main menu to sub-menus
    main_center = 8.0
    for x_pos in [1.7, 5.1, 8.5, 11.9, 14.7]:
        draw_arrow(ax, main_center, 11.5, x_pos, 11.0, C["gray"])
        draw_arrow(ax, x_pos, 11.0, x_pos, 8.2, C["gray"])

    # Legend
    draw_legend(ax, [
        ("Main Menu", C["blue"]), ("ATM / Data / ML", C["teal"]),
        ("Profile / Banks", C["purple"]), ("Web / Reports", C["amber"]),
        ("Demo / Settings", C["green"]),
    ], loc="lower center", ncol=5)

    path = OUTPUT / "04-cli-menu-structure.png"
    plt.savefig(path, bbox_inches="tight", facecolor=C["bg"])
    plt.close()
    print(f"Generated {path.name}")


# ======================================================================
# Diagram 6: User System Flow
# ======================================================================
def generate_user_system_flow():
    fig, ax = plt.subplots(figsize=(16, 10))
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 10)
    ax.set_facecolor(C["bg"])
    fig.patch.set_facecolor(C["bg"])
    ax.axis("off")

    draw_title(ax, "User System — Registration, Auth & Passbook Flow", y=0.97, fontsize=15)

    # Login/Register gate
    draw_box(ax, 5.5, 8.0, 5.0, 1.2, C["blue"],
             "LOGIN / REGISTER GATE\nUserManager.login_or_register()\n"
             "[L] Login  [R] Register  [F] Forgot Card  [P] Forgot PIN",
             fontsize=7)

    # Registration flow
    draw_box(ax, 0.3, 5.5, 3.5, 1.8, C["teal"],
             "REGISTER\n1. Enter name, age, phone,\n   email, bank, income\n"
             "2. Validate all fields\n3. Age check: Adult vs Minor\n"
             "4. If minor: require guardian\n   (name, phone, relation)\n"
             "5. Generate account_no, card_no,\n   PIN, credit_score",
             fontsize=6.5)

    # Login flow
    draw_box(ax, 4.2, 5.5, 3.5, 1.8, C["purple"],
             "LOGIN\n1. Enter user_id\n2. Enter PIN\n"
             "3. Verify credentials\n4. Load user data\n"
             "5. Start session\n6. Main menu",
             fontsize=6.5)

    # Recovery flow
    draw_box(ax, 8.1, 5.5, 3.5, 1.8, C["amber"],
             "FORGOT CARD / PIN\n[Forgot Card]\n1. Enter phone + email\n"
             "2. Verify identity\n3. Display card number\n\n"
             "[Forgot PIN]\n1. Enter user_id + code\n"
             "2. Verify recovery code\n3. Reset to new PIN",
             fontsize=6.5)

    # Passbook flow
    draw_box(ax, 12.0, 5.5, 3.5, 1.8, C["pink"],
             "PASSBOOK GENERATION\nProfile Menu → Option 10\n\n"
             "1. Find linked accounts\n   (same name/phone/email)\n"
             "2. Choose format:\n   PNG (<=20 txns)\n   PDF (>20 txns)\n"
             "3. Overwrite single file\n4. Prompt to open",
             fontsize=6.5)

    # Account types
    draw_box(ax, 1.5, 3.0, 5.0, 1.5, C["green"],
             "ACCOUNT TYPES\n\n"
             "Adult (18+)          Minor (<18)\n"
             "Full access         Limited features\n"
             "Credit 650-780      Credit max 600\n"
             "Loan eligible       Not loan eligible\n"
             "Standard KYC        Guardian KYC required",
             fontsize=7)

    # Transaction types
    draw_box(ax, 7.5, 3.0, 5.0, 1.5, C["orange"],
             "TRANSACTION TYPES\n\n"
             "Withdraw (-bal)    Deposit (+bal)     Transfer (-bal)\n"
             "Fee (-bal)          Credit (+bal)     Payment (-bal)\n\n"
             "Daily ATM Limit: Rs 50,000\n"
             "Fraud detection on every transaction",
             fontsize=7)

    # Security
    draw_box(ax, 13.5, 3.0, 2.0, 1.5, C["accent"],
             "SECURITY\n3 PIN attempts\nFraud scoring\nSession logging\nRecovery codes",
             fontsize=6.5)

    # Arrows
    draw_arrow(ax, 8.0, 8.0, 8.0, 7.3, C["gray"])
    draw_arrow(ax, 2.0, 8.0, 2.0, 7.3, C["gray"])
    draw_arrow(ax, 6.0, 8.0, 6.0, 7.3, C["gray"])
    draw_arrow(ax, 10.0, 8.0, 10.0, 7.3, C["gray"])
    draw_arrow(ax, 14.0, 8.0, 14.0, 7.3, C["gray"])

    # Legend
    draw_legend(ax, [
        ("Auth Gate", C["blue"]), ("Registration", C["teal"]),
        ("Login", C["purple"]), ("Recovery", C["amber"]),
        ("Passbook", C["pink"]), ("Security", C["accent"]),
    ], loc="lower center", ncol=6)

    path = OUTPUT / "05-user-system-flow.png"
    plt.savefig(path, bbox_inches="tight", facecolor=C["bg"])
    plt.close()
    print(f"Generated {path.name}")


# ======================================================================
# Run all
# ======================================================================
def generate_all():
    print("Generating architecture diagrams...")
    generate_system_architecture()
    generate_database_erd()
    generate_ml_architecture()
    generate_data_pipeline()
    generate_menu_structure()
    generate_user_system_flow()
    print(f"\nAll diagrams saved to {OUTPUT}/")


if __name__ == "__main__":
    generate_all()
