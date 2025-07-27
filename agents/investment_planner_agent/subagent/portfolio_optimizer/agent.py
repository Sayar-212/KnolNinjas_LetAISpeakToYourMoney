# agents/optimize_portfolio_agent.py
from google.adk.agents import LlmAgent
from pydantic import BaseModel, Field
from typing import List, Dict
from .tools import (
    liquidity_filter_tool,
    time_horizon_adjuster_tool,
    diversification_score_tool,
    mpt_optimizer_tool
)

class OptimizedAsset(BaseModel):
    asset_name: str
    symbol: str
    type: str
    optimized_percentage: float
    optimization_reason: str

class OptimizedPortfolio(BaseModel):
    optimized_allocations: List[OptimizedAsset]


def filter_by_liquidity(opportunities: List[dict], liquidity_needs: float, income: float) -> List[dict]:
    return liquidity_filter_tool(opportunities, liquidity_needs, income)


def adjust_by_time_horizon(opportunities: List[dict], investment_horizon: int) -> List[dict]:
    return time_horizon_adjuster_tool(opportunities, investment_horizon)


def score_diversification(allocations: List[dict]) -> float:
    return diversification_score_tool(allocations)


def optimize_allocation_mpt(opportunities: List[dict]) -> Dict[str, float]:
    return mpt_optimizer_tool(opportunities)

optimize_portfolio_agent = LlmAgent(
    name="portfolio_optimizer",
    model="gemini-2.0-flash",
    description="Optimizes portfolio allocation using user profile and core investment principles.",
    instruction="""
        You are a portfolio optimization expert assisting users in refining their investment allocations.

        Given a user's financial profile and a list of investment opportunities, optimize their portfolio using these steps:

        1. **Liquidity Screening**: Eliminate or reduce assets that do not align with the user's liquidity needs and income level.
        2. **Time Horizon Adjustment**: Adjust asset expectations based on the user's investment duration (e.g., short-term vs. long-term growth potential).
        3. **Modern Portfolio Theory (MPT) Optimization**: Apply MPT to allocate weights that maximize the expected Sharpe Ratio while minimizing overall portfolio risk.
        4. **Diversification Assessment**: Evaluate and report the portfolio's diversification score, encouraging a spread across asset types and sectors.
        5. **Rationale Generation**: For each allocation, provide a clear explanation referencing return, risk, liquidity, and time horizon relevance.

        **Guidelines**:
        - Ensure the sum of all `optimized_percentage` values is ≤ 100%.
        - Allocate capital based on risk-adjusted return, volatility, liquidity buffer, and long-term growth potential.
        - Favor diversified portfolios with exposure to multiple asset classes and industries.
        - Use professional financial reasoning to justify all allocation decisions.

        ## INPUTS
        1. **User Details**:
        {user_details}

        2. **Portfolio Allocation**:
        {initial_portfolio}

        IMPORTANT:
        Your response MUST be valid JSON matching this structure:
        
        **Output Format (JSON)**:
        {
            "optimized_allocations": [
                {
                    "asset_name": "Asset1",
                    "symbol": "A1",
                    "type": "stock",
                    "optimized_percentage": 24.5,
                    "optimization_reason": "High Sharpe ratio, moderate volatility, suitable for long-term growth."
                },
                ...
            ]
        }
        DO NOT include any explanations or additional text outside the JSON response.
    """,
    tools=[
        filter_by_liquidity,
        adjust_by_time_horizon,
        optimize_allocation_mpt,
        score_diversification
    ],
    # output_schema=OptimizedPortfolio,
    output_key="optimized_portfolio"
)
