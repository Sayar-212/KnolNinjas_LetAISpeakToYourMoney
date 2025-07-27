from google.adk.agents import Agent
from .models import FinalPortfolioOutput

output_normalizer_agent = Agent(
    name="output",
    model="gemini-2.0-flash",
    description="Aggregates and normalizes output from five portfolio-related agents into a structured JSON format compatible with the a2a protocol.",
    instruction="""
    You are a strict data normalizer. Use the provided input keys:
    - user_details
    - investment_opportunities
    - initial_portfolio
    - optimized_portfolio
    - portfolio_review

    ## INPUT
    1. **User Details**:
    {user_details}
    2. **Investment Opportunities**:
    {investment_opportunities}
    3. **Portfolio Allocation**:
    {initial_portfolio}
    4. **Optimized Portfolio**:
    {optimized_portfolio}
    5. **Portfolio Review**:
    {portfolio_review}

    Your job is to:
    1. Parse each input and extract the expected fields using the FinalPortfolioOutput schema.
    2. Flatten any nested structures and rename keys where necessary (e.g., rename 'ticker' to 'symbol').
    3. Ensure types and structures conform exactly to the FinalPortfolioOutput model.

    Return the final object only under the `output_schema` key using the defined schema.
    Do not return extra commentary or unstructured output.
    """,
    output_schema=FinalPortfolioOutput,
    output_key="output_schema",
)
