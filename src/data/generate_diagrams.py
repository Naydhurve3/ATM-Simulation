import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np
from pathlib import Path
from src.utils import OUTPUTS_CHARTS


def create_architecture_overview():
    fig, ax = plt.subplots(1, 1, figsize=(20, 14))
    ax.set_xlim(0, 20)
    ax.set_ylim(0, 26)
    ax.axis("off")
    ax.set_facecolor("#1a1a2e")
    fig.patch.set_facecolor("#1a1a2e")
    colors = {
        "layer1": {"bg": "#16213e", "border": "#0f3460", "text": "#e0e0e0", "header": "#e94560"},
        "layer2": {"bg": "#1a1a2e", "border": "#0f3460", "text": "#e0e0e0", "header": "#0f3460"},
        "layer3": {"bg": "#0f3460", "border": "#16213e", "text": "#e0e0e0", "header": "#533483"},
        "access": {"bg": "#2d2d44", "border": "#533483", "text": "#e0e0e0", "header": "#e94560"},
        "model": {"bg": "#3a3a5c", "border": "#533483", "text": "#cccccc"},
        "db": {"bg": "#1a3a4a", "border": "#0f3460", "text": "#88ccff"},
    }

    def draw_layer(ax, x, y, w, h, label, color_key, alpha=0.9):
        rect = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.3",
                              facecolor=colors[color_key]["bg"],
                              edgecolor=colors[color_key]["border"],
                              linewidth=2, alpha=alpha)
        ax.add_patch(rect)
        ax.text(x + w / 2, y + h - 0.4, label,
                ha="center", va="top", fontsize=11, fontweight="bold",
                color=colors[color_key]["header"],
                family="monospace")
        return rect

    def draw_box(ax, x, y, w, h, text, color_key="model", fontsize=8, subtext=None):
        rect = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.1",
                              facecolor=colors[color_key]["bg"],
                              edgecolor=colors[color_key]["border"],
                              linewidth=1.2)
        ax.add_patch(rect)
        ax.text(x + w / 2, y + h / 2 + (0.08 if subtext else 0), text,
                ha="center", va="center", fontsize=fontsize,
                color=colors[color_key]["text"], fontweight="bold",
                family="monospace")
        if subtext:
            ax.text(x + w / 2, y + h / 2 - 0.2, subtext,
                    ha="center", va="center", fontsize=6,
                    color="#999999", family="monospace")

    def draw_db(ax, x, y, w, h, text, color_key="db", fontsize=8):
        rect = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.1",
                              facecolor=colors[color_key]["bg"],
                              edgecolor="#4a9eff", linewidth=1.5,
                              linestyle="--")
        ax.add_patch(rect)
        ax.text(x + w / 2, y + h / 2, text,
                ha="center", va="center", fontsize=fontsize,
                color=colors[color_key]["text"], fontweight="bold",
                family="monospace")

    def draw_arrow(ax, x1, y1, x2, y2, color="#e94560", style="-", label=""):
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="->", color=color,
                                    linestyle=style, lw=1.5,
                                    connectionstyle="arc3,rad=0.2"))
        if label:
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            ax.text(mx + 0.3, my, label, fontsize=6, color="#aaaaaa",
                    family="monospace", ha="center")

    # === LAYER 1: RAW / INGESTION ===
    l1_y = 22.5
    l1_h = 3.0
    draw_layer(ax, 0.5, l1_y, 19, l1_h, "LAYER 1: RAW DATA INGESTION", "layer1")
    draw_box(ax, 1.0, l1_y + 0.3, 3.5, 0.9, "data/raw/\nRBI_ATM_Stats.csv", "db", 7)
    draw_box(ax, 5.5, l1_y + 0.3, 3.0, 0.9, "DataIngestion\n(clean + agg)", "model", 7)
    draw_db(ax, 9.5, l1_y + 0.3, 3.0, 0.9, "atm_data.db\natm_card_stats\nbank_summary", "db", 6)
    draw_box(ax, 13.5, l1_y + 0.3, 2.5, 0.9, "FeatureEng\n(lag/roll/ratio)", "model", 7)
    draw_db(ax, 17.0, l1_y + 0.3, 2.0, 0.9, "features\n_data.csv", "db", 7)
    draw_arrow(ax, 4.5, l1_y + 0.75, 5.5, l1_y + 0.75, "#4a9eff")
    draw_arrow(ax, 8.5, l1_y + 0.75, 9.5, l1_y + 0.75, "#4a9eff")
    draw_arrow(ax, 12.5, l1_y + 0.75, 13.5, l1_y + 0.75, "#4a9eff")

    # === LAYER 2: OPERATIONAL ===
    l2_y = 13.0
    l2_h = 8.5
    draw_layer(ax, 0.5, l2_y, 19, l2_h, "LAYER 2: OPERATIONAL DATABASE (OLTP)", "layer2")

    draw_db(ax, 1.0, l2_y + 0.8, 3.5, 7.0,
            "ecosystem.db\n\nusers\ntransactions\nloan_applications\nfraud_flags\ncredit_history\nuser_sessions\nsavings_goals\nfeedback\n[data_catalog]\n[export_log]",
            "db", 6.5)

    draw_box(ax, 5.5, l2_y + 0.8, 2.8, 1.2, "UserManager\n(reg/login/\nrecovery)", "model", 7)
    draw_box(ax, 5.5, l2_y + 2.2, 2.8, 1.2, "ATMSimulator\n(withdraw/\ndeposit/loan)", "model", 7)
    draw_box(ax, 5.5, l2_y + 3.6, 2.8, 1.2, "RealTimeFraud\nDetector\n(per-txn score)", "model", 7)
    draw_box(ax, 5.5, l2_y + 5.0, 2.8, 1.2, "UserAnalytics\n(spending/credit\n/savings)", "model", 7)
    draw_box(ax, 5.5, l2_y + 6.4, 2.8, 1.2, "ReportGenerator\n(PDF/CSV/Excel)", "model", 7)

    draw_box(ax, 9.5, l2_y + 0.8, 2.8, 1.2, "DataGenerator\n(8 scenarios)\n10 train CSVs", "model", 7)
    draw_box(ax, 9.5, l2_y + 2.2, 2.8, 1.2, "AutoRetrain\n(threshold\nchecker)", "model", 7)
    draw_box(ax, 9.5, l2_y + 3.6, 2.8, 1.2, "DemoManager\n(12 features\nper-page)", "model", 7)
    draw_box(ax, 9.5, l2_y + 5.0, 2.8, 1.2, "BankSelector\n(fuzzy match\npaginated)", "model", 7)

    draw_box(ax, 13.5, l2_y + 0.8, 2.8, 1.2, "DataAnalysis\n(RBI queries,\nuser vs ind)", "model", 7)
    draw_box(ax, 13.5, l2_y + 2.2, 2.8, 1.2, "DataViz\n(22 charts,\nauto-open)", "model", 7)
    draw_box(ax, 13.5, l2_y + 3.6, 2.8, 1.2, "Dashboard\n(Flask+Plotly\nweb UI)", "model", 7)

    draw_db(ax, 17.5, l2_y + 0.8, 1.8, 1.5,
            "outputs/\ntraining_data/\n(CSVs)", "db", 6.5)
    draw_db(ax, 17.5, l2_y + 3.0, 1.8, 1.5,
            "outputs/\ncharts/\nreports/", "db", 6.5)

    # === LAYER 3: ANALYTICS / ML ===
    l3_y = 6.5
    l3_h = 5.5
    draw_layer(ax, 0.5, l3_y, 19, l3_h, "LAYER 3: ANALYTICS / ML ENGINE (OLAP)", "layer3")

    atm_models = ["CashDemand\nForecaster", "Anomaly\nDetector", "Channel\nMigration", "Transaction\nPredictor", "Bank\nClustering", "WhatIf\nSimulator", "LSTM\nForecaster"]
    eco_models = ["Credit\nScorer", "Churn\nPredictor", "Loan\nDefault", "Bank\nRecommender", "Spending\nForecaster"]
    both_models = ["Investment\nRecommender", "RFM\nSegmenter", "Savings\nOptimizer", "Sentiment\nAnalyzer", "Fraud\nDetector", "Model\nExplainer"]

    x_start = 1.0
    for i, m in enumerate(atm_models):
        col = i % 3
        row = i // 3
        draw_box(ax, x_start + col * 2.2, l3_y + 0.3 + row * 1.6, 2.0, 1.2, m, "model", 6.5, "reads: atm_data.db")

    x_start2 = 7.8
    for i, m in enumerate(eco_models):
        col = i % 3
        row = i // 3
        draw_box(ax, x_start2 + col * 2.2, l3_y + 0.3 + row * 1.6, 2.0, 1.2, m, "model", 6.5, "reads: ecosystem.db")

    x_start3 = 14.6
    for i, m in enumerate(both_models):
        col = i % 2
        row = i // 2
        draw_box(ax, x_start3 + col * 2.2, l3_y + 0.3 + row * 1.6, 2.0, 1.2, m, "model", 6.5, "rule-based/plugins")

    draw_db(ax, 17.5, l3_y + 3.6, 1.8, 1.5,
            "data/models/\n*.pkl / .keras", "db", 6.5)

    # === ACCESS LAYER ===
    ac_y = 3.2
    ac_h = 2.5
    draw_layer(ax, 0.5, ac_y, 19, ac_h, "ACCESS LAYER: DATA PLATFORM (NEW)", "access")

    draw_box(ax, 1.0, ac_y + 0.5, 4.0, 1.2, "DatabaseManager\n(unified connections, query logging)", "access", 8)
    draw_box(ax, 6.0, ac_y + 0.5, 4.0, 1.2, "FeatureStore\n(materialized features, snapshots)", "access", 8)
    draw_box(ax, 11.0, ac_y + 0.5, 4.0, 1.2, "ModelRegistry\n(version tracking, A/B compare)", "access", 8)
    draw_box(ax, 16.0, ac_y + 0.5, 3.0, 1.2, "DataCatalog\n(schema, lineage)", "access", 8)

    # === LEGEND ===
    leg_y = 0.3
    leg_h = 2.2
    draw_layer(ax, 0.5, leg_y, 19, leg_h, "DATA FLOW LEGEND", "layer1", 0.7)
    legend_text = (
        "Arrows  =  Data flow direction      [DB] Cylinders  =  Databases / Storage      [Boxes]  =  Application Components\n"
        "Layer 1 = Raw RBI CSV ingestion pipeline         Layer 2 = User/transaction operational system (OLTP)\n"
        "Layer 3 = ML model training & inference (OLAP)   Access Layer = New unified data platform (db, features, registry, catalog)"
    )
    ax.text(10, leg_y + 0.3, legend_text, ha="center", va="top",
            fontsize=8, color="#cccccc", family="monospace")

    plt.tight_layout()
    path = OUTPUTS_CHARTS / "architecture_overview.png"
    plt.savefig(str(path), dpi=200, bbox_inches="tight")
    plt.close()
    print(f"[green]Architecture overview saved: {path}[/green]")
    return path


def create_data_flow_diagram():
    fig, ax = plt.subplots(1, 1, figsize=(18, 16))
    ax.set_xlim(0, 18)
    ax.set_ylim(0, 30)
    ax.axis("off")
    ax.set_facecolor("#1a1a2e")
    fig.patch.set_facecolor("#1a1a2e")

    colors = {
        "db": {"bg": "#0a1628", "border": "#2a6f9c"},
        "process": {"bg": "#16213e", "border": "#0f3460"},
        "user": {"bg": "#1a3a2e", "border": "#2a8c6f"},
        "ml": {"bg": "#2d1b3a", "border": "#7a3b8c"},
        "web": {"bg": "#3a2a1a", "border": "#8c6f2a"},
        "new": {"bg": "#2a1a3a", "border": "#6f3a8c"},
    }

    def node(ax, x, y, w, h, text, color_key="process", fontsize=8, sub=None, edgecolor=None):
        ec = edgecolor or colors[color_key]["border"]
        rect = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.15",
                              facecolor=colors[color_key]["bg"],
                              edgecolor=ec, linewidth=1.5)
        ax.add_patch(rect)
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
                fontsize=fontsize, color="#e0e0e0", fontweight="bold", family="monospace")

    def arrow(ax, x1, y1, x2, y2, label="", color="#4a9eff", style="-"):
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="->", color=color,
                                    linestyle=style, lw=1.5,
                                    connectionstyle="arc3,rad=0.15"))
        if label:
            ax.text((x1 + x2) / 2, (y1 + y2) / 2 + 0.2, label,
                    fontsize=6, color="#88aacc", ha="center", family="monospace")

    # Title
    ax.text(9, 29.5, "DATA FLOW: FULL USER JOURNEY", ha="center", va="center",
            fontsize=14, fontweight="bold", color="#e94560", family="monospace")

    # Row 1: User Registration flow
    node(ax, 1, 26, 3, 1.2, "USER\nRegistration", "user", 8)
    node(ax, 5, 26, 3, 1.2, "UserManager\n(validate/KYC)", "process", 7)
    node(ax, 9, 26, 2.5, 1.2, "ecosystem.db\nusers table", "db", 7)
    node(ax, 12.5, 26, 2.5, 1.2, "DataGenerator\n(NEW_USER)", "process", 7)
    node(ax, 16, 26, 1.5, 1.2, "train CSV", "db", 7)
    arrow(ax, 4, 26.6, 5, 26.6, "name/phone/email/age")
    arrow(ax, 8, 26.6, 9, 26.6, "INSERT user")
    arrow(ax, 11.5, 26.6, 12.5, 26.6, "trigger check")
    arrow(ax, 15, 26.6, 16, 26.6, "export csv")

    # Row 2: Login flow
    node(ax, 1, 23.5, 3, 1.2, "LOGIN\n(card/email/\nphone/account)", "user", 7)
    node(ax, 5, 23.5, 3, 1.2, "UserManager\n(lookup+verify)", "process", 7)
    node(ax, 9, 23.5, 2.5, 1.2, "ecosystem.db\nusers table", "db", 7)
    node(ax, 12.5, 23.5, 2.5, 1.2, "Session\nLogger", "process", 7)
    node(ax, 16, 23.5, 1.5, 1.2, "user_sessions", "db", 7)
    arrow(ax, 4, 24.0, 5, 24.0, "credentials")
    arrow(ax, 8, 24.0, 9, 24.0, "SELECT user")
    arrow(ax, 11.5, 24.0, 12.5, 24.0, "verify PIN")
    arrow(ax, 15, 24.0, 16, 24.0, "INSERT session")

    # Row 3: ATM Transaction flow
    node(ax, 1, 21, 3, 1.2, "ATM Transaction\n(withdraw/\ndeposit)", "user", 7)
    node(ax, 5, 21, 3, 1.2, "ATMSimulator\n(limits/fees/\nnotes)", "process", 7)
    node(ax, 9, 21, 2.5, 1.2, "ecosystem.db\ntransactions", "db", 7)
    node(ax, 12.5, 21, 2.5, 1.2, "RealTimeFraud\nDetector", "ml", 7)
    node(ax, 16, 21, 1.5, 1.2, "fraud_flags", "db", 7)
    arrow(ax, 4, 21.6, 5, 21.6, "amount + type")
    arrow(ax, 8, 21.6, 9, 21.6, "INSERT txn")
    arrow(ax, 9, 20.4, 12.5, 20.4, "score txn")
    arrow(ax, 15, 20.4, 16, 20.4, "flag if >0.6")

    # Row 4: Loan flow
    node(ax, 1, 18.5, 3, 1.2, "Loan\nApplication", "user", 8)
    node(ax, 5, 18.5, 3, 1.2, "LoanDefault\nModel\n(risk score)", "ml", 7)
    node(ax, 9, 18.5, 2.5, 1.2, "ecosystem.db\nloan_applications", "db", 7)
    node(ax, 12.5, 18.5, 2.5, 1.2, "Amortization\nSchedule\nCalc", "process", 7)
    arrow(ax, 4, 19.1, 5, 19.1, "loan details")
    arrow(ax, 8, 19.1, 9, 19.1, "INSERT")
    arrow(ax, 11.5, 18.5, 12.5, 18.5, "EMI/interest")

    # Row 5: ML Training flow
    node(ax, 1, 15.5, 3, 1.2, "MODEL\nTRAINING\n(manual/auto)", "ml", 7)
    node(ax, 5, 15.5, 3, 1.2, "FeatureStore\n(compute user/\nbank/loan feats)", "new", 7, edgecolor="#6f3a8c")
    node(ax, 9, 15.5, 2.5, 1.2, "feature_store.db\n(snapshot_id)", "db", 7, edgecolor="#6f3a8c")
    node(ax, 12.5, 15.5, 2.5, 1.2, "ModelRegistry\n(log version +\nmetrics)", "new", 7, edgecolor="#6f3a8c")
    node(ax, 16, 15.5, 1.5, 1.2, "data/models/\n*.pkl", "db", 7)
    arrow(ax, 4, 16.1, 5, 16.1, "train() call")
    arrow(ax, 8, 16.1, 9, 16.1, "save snapshot")
    arrow(ax, 11.5, 16.1, 12.5, 16.1, "log training")
    arrow(ax, 15, 16.1, 16, 16.1, "save binary")

    # Row 6: Dashboard
    node(ax, 1, 12.5, 3, 1.2, "WEB\nDASHBOARD\n(menu opt 6)", "web", 7)
    node(ax, 5, 12.5, 3, 1.2, "Flask App\n(app.py + routes)", "web", 7)
    node(ax, 9, 12.5, 2.5, 1.2, "ecosystem.db\n+ atm_data.db", "db", 7)
    node(ax, 12.5, 12.5, 2.5, 1.2, "Plotly Charts\n(5 pages)", "web", 7)
    arrow(ax, 4, 13.1, 5, 13.1, "user clicks")
    arrow(ax, 8, 13.1, 9, 13.1, "query data")
    arrow(ax, 11.5, 12.5, 12.5, 12.5, "render plots")

    # Row 7: Auto Retrain
    node(ax, 1, 10, 3, 1.2, "AUTO-RETRAIN\nSCHEDULER", "ml", 7)
    node(ax, 5, 10, 3, 1.2, "Check Triggers\n(50 txns / 5 users\n/ 7 days)", "process", 7)
    node(ax, 9, 10, 2.5, 1.2, "ecosystem.db\ncounters + log", "db", 7)
    node(ax, 12.5, 10, 2.5, 1.2, "Retrain models\n→ ModelRegistry", "ml", 7)
    arrow(ax, 4, 10.6, 5, 10.6, "check()")
    arrow(ax, 8, 10.6, 9, 10.6, "count txns/users")
    arrow(ax, 11.5, 10, 12.5, 10, "trigger retrain")

    # Row 8: Export Lineage
    node(ax, 1, 7.5, 3, 1.2, "EXPORT\nLINEAGE\n(NEW)", "new", 7, edgecolor="#6f3a8c")
    node(ax, 5, 7.5, 3, 1.2, "DataCatalog\n(record schema,\nlog export)", "new", 7, edgecolor="#6f3a8c")
    node(ax, 9, 7.5, 2.5, 1.2, "feature_store.db\nexport_log +\ndata_catalog", "db", 7, edgecolor="#6f3a8c")
    node(ax, 12.5, 7.5, 2.5, 1.2, "Lineage Query\n(model→snapshot\n→export→schema)", "new", 7, edgecolor="#6f3a8c")
    arrow(ax, 4, 8.1, 5, 8.1, "on every export")
    arrow(ax, 8, 8.1, 9, 8.1, "INSERT log")
    arrow(ax, 11.5, 8.1, 12.5, 8.1, "trace full path")

    # Legend
    legend_y = 4.5
    ax.text(9, legend_y + 1.5, "COLOR LEGEND", ha="center", fontsize=11,
            fontweight="bold", color="#e94560", family="monospace")
    legends = [
        ("#0a1628", "Database / Storage"),
        ("#16213e", "Application Process"),
        ("#1a3a2e", "User Interaction"),
        ("#2d1b3a", "ML Model"),
        ("#3a2a1a", "Web / Dashboard"),
        ("#2a1a3a", "NEW Data Platform"),
    ]
    for i, (color, label) in enumerate(legends):
        ax.add_patch(plt.Rectangle((2 + i * 2.5, legend_y - 0.3), 0.5, 0.5,
                                    facecolor=color, edgecolor="#555", linewidth=1))
        ax.text(2.6 + i * 2.5, legend_y, label, fontsize=7, color="#ccc",
                va="center", family="monospace")

    plt.tight_layout()
    path = OUTPUTS_CHARTS / "data_flow_diagram.png"
    plt.savefig(str(path), dpi=200, bbox_inches="tight")
    plt.close()
    print(f"[green]Data flow diagram saved: {path}[/green]")
    return path


def create_schema_diagram():
    import sqlite3
    from src.utils import DB_PATH, ECOSYSTEM_DB

    fig, axes = plt.subplots(2, 2, figsize=(20, 14))
    fig.patch.set_facecolor("#1a1a2e")

    db_infos = [
        ("atm_data.db — RBI Statistics", DB_PATH, axes[0, 0]),
        ("ecosystem.db — User Operations", ECOSYSTEM_DB, axes[0, 1]),
        ("[NEW] feature_store.db — Analytics/ML", None, axes[1, 0]),
        ("[NEW] Database Manager — Singleton", None, axes[1, 1]),
    ]

    for ax, (title, db_path, _) in zip([axes[0, 0], axes[0, 1], axes[1, 0], axes[1, 1]], db_infos):
        ax.set_facecolor("#16213e")
        ax.set_title(title, color="#e94560", fontsize=10, fontweight="bold", family="monospace")
        ax.axis("off")

    # atm_data.db schema
    ax = axes[0, 0]
    try:
        conn = sqlite3.connect(str(DB_PATH))
        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = c.fetchall()
        y = 0.95
        for t in tables:
            tname = t[0]
            c.execute(f"PRAGMA table_info({tname})")
            cols = c.fetchall()
            c.execute(f"SELECT COUNT(*) FROM {tname}")
            cnt = c.fetchone()[0]
            ax.text(0.02, y, f"[ {tname} ]  ({cnt} rows)", fontsize=8, color="#4a9eff",
                    fontweight="bold", family="monospace", transform=ax.transAxes)
            y -= 0.06
            for col in cols[:6]:
                col_name, col_type = col[1], col[2]
                marker = "*PK" if col[5] else "   "
                ax.text(0.04, y, f"{marker} {col_name} ({col_type})",
                        fontsize=6, color="#cccccc", family="monospace", transform=ax.transAxes)
                y -= 0.04
            if len(cols) > 6:
                ax.text(0.04, y, f"  ... +{len(cols)-6} more cols",
                        fontsize=6, color="#888888", family="monospace", transform=ax.transAxes)
                y -= 0.04
            y -= 0.03
        conn.close()
    except Exception as e:
        ax.text(0.5, 0.5, f"Error: {e}", color="red", ha="center", va="center",
                transform=ax.transAxes, fontsize=8, family="monospace")

    # ecosystem.db schema
    ax = axes[0, 1]
    try:
        conn = sqlite3.connect(str(ECOSYSTEM_DB))
        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = c.fetchall()
        y = 0.95
        for t in tables:
            tname = t[0]
            c.execute(f"PRAGMA table_info({tname})")
            cols = c.fetchall()
            c.execute(f"SELECT COUNT(*) FROM {tname}")
            cnt = c.fetchone()[0]
            ax.text(0.02, y, f"[ {tname} ]  ({cnt} rows)", fontsize=8, color="#4a9eff",
                    fontweight="bold", family="monospace", transform=ax.transAxes)
            y -= 0.06
            for col in cols[:8]:
                col_name, col_type = col[1], col[2]
                marker = "*PK" if col[5] else "   "
                ax.text(0.04, y, f"{marker} {col_name} ({col_type})",
                        fontsize=6, color="#cccccc", family="monospace", transform=ax.transAxes)
                y -= 0.04
            if len(cols) > 8:
                ax.text(0.04, y, f"  ... +{len(cols)-8} more cols",
                        fontsize=6, color="#888888", family="monospace", transform=ax.transAxes)
                y -= 0.04
            y -= 0.03
        conn.close()
    except Exception as e:
        ax.text(0.5, 0.5, f"Error: {e}", color="red", ha="center", va="center",
                transform=ax.transAxes, fontsize=8, family="monospace")

    # feature_store.db schema
    ax = axes[1, 0]
    tables_info = [
        ("feature_definitions", "feature_id, feature_name, feature_set, description, sql_expression, data_type, created_at"),
        ("feature_snapshots", "snapshot_id, feature_set, snapshot_label, row_count, created_at"),
        ("training_datasets", "dataset_id, scenario, export_timestamp, tables_exported, row_counts, file_paths, schema_snapshot, created_at"),
        ("model_registry", "model_id, model_name, description, created_at"),
        ("model_versions", "version_id, model_id(FK), version, hyperparameters(JSON), metrics(JSON), training_dataset_id(FK), feature_snapshot_id(FK), model_path, training_duration_ms, is_production, trained_at"),
        ("production_log", "log_id, model_name, version, promoted_at, notes"),
        ("query_log", "log_id, db_name, query_hash, duration_ms, queried_at"),
        ("data_catalog", "catalog_id, db_name, table_name, schema_json(JSON), row_count, recorded_at"),
        ("export_log", "export_id, scenario, dataset_type, file_path, row_count, checksum, schema_snapshot(JSON), created_at"),
    ]
    y = 0.95
    for tname, cols in tables_info:
        ax.text(0.02, y, f"[ {tname} ]", fontsize=7, color="#6f3a8c",
                fontweight="bold", family="monospace", transform=ax.transAxes)
        y -= 0.05
        ax.text(0.04, y, cols, fontsize=5.5, color="#cccccc",
                family="monospace", transform=ax.transAxes)
        y -= 0.06

    # Database Manager singleton
    ax = axes[1, 1]
    dm_text = (
        "DatabaseManager (Singleton)\n"
        "═══════════════════════════\n\n"
        "Registered Databases:\n"
        "  • atm_data.db       (READ)\n"
        "  • ecosystem.db      (READ/WRITE)\n"
        "  • feature_store.db  (READ/WRITE)\n\n"
        "Key Methods:\n"
        "  • get_connection(name) → conn\n"
        "  • connection(name)     → ctx mgr\n"
        "  • execute(db, sql)     → cursor\n"
        "  • fetch_all(db, sql)   → [dict]\n"
        "  • fetch_one(db, sql)   → dict\n"
        "  • register_database()  → add new\n"
        "  • get_slow_queries()   → monitor\n"
        "  • close_all()          → cleanup\n\n"
        "Properties:\n"
        "  • db.atm_data  → atm_data.db\n"
        "  • db.ecosystem → ecosystem.db\n"
        "  • db.feature_store → analytics\n\n"
        "Logging:\n"
        "  • Slow queries (>1s) auto-logged\n"
        "    to feature_store.query_log\n\n"
        "Connection Pool:\n"
        "  • WAL journal mode\n"
        "  • Foreign keys enabled\n"
        "  • Row factory = sqlite3.Row"
    )
    ax.text(0.02, 0.95, dm_text, fontsize=6.5, color="#e0e0e0",
            family="monospace", transform=ax.transAxes, va="top",
            linespacing=1.3)

    plt.tight_layout()
    path = OUTPUTS_CHARTS / "database_schema_diagram.png"
    plt.savefig(str(path), dpi=200, bbox_inches="tight")
    plt.close()
    print(f"[green]Schema diagram saved: {path}[/green]")
    return path


def create_text_diagrams():
    output_dir = OUTPUTS_CHARTS
    output_dir.mkdir(parents=True, exist_ok=True)

    text = r"""
╔══════════════════════════════════════════════════════════════════════════════════════════════════════════╗
║                          ATM SIMULATION — COMPLETE DATA ARCHITECTURE                                    ║
╚══════════════════════════════════════════════════════════════════════════════════════════════════════════╝

┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│  LAYER 1 — RAW / INGESTION                              LAYER 2 — OPERATIONAL (OLTP)                    │
│                                                                                                        │
│  data/raw/RBI_ATM_Stats.csv                              data/processed/ecosystem.db                    │
│        │                                                           │                                     │
│        ▼                                                           ▼                                     │
│  ┌─────────────┐   clean    ┌─────────────┐              ┌──────────────────────────┐                   │
│  │DataIngestion│ ────────►  │ atm_data.db │              │  users                    │                   │
│  │ (load_csv,  │            │ ┌────────── │              │  transactions             │                   │
│  │  clean_data,│            │ │atm_card   │              │  loan_applications        │                   │
│  │  save2sqlite│            │ │_stats     │              │  fraud_flags              │                   │
│  └──────┬──────┘            │ │bank_summary│             │  credit_history           │                   │
│         │                   │ │monthly_agg │             │  user_sessions            │                   │
│         │                   │ └─────────── │             │  savings_goals            │                   │
│         ▼                   └──────┬───────┘             │  feedback                 │                   │
│  ┌─────────────┐                  │                      │  [data_catalog]           │                   │
│  │FeatureEng   │                  │                      │  [export_log]             │                   │
│  │(lag/roll/   │                  ▼                      └───────────┬──────────────┘                   │
│  │ ratio/encode│          ┌─────────────┐                          │                                     │
│  └──────┬──────┘          │DataAnalysis │                          │ (read/write by all ops)               │
│         │                 │(queries for │                          ▼                                     │
│         ▼                 │ charts/viz) │              ┌──────────────────────┐                          │
│  features_data.csv        └──────┬──────┘              │  UserManager         │                          │
│  (output, no consumer)           │                     │  ATMSimulator        │                          │
│                                  ▼                     │  RealTimeFraudDetect │                          │
│                           ┌─────────────┐              │  UserAnalytics       │                          │
│                           │  DataViz    │              │  ReportGenerator     │                          │
│                           │  (22 charts)│              │  DataGenerator       │                          │
│                           └─────────────┘              │  AutoRetrain         │                          │
│                                                        └──────────────────────┘                          │
└────────────────────────────────────────────────────────────────────────────────────────────────────────┘
                                         │
              ┌──────────────────────────┼──────────────────────────────┐
              ▼                          ▼                              ▼
┌─────────────────────────┐  ┌─────────────────────────┐  ┌─────────────────────────┐
│   atm_data.db MODELS    │  │  ecosystem.db MODELS    │  │  RULE-BASED MODELS      │
│   (read-only, RBI data) │  │  (user/txn data)        │  │  (no SQL needed)        │
│                         │  │                         │  │                         │
│  ┌───────────────────┐  │  │  ┌───────────────────┐  │  │  ┌───────────────────┐  │
│  │CashDemandForecaster│  │  │  │CreditScorer       │  │  │  │InvestmentRecomm.  │  │
│  │AnomalyDetector    │  │  │  │ChurnPredictor     │  │  │  │RFMSegmenter       │  │
│  │ChannelMigration   │  │  │  │LoanDefaultModel   │  │  │  │SavingsOptimizer   │  │
│  │TransactionPredict │  │  │  │BankRecommender    │  │  │  │SentimentAnalyzer  │  │
│  │BankClustering     │  │  │  │SpendingForecaster │  │  │  │FraudDetector      │  │
│  │WhatIfSimulator    │  │  │  │                   │  │  │  │Explainer(SHAP)    │  │
│  │LSTMForecaster     │  │  │  │                   │  │  │  │                   │  │
│  └───────────────────┘  │  │  └───────────────────┘  │  │  └───────────────────┘  │
└─────────────────────────┘  └─────────────────────────┘  └─────────────────────────┘
              │                          │                              │
              └──────────────┬───────────┘                              │
                             │                                          │
                             ▼                                          ▼
              ┌──────────────────────────────┐        ┌────────────────────────────┐
              │  [NEW] FeatureStore          │        │   data/models/*.pkl        │
              │  ┌────────────────────────── │        │   (persisted binaries)     │
              │  │feature_definitions        │        └────────────────────────────┘
              │  │feature_snapshots          │
              │  └────────────────────────── │        ┌────────────────────────────┐
              └──────────────┬───────────────┘        │   outputs/training_data/   │
                             │                        │   (CSV exports, portable)  │
                             ▼                        └────────────────────────────┘
              ┌──────────────────────────────┐
              │  [NEW] ModelRegistry         │
              │  ┌────────────────────────── │
              │  │model_registry             │
              │  │model_versions (metrics)   │
              │  │production_log (A/B)      │
              │  └────────────────────────── │
              └──────────────┬───────────────┘
                             │
                             ▼
              ┌──────────────────────────────┐
              │  [NEW] DataCatalog           │
              │  ┌────────────────────────── │
              │  │data_catalog (schemas)     │
              │  │export_log (lineage)      │
              │  │query_log (perf monitor)  │
              │  └────────────────────────── │
              └──────────────────────────────┘


┌══════════════════════════════════════════════════════════════════════════════════════════════════════════╗
║                                  NEW DATA PLATFORM — ACCESS LAYER                                        ║
╠══════════════════════════════════════════════════════════════════════════════════════════════════════════╣
║                                                                                                          ║
║   src/data/                                                                                              ║
║   ├── __init__.py        — exports: DatabaseManager, db, FeatureStore, ModelRegistry, DataCatalog        ║
║   ├── db_manager.py      — Singleton connection manager for all 3 databases                              ║
║   ├── feature_store.py   — Materialized feature vectors, snapshots, feature definitions                  ║
║   ├── model_registry.py  — Versioned model tracking, metrics, A/B compare, production promotion          ║
║   ├── data_catalog.py    — Schema versioning, export lineage, change detection                           ║
║   └── generate_diagrams.py — Script to generate all architecture diagrams                                ║
║                                                                                                          ║
║   DatabaseManager (singleton):                                                                           ║
║   ┌──────────────────────────────────────────────────────────────────────────────────────────────────┐  ║
║   │  db = DatabaseManager()  ← one instance shared across entire app                                │  ║
║   │                                                                                                  │  ║
║   │  db.get_connection('atm_data')      → sqlite3.Connection to atm_data.db                         │  ║
║   │  db.get_connection('ecosystem')     → sqlite3.Connection to ecosystem.db                        │  ║
║   │  db.get_connection('feature_store') → sqlite3.Connection to feature_store.db                    │  ║
║   │                                                                                                  │  ║
║   │  db.execute('ecosystem', 'SELECT * FROM users WHERE user_id=?', (1,))   → cursor                │  ║
║   │  db.fetch_all('ecosystem', 'SELECT * FROM transactions')               → [dict]                 │  ║
║   │  db.fetch_one('ecosystem', 'SELECT COUNT(*) as cnt FROM users')        → dict                   │  ║
║   │                                                                                                  │  ║
║   │  with db.connection('ecosystem') as conn:                                                        │  ║
║   │      conn.execute(...)               ← context manager with auto-commit/rollback                 │  ║
║   │                                                                                                  │  ║
║   │  db.register_database('custom', '/path/to/custom.db')   ← add new databases at runtime           │  ║
║   │  db.close_all()                                           ← cleanup all connections              │  ║
║   │  db.get_slow_queries(min_duration_ms=1000)               ← performance monitoring                │  ║
║   └──────────────────────────────────────────────────────────────────────────────────────────────────┘  ║
║                                                                                                          ║
╠══════════════════════════════════════════════════════════════════════════════════════════════════════════╣
║  KEY BENEFITS                                                                                            ║
║                                                                                                          ║
║  1. CENTRALIZED CONNECTIONS: All 10+ classes go through db_manager instead of raw sqlite3.connect()      ║
║  2. DATA LINEAGE: Every model training → which snapshot → which export → which schema                   ║
║  3. NO DUPLICATE SQL: FeatureStore computes once, all models consume                                    ║
║  4. VERSIONED MODELS: A/B compare, promote to prod, rollback, performance trends                         ║
║  5. SCHEMA AWARENESS: DataCatalog tracks schema changes so old training CSVs remain interpretable        ║
║  6. QUERY MONITORING: Slow queries (>1s) auto-logged for performance tuning                              ║
║  7. GRADUAL MIGRATION: Old code still works — no breaking changes                                        ║
╚══════════════════════════════════════════════════════════════════════════════════════════════════════════╝
"""
    path = output_dir / "architecture_text_diagram.txt"
    with open(str(path), "w", encoding="utf-8") as f:
        f.write(text)
    print(f"[green]Text diagram saved: {path}[/green]")
    return path


def generate_all():
    from rich.console import Console
    console = Console()
    console.print("[bold yellow]Generating architecture diagrams...[/bold yellow]")
    p1 = create_architecture_overview()
    p2 = create_data_flow_diagram()
    p3 = create_schema_diagram()
    p4 = create_text_diagrams()
    console.print(f"[green]Generated {4} diagrams:[/green]")
    console.print(f"  1. {p1}")
    console.print(f"  2. {p2}")
    console.print(f"  3. {p3}")
    console.print(f"  4. {p4}")
    return [p1, p2, p3, p4]


if __name__ == "__main__":
    generate_all()
