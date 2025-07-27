import logging
import os

import click

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)
from agent import investment_planner
from agent_executor import InvestmentPlannerAgentExecutor
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MissingAPIKeyError(Exception):
    """Exception for missing API key."""

    pass

@click.command()
@click.option('--host', default='localhost')
@click.option('--port', default=10002)

def main(host, port):
    try:
        # Check for API key only if Vertex AI is not configured
        if not os.getenv('GOOGLE_GENAI_USE_VERTEXAI') == 'TRUE':
            if not os.getenv('GOOGLE_API_KEY'):
                raise MissingAPIKeyError(
                    'GOOGLE_API_KEY environment variable not set and GOOGLE_GENAI_USE_VERTEXAI is not TRUE.'
                )

        capabilities = AgentCapabilities(streaming=True)
        skill_user_details = AgentSkill(
            id='get user details',
            name='User Details Scrapping Tool',
            description='Scrapes the required user details for investment planning from user prompt or by asking for the details.',
            tags=['user details', 'get user details', 'scrape user details', "investment planning"],
            examples=[
                '''I am Alisson Burgers. I am an employee in a super market and I earn 5000 Rs per month. I want to buy a small appartment in 10 years.
                I have moderate risk tolerance and i am 26 years old. I have never invested before and i always need some liquidity.'''
            ],
        )
        skill_web_search = AgentSkill(
            id="web_search",
            name="Investment Opportunity Finder",
            description="Finds and curates investment opportunities using real-time financial APIs and search tools based on user's profile.",
            tags=["investment ideas", "stocks", "crypto", "asset discovery", "web search", "financial planning"],
            examples=[
                """Find some good investment options for a 23-year-old college student with a part-time job and long investment horizon."""
            ]
        )
        skill_allocate = AgentSkill(
            id="allocation",
            name="Capital Allocator",
            description="Distributes investable income across selected assets based on user's risk tolerance and goals.",
            tags=["asset allocation", "risk-based distribution", "capital allocation", "portfolio build"],
            examples=[
                """Distribute my income across AAPL and ETH. I'm 30, earn 7 LPA, and have a conservative risk profile."""
            ]
        )
        skill_optimize = AgentSkill(
            id="portfolio_optimizer",
            name="Portfolio Optimizer",
            description="Optimizes portfolio allocations using liquidity, time horizon, diversification, and Modern Portfolio Theory.",
            tags=["portfolio optimization", "MPT", "liquidity", "long-term investing", "Sharpe ratio"],
            examples=[
                """Optimize my portfolio of AAPL, ETH, and BND using MPT and my financial profile: age 40, moderate risk, 10-year horizon."""
            ]
        )
        skill_review = AgentSkill(
            id="review",
            name="Portfolio Reviewer",
            description="Analyzes portfolio alignment with user goals using real-time market and economic data. Suggests improvements if needed.",
            tags=["portfolio review", "market trends", "rebalancing", "financial goals", "adjustments"],
            examples=[
                """Evaluate my portfolio of AAPL 30%, BND 20%, GOOGL 40%. I'm aiming for wealth accumulation with moderate risk tolerance."""
            ]
        )
        skill_output_normalizer = AgentSkill(
            id="output_schema",
            name="Portfolio Output Normalizer",
            description="Aggregates and normalizes output from multiple portfolio agents into A2A-compatible final output format.",
            tags=["output aggregation", "data normalizer", "final portfolio report"],
            examples=[
                """Combine user details, asset allocations, optimized portfolio, and review into a clean final output JSON."""
            ]
        )


        agent_card = AgentCard(
            name='Investment Planning Agent',
            description="""
                A comprehensive financial planning agent that guides users through the entire investment lifecycle.

                1. **User Profiling** - Collects key financial and demographic details including income, age, goals, and risk tolerance.
                2. **Opportunity Discovery** - Searches the web and financial APIs to identify investment opportunities aligned with the user's profile.
                3. **Initial Allocation** - Distributes available capital across assets based on the user's risk profile and liquidity needs.
                4. **Portfolio Optimization** - Refines the allocation using financial modeling principles such as Modern Portfolio Theory (MPT), ensuring better diversification and risk-adjusted return.
                5. **Review & Recommendation** - Evaluates the optimized portfolio using current market trends and provides final actionable suggestions or rebalancing advice.
                6. **Output Normalization** - Normalizes the final output to json format using defined output schemas for a2a compatibility.

                The pipeline ensures structured, explainable, a2a compatibility, and market-aware investment planning tailored to individual user needs.
            """,
            url=f'http://{host}:{port}/',
            version='1.0.0',
            defaultInputModes=investment_planner.SUPPORTED_CONTENT_TYPES,
            defaultOutputModes=investment_planner.SUPPORTED_CONTENT_TYPES,
            capabilities=capabilities,
            skills=[skill_user_details, skill_web_search, skill_allocate, skill_optimize, skill_review, skill_output_normalizer],
        )
        request_handler = DefaultRequestHandler(
            agent_executor=InvestmentPlannerAgentExecutor(),
            task_store=InMemoryTaskStore(),
        )
        server = A2AStarletteApplication(
            agent_card=agent_card, http_handler=request_handler
        )
        import uvicorn

        uvicorn.run(server.build(), host=host, port=port)
    except MissingAPIKeyError as e:
        logger.error(f'Error: {e}')
        exit(1)
    except Exception as e:
        logger.error(f'An error occurred during server startup: {e}')
        exit(1)


if __name__ == '__main__':
    main()
