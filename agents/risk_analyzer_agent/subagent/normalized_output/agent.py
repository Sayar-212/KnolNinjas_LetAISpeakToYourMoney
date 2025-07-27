from pydantic import BaseModel
from typing import List, Literal

from google.adk.agents import Agent

class RiskAnalysis(BaseModel):
    recommendation: Literal["Skip", "Invest"]
    justification: List[str]

risk_output_normalizer = Agent(
    name="risk_output_normalizer",
    model="gemini-2.0-flash",
    description="normalizes output from risk agent into a structured JSON format compatible with the a2a protocol.",
    instruction="""
    You are a strict data normalizer. Use the provided input keys:
    -risk
    ## INPUT
    **Risk Agent**:
    {risk}
    Your job is to:
    1. Parse each input and extract the expected fields using the RiskAnalysis schema.
    2. Flatten any nested structures and rename keys where necessary.
    3. Ensure types and structures conform exactly to the RiskAnalysis model.

    Return the final object only under the `output_risk_analysis` key using the defined schema.
    Do not return extra commentary or unstructured output.
    """,
    output_schema=RiskAnalysis,
    output_key="output_risk_analysis"
)
