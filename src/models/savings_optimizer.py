import math

class SavingsGoalOptimizer:
    def optimize(self, target_amount, deadline_months, current_balance=0, monthly_income=0, monthly_expenses=0):
        monthly_surplus = monthly_income - monthly_expenses
        required_monthly = (target_amount - current_balance) / deadline_months if deadline_months > 0 else target_amount
        if required_monthly <= monthly_surplus:
            status = "achievable"
        elif required_monthly > monthly_surplus * 1.2:
            status = "tight"
        else:
            status = "difficult"

        if deadline_months <= 6:
            product = "Savings Account"
            rate = 3.5
        elif deadline_months <= 12:
            product = "Recurring Deposit"
            rate = 6.0
        elif deadline_months <= 36:
            product = "Fixed Deposit"
            rate = 6.5
        else:
            product = "Mutual Fund - Debt"
            rate = 8.0

        monthly_deposit = required_monthly
        total_deposits = monthly_deposit * deadline_months
        r = rate / 100
        if product in ("Recurring Deposit", "Fixed Deposit"):
            n = 12
            t = deadline_months / 12
            maturity_amount = total_deposits * (1 + r / n) ** (n * t)
        else:
            maturity_amount = total_deposits * (1 + r / 12) ** deadline_months

        suggestion = ""
        if status == "tight":
            suggestion = f"Consider extending the deadline or reducing the target amount. Required monthly deposit (₹{required_monthly:,.2f}) exceeds your surplus (₹{monthly_surplus:,.2f})."
        elif status == "achievable":
            suggestion = f"You can achieve this goal comfortably. Save ₹{required_monthly:,.2f} per month in a {product}."
        else:
            suggestion = f"Carefully plan your budget. Required monthly deposit is ₹{required_monthly:,.2f} against surplus of ₹{monthly_surplus:,.2f}."

        return {
            "target_amount": target_amount,
            "deadline_months": deadline_months,
            "required_monthly_deposit": round(required_monthly, 2),
            "monthly_surplus": monthly_surplus,
            "status": status,
            "recommended_product": product,
            "product_interest_rate": rate,
            "maturity_amount": round(maturity_amount, 2),
            "suggestion_text": suggestion,
        }

    def suggest_recurring_deposit(self, monthly_amount, tenure_months, rate=6.0):
        total_deposited = monthly_amount * tenure_months
        r = (rate / 100) / 12
        n = tenure_months
        maturity_amount = monthly_amount * ((1 + r) ** n - 1) / r * (1 + r) if r > 0 else total_deposited
        interest_earned = maturity_amount - total_deposited
        return {
            "monthly_amount": monthly_amount,
            "tenure_months": tenure_months,
            "total_deposited": round(total_deposited, 2),
            "maturity_amount": round(maturity_amount, 2),
            "interest_earned": round(interest_earned, 2),
        }
