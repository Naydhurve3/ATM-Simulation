import sqlite3
from datetime import datetime
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import matplotlib.pyplot as plt
from collections import defaultdict

class SentimentAnalyzer:
    def __init__(self):
        self.analyzer = SentimentIntensityAnalyzer()

    def analyze_text(self, text):
        scores = self.analyzer.polarity_scores(text)
        compound = scores["compound"]
        if compound >= 0.05:
            label = "Positive"
        elif compound <= -0.05:
            label = "Negative"
        else:
            label = "Neutral"
        return {
            "compound": compound,
            "positive": scores["pos"],
            "negative": scores["neg"],
            "neutral": scores["neu"],
            "sentiment_label": label,
        }

    def analyze_feedback(self, ecosystem_db_path):
        conn = sqlite3.connect(str(ecosystem_db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT id, feedback_text, created_at FROM feedback")
        rows = cursor.fetchall()
        conn.close()
        results = []
        for row in rows:
            fid, text, created_at = row
            analysis = self.analyze_text(text)
            results.append({
                "feedback_id": fid,
                "text": text,
                "compound_score": analysis["compound"],
                "sentiment_label": analysis["sentiment_label"],
                "created_at": created_at,
            })
        return results

    def get_sentiment_summary(self, feedback_results):
        total = len(feedback_results)
        if total == 0:
            return {"total_count": 0, "positive_count": 0, "negative_count": 0, "neutral_count": 0, "avg_compound": 0.0, "positive_pct": 0.0, "negative_pct": 0.0, "neutral_pct": 0.0}
        pos = sum(1 for r in feedback_results if r["sentiment_label"] == "Positive")
        neg = sum(1 for r in feedback_results if r["sentiment_label"] == "Negative")
        neu = sum(1 for r in feedback_results if r["sentiment_label"] == "Neutral")
        avg_comp = sum(r["compound_score"] for r in feedback_results) / total
        return {
            "total_count": total,
            "positive_count": pos,
            "negative_count": neg,
            "neutral_count": neu,
            "avg_compound": round(avg_comp, 4),
            "positive_pct": round(pos / total * 100, 2),
            "negative_pct": round(neg / total * 100, 2),
            "neutral_pct": round(neu / total * 100, 2),
        }

    def plot_sentiment_trend(self, feedback_results, output_path):
        date_groups = defaultdict(list)
        for r in feedback_results:
            dt = r.get("created_at")
            if dt:
                if isinstance(dt, str):
                    dt = datetime.strptime(dt[:10], "%Y-%m-%d")
                date_key = dt.date() if hasattr(dt, "date") else dt
                date_groups[date_key].append(r["compound_score"])
        dates = sorted(date_groups.keys())
        avgs = [sum(date_groups[d]) / len(date_groups[d]) for d in dates]
        plt.figure(figsize=(10, 5))
        plt.plot(dates, avgs, marker="o", linestyle="-", color="b")
        plt.axhline(y=0, color="gray", linestyle="--", alpha=0.7)
        plt.title("Sentiment Trend Over Time")
        plt.xlabel("Date")
        plt.ylabel("Average Compound Score")
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(output_path)
        plt.close()
