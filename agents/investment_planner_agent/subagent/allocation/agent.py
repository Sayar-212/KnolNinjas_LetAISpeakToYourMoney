from google.adk.agents import LlmAgent
from pydantic import BaseModel, Field
from typing import Dict

class PortfolioAllocation(BaseModel):
    allocations: Dict[str, float] = Field(description="Allocated amount for each asset (symbol: amount)")
    cash_reserve: float = Field(description="Remaining unallocated cash after investment")

allocate_agent = LlmAgent(
    name="allocation",
    model="gemini-2.0-flash",
    description="Allocates capital across selected investments based on user profile and risk preference.",
    instruction="""
    You are a portfolio allocation agent.

    Your task is to distribute a user's available investment capital across a set of investment opportunities, based on their personal profile and risk tolerance.

    You will receive:
    - User details including income, liquidity_needs, risk_tolerance, goals, and investment_horizon
    - A list of investment opportunities, each with a name, asset type, expected return, and risk_score (0.0 to 1.0)

    ## INPUTS
    1. **User Details**:
    {user_details}

    2. **Investment Opportunities**:
    {investment_opportunities}

    ### Step-by-step INSTRUCTION:

    1. **Compute investable capital**:
    available_funds = income - liquidity_needs
    Ensure liquidity_needs is reserved as cash_reserve if income is insufficient.

    2. **Allocate based on risk_tolerance**:
    Use the risk_score of each asset to decide how much capital to allocate:
    - **Conservative**: Allocate ~70-80%% to low-risk assets (risk_score < 0.4), ~20-30%% to moderate-risk (0.4-0.7). Avoid high-risk assets.
    - **Moderate**: Mix of ~50%% moderate-risk (0.4-0.7), 30%% low-risk, 20%% high-risk (> 0.7).
    - **Aggressive**: Allocate ≥60%% to high-risk assets, remaining to moderate or low.

    3. **Respect asset diversity**:
    Allocate across different asset types (stocks, crypto, ETFs) without overconcentration in a single asset.

    4. **Return result as strict JSON**:
    {
        "allocations": {
        "AAPL": 5000,
        "ETH": 3000
        },
        "cash_reserve": 2000
    }

    - Use realistic whole or rounded values (no micro-cents).
    - DO NOT include explanations or extra text. Only return valid JSON conforming to the output_schema.
    """,
    # output_schema=PortfolioAllocation,
    output_key="initial_portfolio",
)
