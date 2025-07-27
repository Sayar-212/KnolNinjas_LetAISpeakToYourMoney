from google.adk.agents import LlmAgent
from google.adk.tools import google_search
from pydantic import BaseModel, Field
from typing import List, Dict

class PortfolioReview(BaseModel):
    summary: str = Field(description="Concise evaluation of how the portfolio aligns with user goals and risk profile.")
    recommendations: List[str] = Field(description="Actionable suggestions to improve portfolio based on current trends.")
    updated_allocations: Dict[str, float] = Field(description="Adjusted portfolio weights if changes are recommended.")

review_agent = LlmAgent(
    name="review",
    model="gemini-2.0-flash",
    description="Reviews portfolio alignment using current market data and user goals.",
    instruction="""
    You are a portfolio review assistant.

    ## Task:
    Evaluate the optimized portfolio in the context of current market trends, macroeconomic factors, and the user's financial goals and risk profile.

    ## Steps:
    1. Use the search tool to gather relevant market news and economic updates.
    2. Assess how the current portfolio aligns with user-specific needs and risks.
    3. Suggest adjustments to enhance diversification, performance, or goal alignment.
    4. Modify allocations only if justified by analysis.

    ## INPUTS:
    1. **User Details**:
    {user_details}

    2. **Optimized Portfolio**:
    {optimized_portfolio}

    ## OUTPUT FORMAT (Strict JSON):
    Respond only with a valid JSON object in the structure below:

    {
    "summary": "Concise overview of portfolio alignment and key findings.",
    "recommendations": [
        "Example: Increase exposure to large-cap stocks due to improved earnings outlook.",
        "Example: Reduce bond holdings amid rising interest rates."
    ],
    "updated_allocations": {
        "AAPL": 25.0,
        "BND": 15.0,
        "GOOGL": 30.0
    }
    }

    Ensure the total of `updated_allocations` does not exceed 100%. If no changes are required, keep the original allocation and explain why.
    """,
    tools=[google_search],
    # output_schema=PortfolioReview,
    output_key="portfolio_review",
)
