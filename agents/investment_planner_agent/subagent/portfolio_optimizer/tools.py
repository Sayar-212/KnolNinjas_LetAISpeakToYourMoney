import numpy as np
import pandas as pd
from typing import List, Dict
from collections import Counter
from pypfopt.efficient_frontier import EfficientFrontier
from pypfopt import expected_returns

def liquidity_filter_tool(opportunities: List[dict], liquidity_needs: float, income: float) -> List[dict]:
    buffer_ratio = liquidity_needs / income
    return [
        asset for asset in opportunities
        if not (buffer_ratio > 0.3 and asset["risk_score"] > 0.7)
    ]

def time_horizon_adjuster_tool(opportunities: List[dict], investment_horizon: int) -> List[dict]:
    for asset in opportunities:
        if investment_horizon < 3 and asset["risk_score"] > 0.5:
            asset["expected_return"] *= 0.8
        elif investment_horizon >= 5 and asset["risk_score"] > 0.5:
            asset["expected_return"] *= 1.2
    return opportunities

def diversification_score_tool(allocations: List[dict]) -> float:
    types = [a["type"] for a in allocations]
    counts = Counter(types)
    total = sum(counts.values())
    entropy = -sum((count / total) ** 2 for count in counts.values())
    max_entropy = 1 / len(counts) if counts else 0
    return round(min(entropy / max_entropy if max_entropy else 0, 1.0), 3)

def mpt_optimizer_tool(opportunities: List[dict]) -> Dict[str, float]:
    asset_names = [a["asset_name"] for a in opportunities]
    returns = np.array([a["expected_return"] / 100 for a in opportunities])
    risk_scores = np.array([a["risk_score"] for a in opportunities])
    cov_matrix = np.outer(risk_scores, risk_scores) * 0.02

    mu = expected_returns.mean_historical_return(pd.DataFrame([returns], columns=asset_names), frequency=1)
    S = pd.DataFrame(cov_matrix, columns=asset_names, index=asset_names)

    ef = EfficientFrontier(mu, S)
    raw_weights = ef.max_sharpe()
    cleaned = ef.clean_weights()

    return {k: round(v * 100, 2) for k, v in cleaned.items() if v > 0.001}
