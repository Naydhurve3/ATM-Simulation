import math

class InvestmentRecommender:
    PRODUCTS = {
        "FD": {"name": "Fixed Deposit", "expected_return": 6.5},
        "RD": {"name": "Recurring Deposit", "expected_return": 6.0},
        "MF_Debt": {"name": "Mutual Fund - Debt", "expected_return": 8.0},
        "MF_Hybrid": {"name": "Mutual Fund - Hybrid", "expected_return": 10.0},
        "MF_Equity": {"name": "Mutual Fund - Equity", "expected_return": 12.0},
        "PPF": {"name": "Public Provident Fund", "expected_return": 7.1},
    }

    def recommend(self, age, income_bracket, balance, risk_tolerance="moderate"):
        if age < 18:
            products = self._allocate([("RD", 40), ("PPF", 60)], balance)
        elif income_bracket.startswith("not_earning"):
            products = self._allocate([("RD", 50), ("PPF", 50)], balance)
        elif balance < 10000:
            products = self._allocate([("RD", 100)], balance)
        elif balance <= 50000:
            products = self._allocate([("RD", 50), ("FD", 50)], balance)
        else:
            if risk_tolerance == "conservative":
                products = self._allocate([("FD", 30), ("RD", 30), ("MF_Debt", 30), ("MF_Hybrid", 10)], balance)
            elif risk_tolerance == "aggressive":
                products = self._allocate([("FD", 10), ("MF_Debt", 20), ("MF_Hybrid", 30), ("MF_Equity", 40)], balance)
            else:
                products = self._allocate([("FD", 15), ("RD", 15), ("MF_Debt", 30), ("MF_Hybrid", 30), ("MF_Equity", 10)], balance)
        products.sort(key=lambda x: x["allocation_pct"], reverse=True)
        total_expected_return_yearly = sum(p["expected_yearly_return"] for p in products)
        return {"products": products, "total_expected_return_yearly": round(total_expected_return_yearly, 2)}

    def _allocate(self, allocations, balance):
        result = []
        for key, pct in allocations:
            info = self.PRODUCTS[key]
            amount = balance * (pct / 100)
            expected_yearly = amount * (info["expected_return"] / 100)
            result.append({
                "product_key": key,
                "name": info["name"],
                "allocation_pct": pct,
                "amount": round(amount, 2),
                "expected_return_pct": info["expected_return"],
                "expected_yearly_return": round(expected_yearly, 2),
            })
        return result

    def get_explanation(self, product_name):
        explanations = {
            "Fixed Deposit": "A lump sum deposit with a fixed interest rate for a set tenure. Safe and predictable.",
            "Recurring Deposit": "Regular monthly deposits earning interest at FD-like rates. Ideal for disciplined saving.",
            "Mutual Fund - Debt": "Invests in bonds and fixed-income securities. Low risk with moderate returns.",
            "Mutual Fund - Hybrid": "A mix of debt and equity for balanced risk-return profile.",
            "Mutual Fund - Equity": "Invests primarily in stocks. High potential returns with higher risk.",
            "Public Provident Fund": "Government-backed long-term savings scheme with tax benefits and safe returns.",
        }
        return explanations.get(product_name, "No explanation available.")
