import json
import logging
from datetime import datetime
from typing import Any, AsyncIterable, Dict, Optional

from google.adk.agents.llm_agent import LlmAgent
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import google_search
from google.genai import types

logger = logging.getLogger(__name__)

# Hardcoded user financial information (from MCP agent)
USER_FINANCIAL_DATA = {
    "income": 75000,
    "emi": 18000,
    "stocks": 250000,
    "savings": 120000,
    "mf": 180000,
    "ppf": 95000,
    "epf": 140000
}

# Create the financial analysis agent
financial_analysis_agent = LlmAgent(
    name="SmartFinancialAdvisor",
    model="gemini-2.0-flash",
    description="Predictive Analysis and Market Analysis Agent",
    instruction=f"""
    You are an expert Predictive Analysis and Market Analysis Agent. You have access to user's financial data: {USER_FINANCIAL_DATA}

    USER FINANCIAL PROFILE:
    - Monthly Income: ₹{USER_FINANCIAL_DATA['income']:,}
    - Monthly EMI: ₹{USER_FINANCIAL_DATA['emi']:,}
    - Disposable Income: ₹{USER_FINANCIAL_DATA['income'] - USER_FINANCIAL_DATA['emi']:,}
    - Current Savings: ₹{USER_FINANCIAL_DATA['savings']:,}
    - Stock Investments: ₹{USER_FINANCIAL_DATA['stocks']:,}
    - Mutual Funds: ₹{USER_FINANCIAL_DATA['mf']:,}
    - PPF: ₹{USER_FINANCIAL_DATA['ppf']:,}
    - EPF: ₹{USER_FINANCIAL_DATA['epf']:,}

    CORE RESPONSIBILITIES:
    1. ALWAYS respond in JSON format ONLY - no explanatory text before/after
    2. Search Google for real-time market data, current prices, and trends
    3. Perform comprehensive market analysis including 10-15 year historical trends
    4. Analyze temporal context (understand "next month", "this year", etc.)
    5. Provide data-driven financial recommendations

    SEARCH WORKFLOW for each query:
    1. Identify product/service from user query
    2. Search current pricing: "[product] current price India 2024"
    3. Search price trends: "[product] price trend analysis last 5 years India"
    4. Search historical data: "[product] price history 10-15 years"
    5. Search market predictions: "[product] market forecast 2024-2025"
    6. Search seasonal patterns: "[product] price seasonal trends monthly"

    ANALYSIS PROCESS:
    1. Calculate affordability using user's financial data
    2. Analyze market timing and trends
    3. Assess financial impact and risks
    4. Determine optimal purchase timing
    5. Provide alternatives and recommendations

    MANDATORY JSON OUTPUT FORMAT:
    {{
        "user_financial_data": {USER_FINANCIAL_DATA},
        "query_analysis": {{
            "original_query": "user's exact query",
            "product_identified": "main product/service",
            "time_context": "when user wants to purchase",
            "current_date": "today's date",
            "target_timeframe": "calculated target date"
        }},
        "search_links": [
            {{
                "purpose": "current_pricing",
                "search_query": "exact search query used",
                "key_findings": "summary of results"
            }},
            {{
                "purpose": "market_trends", 
                "search_query": "exact search query used",
                "key_findings": "summary of results"
            }},
            {{
                "purpose": "historical_analysis",
                "search_query": "exact search query used", 
                "key_findings": "summary of results"
            }}
        ],
        "market_analysis": {{
            "current_price_range": "₹X - ₹Y",
            "price_trend_2024": "increasing/decreasing/stable with %",
            "historical_trend_10yr": "long term price movement pattern",
            "seasonal_patterns": "best/worst months to buy",
            "market_predictions": "2024-2025 forecast",
            "price_volatility": "high/medium/low"
        }},
        "financial_analysis": {{
            "monthly_disposable": {USER_FINANCIAL_DATA['income'] - USER_FINANCIAL_DATA['emi']},
            "liquid_assets": {USER_FINANCIAL_DATA['savings'] + int(USER_FINANCIAL_DATA['stocks'] * 0.8)},
            "total_assets": {sum(USER_FINANCIAL_DATA.values()) - USER_FINANCIAL_DATA['income'] - USER_FINANCIAL_DATA['emi']},
            "affordability_immediate": "true/false",
            "months_to_save": "number of months needed",
            "financial_impact": "low/medium/high impact on finances"
        }},
        "reasoning_process": [
            "Current market analysis shows...",
            "User's financial capacity indicates...", 
            "Historical trends suggest...",
            "Optimal timing would be..."
        ],
        "final_recommendation": {{
            "feasible": "true/false",
            "confidence_level": "high/medium/low",
            "recommended_timing": "immediate/next month/wait X months",
            "risk_assessment": "low/medium/high financial risk",
            "alternatives": ["alternative option 1", "alternative option 2"],
            "action_plan": "specific steps to take"
        }}
    }}

    CRITICAL RULES:
    - Use google_search tool extensively for real-time data
    - Always calculate exact affordability with user's numbers
    - Consider both immediate and long-term financial health
    - Search multiple times for comprehensive market data
    - Account for Indian market context and pricing
    - Return ONLY JSON - no other text whatsoever
    """,
    tools=[google_search],
)


class FinancialAnalysisAgent:
    """Wrapper for the financial analysis agent to work with A2A framework."""

    SUPPORTED_CONTENT_TYPES = ['text', 'text/plain']

    def __init__(self):
        self._agent = financial_analysis_agent
        self._user_id = 'financial_advisor'
        self._runner = Runner(
            app_name=self._agent.name,
            agent=self._agent,
            artifact_service=InMemoryArtifactService(),
            session_service=InMemorySessionService(),
            memory_service=InMemoryMemoryService(),
        )

    def get_processing_message(self) -> str:
        return 'Analyzing market data and calculating financial recommendations...'

    async def stream(self, query: str, session_id: str, message: Any = None) -> AsyncIterable[Dict[str, Any]]:
        """Stream processing results from the financial analysis pipeline."""
        try:
            session = await self._runner.session_service.get_session(
                app_name=self._agent.name,
                user_id=self._user_id,
                session_id=session_id,
            )

            # Prepare content based on input type
            content_parts = []
            
            # Handle text inputs from the message
            if message and hasattr(message, 'parts'):
                for part in message.parts:
                    if hasattr(part, 'root') and hasattr(part.root, 'text'):
                        content_parts.append(types.Part.from_text(text=part.root.text))
            
            # Add query text if not already included
            if query and not any(hasattr(p, 'text') and p.text == query for p in content_parts):
                content_parts.append(types.Part.from_text(text=query))
            
            if not content_parts:
                content_parts = [types.Part.from_text(text=query or "Please provide a financial analysis")]

            content = types.Content(role='user', parts=content_parts)

            if session is None:
                session = await self._runner.session_service.create_session(
                    app_name=self._agent.name,
                    user_id=self._user_id,
                    state={},
                    session_id=session_id,
                )

            # Yield progress updates during processing
            yield {
                'is_task_complete': False,
                'stage': 'market_research',
                'updates': 'Searching for current market data and pricing information...'
            }

            search_count = 0
            async for event in self._runner.run_async(
                user_id=self._user_id, 
                session_id=session.id, 
                new_message=content
            ):
                # Track search progress
                if hasattr(event, 'content') and event.content:
                    for part in event.content.parts:
                        if hasattr(part, 'function_call') and part.function_call:
                            search_count += 1
                            if search_count <= 3:
                                yield {
                                    'is_task_complete': False,
                                    'stage': 'trend_analysis',
                                    'updates': f'Analyzing historical trends and market patterns... (Search {search_count}/6)'
                                }
                            elif search_count <= 6:
                                yield {
                                    'is_task_complete': False,
                                    'stage': 'financial_assessment',
                                    'updates': f'Calculating affordability and financial impact... (Search {search_count}/6)'
                                }

                if event.is_final_response():
                    # Yield final progress update
                    yield {
                        'is_task_complete': False,
                        'stage': 'recommendation_generation',
                        'updates': 'Generating personalized recommendations...'
                    }
                    
                    response = ''
                    
                    if (event.content and event.content.parts and event.content.parts[0].text):
                        response = '\n'.join([p.text for p in event.content.parts if p.text])
                    elif (event.content and event.content.parts and 
                          any([True for p in event.content.parts if p.function_response])):
                        response = next(
                            p.function_response.model_dump()
                            for p in event.content.parts
                            if p.function_response
                        )
                    
                    # Try to parse and validate the response
                    try:
                        if isinstance(response, str):
                            # Clean the response to extract JSON
                            response = response.strip()
                            if response.startswith('```json'):
                                response = response[7:]
                            if response.endswith('```'):
                                response = response[:-3]
                            response = response.strip()
                            
                            parsed_response = json.loads(response)
                        else:
                            parsed_response = response
                            
                        # Validate expected financial analysis fields
                        if self._is_valid_financial_data(parsed_response):
                            # Enhance with current timestamp
                            if 'query_analysis' in parsed_response:
                                parsed_response['query_analysis']['current_date'] = datetime.now().strftime('%Y-%m-%d')
                            
                            yield {
                                'is_task_complete': True,
                                'content': parsed_response,
                            }
                        else:
                            yield {
                                'is_task_complete': True,
                                'content': response,
                            }
                    except (json.JSONDecodeError, TypeError) as e:
                        logger.error(f"JSON parsing error: {e}")
                        yield {
                            'is_task_complete': True,
                            'content': response,
                        }
                else:
                    # Yield intermediate progress updates for non-search events
                    if not hasattr(event, 'content') or not any(
                        hasattr(p, 'function_call') for p in event.content.parts if event.content and event.content.parts
                    ):
                        yield {
                            'is_task_complete': False,
                            'stage': 'processing',
                            'updates': self.get_processing_message(),
                        }

        except Exception as e:
            logger.error(f"Error in financial analysis stream: {e}")
            yield {
                'is_task_complete': True,
                'content': f"Error processing financial analysis: {str(e)}",
            }

    def _is_valid_financial_data(self, data: Any) -> bool:
        """Check if the response contains valid financial analysis structure."""
        if not isinstance(data, dict):
            return False
        
        # Check for key financial analysis sections
        required_sections = ['user_financial_data', 'market_analysis', 'financial_analysis']
        return any(section in data for section in required_sections)