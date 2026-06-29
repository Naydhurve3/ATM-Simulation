import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib.patches import Wedge
import seaborn as sns
import numpy as np
import pandas as pd
from pathlib import Path
from src.utils import OUTPUTS_CHARTS
import webbrowser

plt.rcParams["figure.dpi"] = 150
plt.rcParams["figure.figsize"] = (12, 6)
plt.rcParams["font.size"] = 11
sns.set_style("whitegrid")

class DataVisualization:
    def __init__(self, data_analysis):
        self.da = data_analysis
        self.chart_dir = OUTPUTS_CHARTS
        self.chart_dir.mkdir(parents=True, exist_ok=True)

    def plot_monthly_trend(self, metric="Total_Txn_Vol", bank_name=None, title=None):
        trend = self.da.monthly_trend(bank_name, metric)
        if trend.empty:
            return None
        fig, ax = plt.subplots()
        ax.plot(range(len(trend)), trend[metric], marker="o", linewidth=2, color="#2563eb")
        ax.fill_between(range(len(trend)), trend[metric], alpha=0.1, color="#2563eb")
        ax.set_xticks(range(len(trend)))
        ax.set_xticklabels(trend["Reporting_Month"], rotation=45, ha="right")
        lbl = bank_name or "All Banks"
        ax.set_title(title or f"{metric} Trend — {lbl}", fontweight="bold")
        ax.set_xlabel("Month")
        ax.set_ylabel(metric)
        ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
        fig.tight_layout()
        path = self.chart_dir / f"trend_{metric}_{lbl.replace(' ','_')}.png"
        fig.savefig(path, bbox_inches="tight")
        plt.close(fig)
        return path

    def plot_market_share(self, metric="Total_Txn_Vol", top_n=10):
        ms = self.da.market_share(metric).head(top_n)
        fig, ax = plt.subplots()
        colors = plt.cm.Blues(np.linspace(0.4, 0.9, len(ms)))
        bars = ax.barh(ms["Bank_Name"], ms["Share_%"], color=colors[::-1])
        for bar, val in zip(bars, ms["Share_%"]):
            ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height()/2,
                    f"{val:.1f}%", va="center", fontsize=9)
        ax.set_xlabel("Market Share (%)")
        ax.set_title(f"Market Share by {metric}", fontweight="bold")
        ax.invert_yaxis()
        fig.tight_layout()
        path = self.chart_dir / f"market_share_{metric}.png"
        fig.savefig(path, bbox_inches="tight")
        plt.close(fig)
        return path

    def plot_correlation_heatmap(self):
        corr = self.da.correlation_matrix()
        key_cols = ["Total_ATMs", "Total_Cards", "CC_Total_Vol", "CC_Total_Val",
                     "DC_Total_Vol", "DC_Total_Val", "Digital_Share", "Cash_Share",
                     "PoS", "UPI_QR_Codes"]
        existent = [c for c in key_cols if c in corr.columns]
        corr_subset = corr.loc[existent, existent]
        fig, ax = plt.subplots(figsize=(10, 8))
        sns.heatmap(corr_subset, annot=True, fmt=".2f", cmap="RdBu_r",
                    center=0, vmin=-1, vmax=1, ax=ax, linewidths=0.5)
        ax.set_title("Correlation Heatmap", fontweight="bold")
        fig.tight_layout()
        path = self.chart_dir / "correlation_heatmap.png"
        fig.savefig(path, bbox_inches="tight")
        plt.close(fig)
        return path

    def plot_bank_comparison(self, banks, metrics):
        comp = self.da.compare_banks(banks)
        fig, axes = plt.subplots(1, len(metrics), figsize=(6*len(metrics), 5))
        if len(metrics) == 1:
            axes = [axes]
        for ax, metric in zip(axes, metrics):
            if metric in comp.columns:
                vals = comp.set_index("Bank_Name")[metric]
                colors = plt.cm.Set2(np.linspace(0, 1, len(vals)))
                ax.bar(vals.index, vals.values, color=colors)
                ax.set_title(metric, fontweight="bold")
                ax.tick_params(axis="x", rotation=45)
                ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
        fig.tight_layout()
        path = self.chart_dir / f"comparison_{'_'.join(banks)}.png"
        fig.savefig(path, bbox_inches="tight")
        plt.close(fig)
        return path

    def plot_radar_comparison(self, banks, metrics):
        try:
            comp = self.da.compare_banks(banks)
            fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(polar=True))
            angles = np.linspace(0, 2 * np.pi, len(metrics), endpoint=False).tolist()
            angles += angles[:1]
            colors = plt.cm.Set2(np.linspace(0, 1, len(banks)))
            for i, bank in enumerate(banks):
                if bank not in comp["Bank_Name"].values:
                    continue
                row = comp[comp["Bank_Name"] == bank].iloc[0]
                values = [row[m] if m in comp.columns else 0 for m in metrics]
                values_norm = [(v - min(values)) / (max(values) - min(values) + 0.001) for v in values]
                values_norm += values_norm[:1]
                ax.plot(angles, values_norm, 'o-', linewidth=2, label=bank, color=colors[i])
                ax.fill(angles, values_norm, alpha=0.1, color=colors[i])
            ax.set_xticks(angles[:-1])
            ax.set_xticklabels(metrics, size=10)
            ax.set_title("Bank Comparison — Radar", fontweight="bold", pad=20)
            ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1))
            fig.tight_layout()
            path = self.chart_dir / f"radar_comparison_{'_'.join(banks)}.png"
            fig.savefig(path, bbox_inches="tight")
            plt.close(fig)
            return path
        except:
            return None

    def plot_gauge(self, value, title="Score", max_val=900, path="gauge.png"):
        try:
            fig, ax = plt.subplots(figsize=(6, 4))
            ax.axis("off")
            colors = ["#dc2626", "#f59e0b", "#22c55e"]
            wedges, _ = ax.pie([0.33, 0.33, 0.34], colors=colors,
                               startangle=180, counterclock=False,
                               radius=0.8, wedgeprops=dict(width=0.3, edgecolor="white"))
            ax.text(0, -0.1, str(value), ha="center", va="center", fontsize=32, fontweight="bold")
            ax.text(0, -0.35, title, ha="center", va="center", fontsize=14, color="gray")
            ax.text(-0.7, 0.5, "Poor", ha="center", fontsize=9, color="gray")
            ax.text(0.7, 0.5, "Excellent", ha="center", fontsize=9, color="gray")
            fig.tight_layout()
            full_path = self.chart_dir / path
            fig.savefig(full_path, bbox_inches="tight")
            plt.close(fig)
            return full_path
        except:
            return None

    def plot_calendar_heatmap(self, user_transactions, title="Activity", path="calendar_heatmap.png"):
        try:
            if not user_transactions:
                return None
            df = pd.DataFrame(user_transactions)
            df["date"] = pd.to_datetime(df["timestamp"])
            df["day"] = df["date"].dt.day_name()
            df["week"] = df["date"].dt.isocalendar().week
            pivot = df.pivot_table(index="day", columns="week", aggfunc="size", fill_value=0)
            day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            pivot = pivot.reindex([d for d in day_order if d in pivot.index])
            fig, ax = plt.subplots(figsize=(10, 3))
            sns.heatmap(pivot, ax=ax, cmap="YlOrRd", linewidths=0.5, cbar_kws={"shrink": 0.8})
            ax.set_title(f"{title} — Activity Heatmap", fontweight="bold")
            fig.tight_layout()
            full_path = self.chart_dir / path
            fig.savefig(full_path, bbox_inches="tight")
            plt.close(fig)
            return full_path
        except:
            return None

    def plot_channel_pie(self, bank_name=None):
        ch = self.da.channel_breakdown(bank_name)
        labels = list(ch.keys())
        values = [ch[k]["Vol"] for k in labels]
        if sum(values) == 0:
            return None
        fig, ax = plt.subplots()
        colors = plt.cm.tab20c(np.linspace(0, 1, len(labels)))
        wedges, texts, autotexts = ax.pie(
            values, labels=None, autopct="%1.1f%%", colors=colors, startangle=90
        )
        ax.legend(wedges, labels, title="Channel", loc="center left",
                  bbox_to_anchor=(1, 0, 0.5, 1), fontsize=8)
        lbl = bank_name or "All Banks"
        ax.set_title(f"Transaction Volume by Channel — {lbl}", fontweight="bold")
        fig.tight_layout()
        path = self.chart_dir / f"channel_pie_{lbl.replace(' ','_')}.png"
        fig.savefig(path, bbox_inches="tight")
        plt.close(fig)
        return path

    def plot_clusters(self, X_pca, labels, centers=None):
        fig, ax = plt.subplots(figsize=(10, 8))
        scatter = ax.scatter(X_pca[:, 0], X_pca[:, 1], c=labels, cmap="Set2",
                             s=100, alpha=0.8, edgecolors="w", linewidth=0.5)
        if centers is not None:
            ax.scatter(centers[:, 0], centers[:, 1], c="red", marker="X",
                       s=200, linewidths=2, edgecolors="black", label="Centroids")
        ax.set_xlabel("PCA Component 1")
        ax.set_ylabel("PCA Component 2")
        ax.set_title("Bank Clustering (PCA Projection)", fontweight="bold")
        legend1 = ax.legend(*scatter.legend_elements(), title="Cluster",
                            loc="best", fontsize=9)
        ax.add_artist(legend1)
        fig.tight_layout()
        path = self.chart_dir / "bank_clusters.png"
        fig.savefig(path, bbox_inches="tight")
        plt.close(fig)
        return path

    def plot_amortization_schedule(self, schedule, path="amortization.png"):
        months = [s["month"] for s in schedule]
        interest = [s["interest"] for s in schedule]
        principal = [s["principal"] for s in schedule]
        balance = [s["balance"] for s in schedule]
        fig, ax1 = plt.subplots()
        ax1.bar(months, principal, label="Principal", color="#22c55e")
        ax1.bar(months, interest, bottom=principal, label="Interest", color="#dc2626")
        ax1.set_xlabel("Month")
        ax1.set_ylabel("Payment Amount")
        ax1.legend(loc="upper left")
        ax2 = ax1.twinx()
        ax2.plot(months, balance, color="#2563eb", linewidth=2, marker=".", label="Balance")
        ax2.set_ylabel("Remaining Balance")
        ax2.legend(loc="upper right")
        ax1.set_title("Amortization Schedule", fontweight="bold")
        fig.tight_layout()
        full_path = self.chart_dir / path
        fig.savefig(full_path, bbox_inches="tight")
        plt.close(fig)
    def plot_churn_gauge(self, risk_score, path="churn_gauge.png"):
        fig, ax = plt.subplots(figsize=(8, 2))
        ax.axis("off")
        gradient = np.linspace(0, 1, 256).reshape(1, -1)
        gradient = np.vstack([gradient, gradient])
        grad_img = np.zeros((2, 256, 4))
        for i in range(256):
            t = i / 255
            if t < 0.5:
                r, g, b = 0.2 + 0.8 * (t * 2), 0.8 - 0.6 * (t * 2), 0.2
            else:
                r, g, b = 1.0, 0.8 - 0.8 * ((t - 0.5) * 2), 0.2 - 0.2 * ((t - 0.5) * 2)
            grad_img[:, i] = [r, g, b, 1]
        ax.imshow(grad_img, aspect="auto", extent=[0, 1, 0, 1])
        marker_x = max(0, min(1, risk_score))
        ax.scatter(marker_x, 0.5, marker="v", color="black", s=200, zorder=5)
        ax.text(marker_x, 0.15, f"{risk_score:.2f}", ha="center", va="center", fontsize=14, fontweight="bold", color="black")
        ax.text(0.02, 0.8, "Low Risk", ha="left", va="center", fontsize=9, color="white", fontweight="bold")
        ax.text(0.98, 0.8, "High Risk", ha="right", va="center", fontsize=9, color="white", fontweight="bold")
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_title("Churn Risk Gauge", fontweight="bold", pad=10)
        fig.tight_layout()
        full_path = self.chart_dir / path
        fig.savefig(full_path, bbox_inches="tight")
        plt.close(fig)
        return full_path

    def plot_monthly_spending_trend(self, months, spent, deposited, path="spending_trend.png"):
        fig, ax = plt.subplots()
        x = np.arange(len(months))
        ax.plot(x, spent, color="#dc2626", linewidth=2, marker="o", label="Spent")
        ax.plot(x, deposited, color="#22c55e", linewidth=2, marker="o", label="Deposited")
        ax.fill_between(x, spent, deposited, alpha=0.15, color="#2563eb")
        ax.set_xticks(x)
        ax.set_xticklabels(months, rotation=45, ha="right")
        ax.set_xlabel("Month")
        ax.set_ylabel("Amount")
        ax.set_title("Monthly Spending Trend", fontweight="bold")
        ax.legend()
        ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
        fig.tight_layout()
        full_path = self.chart_dir / path
        fig.savefig(full_path, bbox_inches="tight")
        plt.close(fig)
    @staticmethod
    def open_chart(path):
        try:
            full_path = str(Path(path).resolve())
            if os.name == "nt":
                os.startfile(full_path)
            else:
                webbrowser.open(f"file://{full_path}")
        except:
            pass


