from google.adk.agents import LlmAgent 
from google.adk.tools import google_search
from pydantic import BaseModel, Field
from typing import List

class InvestmentOpportunity(BaseModel):
    name: str = Field(description="Name or symbol of the asset (e.g., AAPL, BTC).")
    asset_type: str = Field(description="Type of asset: 'stock', 'crypto', 'fund', etc.")
    expected_return: float = Field(description="Estimated annual return percentage for the asset.")
    risk_score: float = Field(description="Normalized risk score between 0 (low risk) and 1 (high risk).")

class InvestmentOpportunityList(BaseModel):
    opportunities: List[InvestmentOpportunity] = Field(
        description="A curated list of investment opportunities based on the user's profile and market data."
    )

web_search_agent = LlmAgent(
    name="web_search",
    model="gemini-2.0-flash",
    description="Finds relevant investment opportunities using financial APIs and web data, filtered by user profile.",
    instruction="""
    ## TASKS
    You are a financial research agent that finds investment opportunities tailored to the user's overall profile (excluding risk_tolerance).

    Use real-time web search and financial APIs to discover suitable and trending assets (stocks, crypto, funds, etc.). When selecting investments, consider the user's:

    - Age
    - Profession
    - Income level
    - Investment horizon (in years)
    - Investment goals (e.g., retirement, wealth growth, buying a house)
    - Liquidity needs

    Choose opportunities that align generally with these attributes. For example:
    - Younger users with longer horizons may tolerate more volatile, high-growth assets.
    - Users near retirement or with short horizons may prefer more stable or income-generating assets.
    - Students or low-income users may need lower-cost or fractional options.

    Return a diverse list of assets using both the **full name** (for clarity) and **ticker symbol** (which is REQUIRED). The `ticker` must be a valid, commonly used symbol for the asset (e.g., "AAPL" for Apple Inc., "ETH" for Ethereum).

    **DO NOT apply strict risk-based allocation rules (conservative/moderate/aggressive).** Another agent will handle that.

    ## INPUTS
    {user_details}

    ## OUTPUT

    Output MUST be a valid JSON object in this format:

    {
      "opportunities": [
        {
          "name": "Apple Inc.",
          "ticker": "AAPL",
          "asset_type": "stock",
          "expected_return": 7.5,
          "risk_score": 0.3
        },
        {
          "name": "Ethereum",
          "ticker": "ETH",
          "asset_type": "crypto",
          "expected_return": 12.0,
          "risk_score": 0.75
        }
        // Add more
      ]
    }

    `ticker` is REQUIRED for each asset. Do not return any asset without a valid ticker symbol.

    Do not include any explanations or extra text. Only return the JSON that matches the output schema exactly.
    """,
    tools=[google_search],
    # output_schema=InvestmentOpportunityListWithTicker,  # Update schema if you have one
    output_key="investment_opportunities",
)

