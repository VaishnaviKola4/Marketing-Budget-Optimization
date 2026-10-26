"""
Constrained Marketing Budget Allocation Optimizer.
Solves non-linear optimization problems using Sequential Least Squares Programming (SLSQP)
to maximize revenue, conversions, or profit across channels under budget and flexibility constraints.
"""

from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd
from scipy.optimize import minimize

from marketing_budget_optimizer.config import OBJECTIVE_REVENUE, OBJECTIVE_CONVERSIONS, OBJECTIVE_PROFIT
from marketing_budget_optimizer.data.schemas import (
    OptimizationRequest,
    OptimizationSummary,
    ChannelOptimizationResult,
    ChannelConstraint
)
from marketing_budget_optimizer.models.saturation import SaturationCurveFitter


class BudgetAllocator:
    """
    Mathematical optimizer that reallocates total marketing budget across channels
    to maximize selected objective function subject to realistic marketing bounds.
    """

    def __init__(self, curve_fitter: SaturationCurveFitter):
        self.curve_fitter = curve_fitter

    def optimize(
        self,
        current_spend_dict: Dict[str, float],
        request: Optional[OptimizationRequest] = None,
        channel_aovs: Optional[Dict[str, float]] = None
    ) -> OptimizationSummary:
        """
        Executes constrained non-linear budget optimization.
        """
        req = request or OptimizationRequest()
        channels = [ch for ch in current_spend_dict.keys() if ch in self.curve_fitter.channel_models]

        if not channels:
            raise ValueError("None of the specified channels have fitted response models.")

        # Baseline budget
        total_current_spend = sum(current_spend_dict[ch] for ch in channels)
        target_budget = req.total_budget if req.total_budget is not None else (total_current_spend * req.budget_scaling_factor)

        # Build bounds & constraints per channel
        user_constraints: Dict[str, ChannelConstraint] = {}
        if req.constraints:
            user_constraints = {c.channel: c for c in req.constraints}

        bounds = []
        x0 = []
        for ch in channels:
            curr = current_spend_dict[ch]
            x0.append(curr)

            if ch in user_constraints:
                c = user_constraints[ch]
                if c.fixed:
                    bounds.append((curr, curr))
                else:
                    low = c.min_spend if c.min_spend is not None else curr * (1.0 - req.max_channel_shift_pct)
                    high = c.max_spend if c.max_spend is not None else curr * (1.0 + req.max_channel_shift_pct)
                    bounds.append((max(10.0, low), max(low, high)))
            else:
                low = max(10.0, curr * (1.0 - req.max_channel_shift_pct))
                high = max(low, curr * (1.0 + req.max_channel_shift_pct))
                bounds.append((low, high))

        x0 = np.array(x0, dtype=float)
        # Normalize initial guess to target budget
        if np.sum(x0) > 0:
            x0 = x0 * (target_budget / np.sum(x0))

        # Define Objective Function (minimize negative utility)
        aov_map = channel_aovs or {ch: 95.0 for ch in channels}

        def objective_func(spend_vector: np.ndarray) -> float:
            total_metric = 0.0
            for idx, ch in enumerate(channels):
                s = spend_vector[idx]
                rev = self.curve_fitter.predict(ch, s)
                if req.objective == OBJECTIVE_CONVERSIONS:
                    aov = aov_map.get(ch, 95.0)
                    total_metric += (rev / max(aov, 1.0))
                elif req.objective == OBJECTIVE_PROFIT:
                    net_margin = (1.0 - req.cost_margin_pct)
                    profit = (rev * net_margin) - s
                    total_metric += profit
                else:
                    # Default: maximize revenue
                    total_metric += rev
            return -1.0 * float(total_metric)

        # Budget equality constraint: sum(x) == target_budget
        budget_constraint = {
            "type": "eq",
            "fun": lambda x: np.sum(x) - target_budget
        }

        # Run SLSQP (Sequential Least Squares Programming)
        res = minimize(
            fun=objective_func,
            x0=x0,
            method="SLSQP",
            bounds=bounds,
            constraints=[budget_constraint],
            options={"maxiter": 1000, "ftol": 1e-6}
        )

        optimized_spends = res.x if res.success else x0

        # Construct Channel & Summary Results
        channel_results: List[ChannelOptimizationResult] = []
        tot_curr_rev = 0.0
        tot_opt_rev = 0.0

        for idx, ch in enumerate(channels):
            curr_s = current_spend_dict[ch]
            rec_s = float(optimized_spends[idx])
            curr_rev = float(self.curve_fitter.predict(ch, curr_s))
            rec_rev = float(self.curve_fitter.predict(ch, rec_s))

            tot_curr_rev += curr_rev
            tot_opt_rev += rec_rev

            curr_mroas = float(self.curve_fitter.marginal_roas(ch, curr_s))
            opt_mroas = float(self.curve_fitter.marginal_roas(ch, rec_s))

            spend_delta = rec_s - curr_s
            spend_delta_pct = (spend_delta / curr_s) if curr_s > 0 else 0.0

            channel_results.append(ChannelOptimizationResult(
                channel=ch,
                current_spend=round(curr_s, 2),
                recommended_spend=round(rec_s, 2),
                spend_delta=round(spend_delta, 2),
                spend_delta_pct=round(spend_delta_pct * 100, 2),
                predicted_current_revenue=round(curr_rev, 2),
                predicted_recommended_revenue=round(rec_rev, 2),
                revenue_delta=round(rec_rev - curr_rev, 2),
                current_roas=round(curr_rev / max(curr_s, 1.0), 2),
                projected_roas=round(rec_rev / max(rec_s, 1.0), 2),
                current_marginal_roas=round(curr_mroas, 2),
                projected_marginal_roas=round(opt_mroas, 2)
            ))

        rev_lift = tot_opt_rev - tot_curr_rev
        rev_lift_pct = (rev_lift / max(tot_curr_rev, 1.0)) * 100

        summary = OptimizationSummary(
            total_current_spend=round(total_current_spend, 2),
            total_recommended_spend=round(target_budget, 2),
            total_predicted_current_revenue=round(tot_curr_rev, 2),
            total_predicted_recommended_revenue=round(tot_opt_rev, 2),
            revenue_lift=round(rev_lift, 2),
            revenue_lift_pct=round(rev_lift_pct, 2),
            overall_current_roas=round(tot_curr_rev / max(total_current_spend, 1.0), 2),
            overall_projected_roas=round(tot_opt_rev / max(target_budget, 1.0), 2),
            objective=req.objective,
            channel_allocations=channel_results
        )

        return summary

