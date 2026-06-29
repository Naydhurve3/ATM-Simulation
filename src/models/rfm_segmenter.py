from datetime import datetime, timedelta

class RFMSegmenter:
    def segment(self, transactions):
        if not transactions:
            return {"rfm_score": {"R": 0, "F": 0, "M": 0}, "total_score": 0, "segment": "Unknown", "recommendation": "No transaction data available."}
        now = datetime.now()
        last_txn = max(t.get("timestamp", now) for t in transactions)
        recency = (now - last_txn).days if isinstance(last_txn, datetime) else 0
        cutoff_30 = now - timedelta(days=30)
        recent = [t for t in transactions if isinstance(t.get("timestamp"), datetime) and t["timestamp"] >= cutoff_30]
        frequency = len(recent)
        amounts = [t.get("amount", 0) for t in transactions if t.get("amount") is not None]
        monetary = sum(amounts) / len(amounts) if amounts else 0

        r = self._score_recency(recency)
        f = self._score_frequency(frequency)
        m = self._score_monetary(monetary)
        total = r + f + m
        segment = self._map_segment(total)
        rec = self._recommendation(segment)
        return {
            "rfm_score": {"R": r, "F": f, "M": m},
            "total_score": total,
            "segment": segment,
            "recommendation": rec,
        }

    def _score_recency(self, days):
        if days <= 2:
            return 5
        if days <= 7:
            return 4
        if days <= 15:
            return 3
        if days <= 30:
            return 2
        return 1

    def _score_frequency(self, count):
        if count >= 20:
            return 5
        if count >= 10:
            return 4
        if count >= 5:
            return 3
        if count >= 2:
            return 2
        return 1

    def _score_monetary(self, avg):
        if avg >= 50000:
            return 5
        if avg >= 20000:
            return 4
        if avg >= 10000:
            return 3
        if avg >= 5000:
            return 2
        return 1

    def _map_segment(self, score):
        if score >= 13:
            return "Champions"
        if score >= 10:
            return "Loyal Customers"
        if score >= 7:
            return "Potential Loyalists"
        if score >= 4:
            return "At Risk"
        return "Lost"

    def _recommendation(self, segment):
        recs = {
            "Champions": "Reward them with exclusive offers and loyalty programs. They are your best customers.",
            "Loyal Customers": "Engage with personalized offers and cross-sell premium products.",
            "Potential Loyalists": "Nurture with targeted campaigns and educational content to deepen engagement.",
            "At Risk": "Reactivate with special offers, reminders, and win-back campaigns.",
            "Lost": "Send re-engagement emails with strong incentives to return.",
        }
        return recs.get(segment, "No specific recommendation.")

    def get_segment_behavior(self, segment):
        behaviors = {
            "Champions": "High-value, frequent, and recently active customers. Most profitable segment.",
            "Loyal Customers": "Regular customers with good transaction history. Respond well to offers.",
            "Potential Loyalists": "Moderately active customers with room to grow. Need nurturing.",
            "At Risk": "Previously active but declining engagement. Risk of churning.",
            "Lost": "Long-inactive customers unlikely to return without significant intervention.",
        }
        return behaviors.get(segment, "Unknown segment.")
