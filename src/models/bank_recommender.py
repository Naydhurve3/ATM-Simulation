import numpy as np
from src.bank_attributes import get_bank_attrs
from src.utils import get_bank_type

class BankRecommender:
    def __init__(self):
        self.metrics = {}

    def train(self, data=None):
        self.metrics = {"status": "Rule-based recommender (no training needed)"}
        return self.metrics

    def recommend(self, user_data, top_n=5):
        age = user_data.get("age", 30)
        is_minor = user_data.get("is_minor", False)
        income = user_data.get("income_bracket", "not_earning_student")
        preferences = user_data.get("preferences", {})
        from src.data_analysis import DataAnalysis
        da = DataAnalysis()
        banks = da.get_banks()
        scored = []
        for bank in banks:
            attrs = get_bank_attrs(bank)
            score = 0
            if is_minor:
                if attrs.get("has_minor_account"):
                    score += 30
                score += attrs.get("minor_savings_rate", 0) * 5
                score += attrs.get("digital_rating", 3) * 3
                if attrs.get("minor_limit", 0) > 0:
                    score += 10
            else:
                score += attrs.get("savings_rate", 3) * 5
                score += attrs.get("digital_rating", 3) * 6
                score -= abs(attrs.get("atm_fee_other", 21) - 21)
                if preferences.get("prefer_network"):
                    score += min(attrs.get("branch_count", 0) / 1000, 20)
                if preferences.get("prefer_low_fees"):
                    score -= attrs.get("monthly_fee", 0) / 20
                if preferences.get("prefer_high_limits"):
                    score += attrs.get("atm_daily_limit", 25000) / 5000
                income_type = income.split("_")[0] if "_" in income else income
                if income_type in ("earning",):
                    amt_str = income.split("_")[-1] if "_" in income else "0"
                    if "25L_plus" in income or "10L_25L" in income:
                        score += 5
                    if "25L_plus" in income:
                        score += attrs.get("digital_rating", 3) * 3
                score += attrs.get("cashback_rate", 0) * 5
                score -= attrs.get("loan_rate_pl", 10) / 2
            scored.append((score, bank))
        scored.sort(reverse=True, key=lambda x: x[0])
        return [(bank, round(score, 1)) for score, bank in scored[:top_n]]

    def get_explanation(self, bank, user_data):
        attrs = get_bank_attrs(bank)
        reasons = []
        is_minor = user_data.get("is_minor", False)
        if is_minor:
            if attrs.get("has_minor_account"):
                reasons.append(f"Offers minor account with {attrs.get('minor_savings_rate', 'N/A')}% savings rate")
            if attrs.get("minor_limit", 0) > 0:
                reasons.append(f"ATM limit of ₹{attrs.get('minor_limit', 0):,}/day for minors")
        else:
            reasons.append(f"Savings rate: {attrs.get('savings_rate', 'N/A')}%")
            reasons.append(f"Digital rating: {attrs.get('digital_rating', 'N/A')}/5")
            reasons.append(f"ATM limit: ₹{attrs.get('atm_daily_limit', 'N/A'):,}/day")
        reasons.append(attrs.get("tagline", ""))
        return reasons

    def load(self):
        return True

    def save(self):
        pass
