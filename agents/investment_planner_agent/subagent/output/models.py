# models.py
from pydantic import BaseModel, Field
from typing import List, Literal

AssetType = Literal[
    "stock",
    "ETF",
    "REIT",
    "bond",
    "mutual fund",
    "crypto",
    "commodity",
    "index",
    "treasury",
    "real estate",
    "CD",  # Certificate of Deposit
    "cash",
    "other"
]


class UserDetails(BaseModel):
    name: str
    age: int
    profession: str
    income: float
    net_worth: float
    risk_tolerance: Literal["low", "moderate", "high"]
    investment_horizon: int
    liquidity_needs: float
    investment_goals: List[str]


class InvestmentOpportunity(BaseModel):
    name: str
    symbol: str
    type: AssetType
    expected_return: float
    risk_score: float


class InitialAllocation(BaseModel):
    symbol: str
    amount: float


class InitialPortfolio(BaseModel):
    cash_reserve: float
    allocations: List[InitialAllocation]


class OptimizedAllocation(BaseModel):
    name: str
    symbol: str
    type: AssetType
    optimized_percentage: float
    reason: str = Field(..., alias="optimization_reason")


class UpdatedAllocation(BaseModel):
    symbol: str
    percentage: float


class PortfolioReview(BaseModel):
    summary: str
    recommendations: List[str]
    updated_allocations: List[UpdatedAllocation]


class FinalPortfolioOutput(BaseModel):
    user_details: UserDetails
    investment_opportunities: List[InvestmentOpportunity]
    initial_portfolio: InitialPortfolio
    optimized_portfolio: List[OptimizedAllocation]
    portfolio_review: PortfolioReview
