import math

class ATMReplenishmentOptimizer:
    def optimize(self, predicted_monthly_demand, atm_capacity=5000000, cost_per_visit=500, holding_cost_pct=0.02):
        optimal_refill_amount = math.sqrt(2 * predicted_monthly_demand * cost_per_visit / holding_cost_pct)
        optimal_refills = math.ceil(predicted_monthly_demand / optimal_refill_amount) if optimal_refill_amount > 0 else 1
        total_replenishment_cost = optimal_refills * cost_per_visit
        total_holding_cost = (optimal_refill_amount / 2) * holding_cost_pct
        total_cost = total_replenishment_cost + total_holding_cost
        return {
            "optimal_refill_amount": round(optimal_refill_amount, 2),
            "optimal_refills_per_month": optimal_refills,
            "total_replenishment_cost": round(total_replenishment_cost, 2),
            "total_holding_cost": round(total_holding_cost, 2),
            "total_cost": round(total_cost, 2),
            "predicted_demand": predicted_monthly_demand,
        }

    def compare_strategies(self, predicted_demand):
        strategies = [
            {"strategy_name": "Weekly", "refills": 4},
            {"strategy_name": "Bi-weekly", "refills": 2},
        ]
        results = []
        for s in strategies:
            refills = s["refills"]
            amount_per_refill = predicted_demand / refills
            cost = refills * 500
            holding_cost = (amount_per_refill / 2) * 0.02
            results.append({
                "strategy_name": s["strategy_name"],
                "refills": refills,
                "cost": round(cost, 2),
                "holding_cost": round(holding_cost, 2),
                "total_cost": round(cost + holding_cost, 2),
            })
        opt = self.optimize(predicted_demand)
        results.append({
            "strategy_name": "Optimized (EOQ)",
            "refills": opt["optimal_refills_per_month"],
            "cost": opt["total_replenishment_cost"],
            "holding_cost": opt["total_holding_cost"],
            "total_cost": opt["total_cost"],
        })
        best = min(results, key=lambda r: r["total_cost"])
        return {"strategies": results, "best_strategy": best["strategy_name"]}
