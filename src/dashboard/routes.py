import sys
import os
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, date
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from flask import render_template, jsonify
from src.data.db_manager import db
import plotly.graph_objects as go
import plotly.express as px
from plotly.offline import plot as plotly_plot
from plotly.subplots import make_subplots

def _plot( fig):
    return plotly_plot(fig, include_plotlyjs=False, output_type='div')

def _get_monitor():
    from src.models.model_monitor import ModelMonitor
    return ModelMonitor()

def register_routes(app):

    @app.route('/')
    def overview():
        da = app.config.get('data_analysis')
        um = app.config.get('user_manager')
        user_data = app.config.get('user_data')
        total_users = 0
        total_txns = 0
        avg_balance = 0
        credit_score = 0
        bank_name = ""
        if um:
            try:
                total_users = um.get_user_count()
                c = um.conn.cursor()
                c.execute("SELECT COUNT(*) FROM transactions")
                total_txns = c.fetchone()[0] or 0
                c.execute("SELECT AVG(balance) FROM users")
                avg_balance = round(c.fetchone()[0] or 0, 2)
            except:
                pass
        if user_data:
            credit_score = user_data.get('credit_score', 0)
            bank_name = user_data.get('bank', '')
        gauge_html = ""
        if credit_score:
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=credit_score,
                number={"suffix": "/900", "font": {"size": 28}},
                gauge={
                    "axis": {"range": [0, 900], "tickwidth": 1},
                    "bar": {"color": "#2563eb"},
                    "steps": [
                        {"range": [0, 300], "color": "#ef4444"},
                        {"range": [300, 600], "color": "#f59e0b"},
                        {"range": [600, 750], "color": "#84cc16"},
                        {"range": [750, 900], "color": "#22c55e"},
                    ],
                    "threshold": {
                        "line": {"color": "red", "width": 4},
                        "thickness": 0.75,
                        "value": credit_score,
                    },
                },
                title={"text": "Credit Score"}
            ))
            fig.update_layout(height=280, margin=dict(l=20, r=20, t=40, b=20))
            gauge_html = _plot(fig)
        top_banks_html = ""
        monthly_html = ""
        if da:
            try:
                top5 = da.top_banks("Total_Txn_Vol", 5)
                if top5 is not None and len(top5):
                    fig = go.Figure(go.Bar(
                        x=top5.values.tolist(),
                        y=top5.index.tolist(),
                        orientation='h',
                        marker_color='#2563eb',
                        text=[f"{v:,.0f}" for v in top5.values],
                        textposition='outside',
                    ))
                    fig.update_layout(
                        title="Top 5 Banks by Transaction Volume",
                        xaxis_title="Total Volume",
                        yaxis_title="",
                        height=350,
                        margin=dict(l=10, r=80, t=40, b=10),
                    )
                    top_banks_html = _plot(fig)
            except:
                pass
            try:
                trend = da.monthly_trend(None, "Total_Txn_Vol")
                if trend is not None and not trend.empty:
                    fig = go.Figure(go.Scatter(
                        x=trend["Reporting_Month"],
                        y=trend["Total_Txn_Vol"],
                        mode='lines+markers',
                        line=dict(color='#2563eb', width=2),
                        fill='tozeroy',
                        fillcolor='rgba(37,99,235,0.1)',
                    ))
                    fig.update_layout(
                        title="Monthly Transaction Volume Trend",
                        xaxis_title="Month",
                        yaxis_title="Total Volume",
                        height=350,
                        margin=dict(l=10, r=20, t=40, b=40),
                    )
                    monthly_html = _plot(fig)
            except:
                pass
        return render_template('index.html',
                               total_users=total_users,
                               total_txns=total_txns,
                               avg_balance=avg_balance,
                               credit_score=credit_score,
                               bank_name=bank_name,
                               gauge_chart=gauge_html,
                               top_banks_chart=top_banks_html,
                               monthly_chart=monthly_html)

    @app.route('/analysis')
    def analysis():
        da = app.config.get('data_analysis')
        metric = app.config.get('metric', 'Total_Txn_Vol')
        heatmap_html = ""
        market_html = ""
        pie_html = ""
        trend_html = ""
        if da:
            try:
                corr = da.correlation_matrix()
                if corr is not None and not corr.empty:
                    key_cols = ["Total_ATMs", "Total_Cards", "CC_Total_Vol", "CC_Total_Val",
                                 "DC_Total_Vol", "DC_Total_Val", "Digital_Share", "Cash_Share",
                                 "PoS", "UPI_QR_Codes"]
                    existent = [c for c in key_cols if c in corr.columns]
                    corr_sub = corr.loc[existent, existent]
                    fig = go.Figure(data=go.Heatmap(
                        z=corr_sub.values,
                        x=corr_sub.columns,
                        y=corr_sub.index,
                        colorscale='RdBu_r',
                        zmin=-1, zmax=1,
                        text=np.round(corr_sub.values, 2),
                        texttemplate='%{text}',
                    ))
                    fig.update_layout(title="Correlation Heatmap", height=500, margin=dict(l=80, r=20, t=40, b=80))
                    heatmap_html = _plot(fig)
            except:
                pass
            try:
                ms = da.market_share(metric)
                if ms is not None and not ms.empty:
                    fig = go.Figure(go.Bar(
                        x=ms["Share_%"][:10],
                        y=ms["Bank_Name"][:10],
                        orientation='h',
                        marker_color='#2563eb',
                        text=[f"{v:.1f}%" for v in ms["Share_%"][:10]],
                        textposition='outside',
                    ))
                    fig.update_layout(title=f"Market Share by {metric} (Top 10)", height=450,
                                      xaxis_title="Share (%)", yaxis_title="",
                                      margin=dict(l=10, r=60, t=40, b=10))
                    market_html = _plot(fig)
            except:
                pass
            try:
                ch = da.channel_breakdown(None)
                if ch:
                    labels = list(ch.keys())
                    values = [ch[k]["Vol"] for k in labels]
                    if sum(values) > 0:
                        fig = go.Figure(data=go.Pie(labels=labels, values=values, hole=0.3))
                        fig.update_layout(title="Channel Breakdown (Volume)", height=400,
                                          margin=dict(l=20, r=20, t=40, b=20))
                        pie_html = _plot(fig)
            except:
                pass
            try:
                trend = da.monthly_trend(None, metric)
                if trend is not None and not trend.empty:
                    fig = go.Figure(go.Scatter(
                        x=trend["Reporting_Month"], y=trend[metric],
                        mode='lines+markers', line=dict(color='#2563eb', width=2),
                    ))
                    fig.update_layout(title=f"Monthly Trend — {metric}", height=350,
                                      xaxis_title="Month", yaxis_title=metric,
                                      margin=dict(l=10, r=20, t=40, b=40))
                    trend_html = _plot(fig)
            except:
                pass
        return render_template('analysis.html',
                               heatmap_chart=heatmap_html,
                               market_chart=market_html,
                               pie_chart=pie_html,
                               trend_chart=trend_html,
                               current_metric=metric)

    @app.route('/ml')
    def ml_view():
        da = app.config.get('data_analysis')
        um = app.config.get('user_manager')
        models_status = {}
        feature_imp_html = ""
        cluster_html = ""
        anomaly_html = ""
        model_names = [
            "CashDemandForecaster", "TransactionPredictor", "BankClustering",
            "AnomalyDetector", "TrendAnalyzer", "ChannelMigrationPredictor",
            "WhatIfSimulator", "CreditScorer", "ChurnPredictor",
            "LoanDefaultModel", "BankRecommender", "SpendingForecaster",
        ]
        try:
            monitor = _get_monitor()
            models_status = monitor.get_all_model_status()
        except:
            pass
        try:
            predictor = None
            for mod_name in ['transaction_predictor', 'TransactionPredictor']:
                try:
                    from src.models.transaction_predictor import TransactionPredictor
                    predictor = TransactionPredictor()
                    if predictor.load():
                        break
                except:
                    predictor = None
            if predictor and predictor.is_trained:
                importance = predictor.get_feature_importance()
                if importance:
                    feats = list(importance.keys())
                    vals = list(importance.values())
                    fig = go.Figure(go.Bar(
                        x=vals, y=feats, orientation='h',
                        marker_color='#2563eb',
                        text=[f"{v:.4f}" for v in vals],
                        textposition='outside',
                    ))
                    fig.update_layout(title="XGBoost Feature Importance", height=400,
                                      xaxis_title="Importance", yaxis_title="",
                                      margin=dict(l=10, r=60, t=40, b=10))
                    feature_imp_html = _plot(fig)
        except:
            pass
        try:
            from src.models.bank_clustering import BankClustering
            clusterer = BankClustering()
            if clusterer.load():
                results = clusterer.results
                if results is not None and 'PCA1' in results.columns:
                    fig = go.Figure()
                    for cl in sorted(results['Cluster'].unique()):
                        subset = results[results['Cluster'] == cl]
                        fig.add_trace(go.Scatter(
                            x=subset['PCA1'], y=subset['PCA2'],
                            mode='markers+text', name=f"Cluster {cl}",
                            text=subset['Bank'],
                            textposition='top center',
                            marker=dict(size=12),
                        ))
                    fig.update_layout(title="Bank Clusters (PCA Projection)", height=450,
                                      xaxis_title="PCA1", yaxis_title="PCA2",
                                      margin=dict(l=10, r=20, t=40, b=10))
                    cluster_html = _plot(fig)
        except:
            pass
        try:
            from src.models.anomaly_detector import AnomalyDetector
            detector = AnomalyDetector()
            if detector.load():
                scores = detector.anomaly_scores if hasattr(detector, 'anomaly_scores') else None
                if scores is not None and len(scores):
                    threshold = np.percentile(scores, 95)
                    fig = go.Figure()
                    fig.add_trace(go.Histogram(
                        x=scores, nbinsx=50, name="All Scores",
                        marker_color='#94a3b8', opacity=0.7,
                    ))
                    fig.add_vline(x=threshold, line_dash="dash",
                                  line_color="#dc2626",
                                  annotation_text=f"Threshold ({threshold:.3f})")
                    fig.update_layout(title="Anomaly Score Distribution", height=350,
                                      xaxis_title="Anomaly Score", yaxis_title="Frequency",
                                      margin=dict(l=10, r=20, t=40, b=10))
                    anomaly_html = _plot(fig)
        except:
            pass
        return render_template('ml.html',
                               models_status=models_status,
                               model_names=model_names,
                               feature_imp_chart=feature_imp_html,
                               cluster_chart=cluster_html,
                               anomaly_chart=anomaly_html)

    @app.route('/personal')
    def personal():
        user_data = app.config.get('user_data')
        um = app.config.get('user_manager')
        spending_html = ""
        pie_html = ""
        goals_html = ""
        transactions = []
        if user_data and um:
            user_id = user_data.get('user_id')
            if user_id:
                transactions = um.get_transactions(user_id, 15)
                try:
                    conn = um.conn
                    monthly = conn.execute("""
                        SELECT strftime('%Y-%m', timestamp) as month,
                               SUM(CASE WHEN type='withdraw' THEN amount ELSE 0 END) as spent,
                               SUM(CASE WHEN type='deposit' THEN amount ELSE 0 END) as deposited
                        FROM transactions WHERE user_id = ?
                        GROUP BY month ORDER BY month DESC LIMIT 6
                    """, (user_id,)).fetchall()
                    monthly = list(reversed(monthly))
                    if monthly:
                        months = [r[0] for r in monthly]
                        spent = [(r[1] or 0) for r in monthly]
                        deposited = [(r[2] or 0) for r in monthly]
                        fig = go.Figure()
                        fig.add_trace(go.Scatter(
                            x=months, y=spent, mode='lines+markers',
                            name='Spent', line=dict(color='#dc2626', width=2),
                        ))
                        fig.add_trace(go.Scatter(
                            x=months, y=deposited, mode='lines+markers',
                            name='Deposited', line=dict(color='#22c55e', width=2),
                        ))
                        fig.update_layout(title="Monthly Spending Trend", height=350,
                                          xaxis_title="Month", yaxis_title="Amount",
                                          margin=dict(l=10, r=20, t=40, b=40))
                        spending_html = _plot(fig)
                except:
                    pass
                try:
                    txns = um.get_transactions(user_id, 200)
                    if txns:
                        type_counts = {}
                        for t in txns:
                            tp = t.get('type', 'unknown')
                            type_counts[tp] = type_counts.get(tp, 0) + 1
                        if type_counts:
                            fig = go.Figure(data=go.Pie(
                                labels=list(type_counts.keys()),
                                values=list(type_counts.values()),
                                hole=0.3,
                            ))
                            fig.update_layout(title="Transaction Types", height=350,
                                              margin=dict(l=20, r=20, t=40, b=20))
                            pie_html = _plot(fig)
                except:
                    pass
                try:
                    goals = conn.execute("""
                        SELECT goal_name, target_amount, current_amount FROM savings_goals
                        WHERE user_id = ? AND is_completed = 0
                    """, (user_id,)).fetchall()
                    if goals:
                        names = [r[0] for r in goals]
                        pcts = [(r[2] / r[1] * 100) if r[1] > 0 else 0 for r in goals]
                        colors = []
                        for p in pcts:
                            if p < 33:
                                colors.append('#dc2626')
                            elif p < 66:
                                colors.append('#eab308')
                            else:
                                colors.append('#22c55e')
                        fig = go.Figure(go.Bar(
                            x=pcts, y=names, orientation='h',
                            marker_color=colors,
                            text=[f"{p:.0f}%" for p in pcts],
                            textposition='outside',
                        ))
                        fig.update_layout(title="Savings Goal Progress", height=300,
                                          xaxis=dict(range=[0, 110], title="Progress (%)"),
                                          yaxis_title="",
                                          margin=dict(l=10, r=60, t=40, b=10))
                        goals_html = _plot(fig)
                except:
                    pass
        return render_template('personal.html',
                               user=user_data,
                               spending_chart=spending_html,
                               pie_chart=pie_html,
                               goals_chart=goals_html,
                               transactions=transactions)

    @app.route('/monitoring')
    def monitoring():
        perf_html = ""
        versions_table = []
        stale_models = []
        try:
            monitor = _get_monitor()
            all_status = monitor.get_all_model_status()
            rows = []
            for model_name, info in all_status.items():
                rows.append({
                    "model_name": model_name,
                    "version": info.get("version", 0),
                    "metrics": info.get("metrics_summary", {}),
                    "last_trained": info.get("last_trained", ""),
                    "freshness_days": info.get("freshness_days", 999),
                })
                if info.get("freshness_days", 0) > 7:
                    stale_models.append(model_name)
            rows.sort(key=lambda r: r["model_name"])
            versions_table = rows
            model_names = sorted(set(r["model_name"] for r in rows))
            if model_names:
                fig = go.Figure()
                for mn in model_names[:5]:
                    mae_data = monitor.get_performance_trend(mn, "MAE", 20)
                    rmse_data = monitor.get_performance_trend(mn, "RMSE", 20)
                    if mae_data:
                        fig.add_trace(go.Scatter(
                            x=[r[0] for r in mae_data],
                            y=[r[1] for r in mae_data],
                            mode='lines+markers',
                            name=f"{mn} MAE",
                        ))
                    if rmse_data:
                        fig.add_trace(go.Scatter(
                            x=[r[0] for r in rmse_data],
                            y=[r[1] for r in rmse_data],
                            mode='lines+markers',
                            name=f"{mn} RMSE",
                            line=dict(dash='dash'),
                        ))
                fig.update_layout(title="Model Performance Over Versions", height=400,
                                  xaxis_title="Version", yaxis_title="Metric Value",
                                  margin=dict(l=10, r=20, t=40, b=10))
                perf_html = _plot(fig)
        except:
            pass
        return render_template('monitoring.html',
                               perf_chart=perf_html,
                               versions=versions_table,
                               stale_models=stale_models)

    @app.route('/api/metrics')
    def api_metrics():
        da = app.config.get('data_analysis')
        um = app.config.get('user_manager')
        total_users = 0
        total_txns = 0
        avg_balance = 0
        if um:
            try:
                total_users = um.get_user_count()
                c = um.conn.cursor()
                c.execute("SELECT COUNT(*) FROM transactions")
                total_txns = c.fetchone()[0] or 0
                c.execute("SELECT AVG(balance) FROM users")
                avg_balance = round(c.fetchone()[0] or 0, 2)
            except:
                pass
        top_banks = {}
        if da:
            try:
                top5 = da.top_banks("Total_Txn_Vol", 5)
                if top5 is not None:
                    top_banks = top5.to_dict()
            except:
                pass
        return jsonify({
            "total_users": total_users,
            "total_transactions": total_txns,
            "avg_balance": avg_balance,
            "top_banks": top_banks,
        })

    @app.route('/api/models')
    def api_models():
        try:
            monitor = _get_monitor()
            status = monitor.get_all_model_status()
            return jsonify(status)
        except Exception as e:
            return jsonify({"error": str(e)})

    @app.route('/api/user_summary')
    def api_user_summary():
        user_data = app.config.get('user_data')
        um = app.config.get('user_manager')
        if not user_data or not um:
            return jsonify({"error": "No user data"})
        user_id = user_data.get('user_id')
        txns = []
        goals = []
        if user_id:
            txns = um.get_transactions(user_id, 10)
            try:
                c = um.conn.cursor()
                c.execute("SELECT goal_name, target_amount, current_amount, deadline, is_completed FROM savings_goals WHERE user_id = ?", (user_id,))
                goals = [dict(zip([d[0] for d in c.description], r)) for r in c.fetchall()]
            except:
                pass
        return jsonify({
            "user": {k: v for k, v in user_data.items() if k != 'pin_hash'},
            "recent_transactions": txns,
            "savings_goals": goals,
        })
