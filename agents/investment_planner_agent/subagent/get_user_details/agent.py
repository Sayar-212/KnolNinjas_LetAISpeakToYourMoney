from google.adk.agents import LlmAgent
from pydantic import BaseModel, Field
from typing import Dict, List

class UserDetails(BaseModel):
    name: str = Field(
        description="User's full name. (Optional)"
    )
    user_id: str = Field(
        description="Unique identifier for the user. (Optional: internal use only)"
    )
    risk_tolerance: str = Field(
        description="User's risk tolerance or appetite: 'conservative', 'moderate', or 'aggressive'. Defaults based on profile if unspecified."
    )
    investment_horizon: int = Field(
        description="Planned investment duration in years."
    )
    profession: str = Field(
        description="User's profession. (Optional, e.g., student, unemployed)"
    )
    income: float = Field(
        description="User's annual income in local currency."
    )
    age: int = Field(
        description="User's age in years."
    )
    investment_goals: List[str] = Field(
        description="Financial goals such as retirement, wealth accumulation, or buying a house."
    )
    current_portfolio: Dict[str, float] = Field(
        description="User's current investment holdings mapped by asset name and amount. Optional. If not provided Explicitly assume no current portfolio."
    )
    liquidity_needs: float = Field(
        description="Immediate cash requirement or expected short-term expense in local currency. If not provided assume from user profile."
    )
    net_worth: float = Field(
        description="Net Worth of the User. If not specified assume from user profile."
    )


user_details_agent = LlmAgent(
    name="get_user_details",
    model="gemini-2.0-flash",
    description="Asks and collects relevant user data with structured output.",
    instruction="""You are an query agent who asks the user to provide user details if not provided already.
    DETAILS:
    - Name (Optional)
    - User ID (Optional: internal use only)
    - risk_tolerance
    - investment_horizon
    - Profession
    - Income (LPA)
    - Age
    - Investment Goals
    - Current Portfolio (Optional: If not provided Explicitly assume no current portfolio.)
    - Liquidity Needs (Optional: If not provided assume from user profile.)
    - Net Worth (Net Worth of the User. If not specified assume from user profile.)

    After collecting the necessary details keep it in a concise manner.

    IMPORTANT:
    Your response MUST be valid JSON matching this structure:
        {
            "name": "",
            "user_id": "",
            "risk_tolerance": "moderate",
            "investment_horizon": 5,
            "profession": "",
            "income": 0.0,
            "age": 0,
            "investment_goals": [],
            "current_portfolio": {},
            "liquidity_needs": 0.0,
            "net_worth": 0.0
        }

       DO NOT include any explanations or additional text outside the JSON response.
    """,
    # output_schema=UserDetails,
    output_key="user_details",
)