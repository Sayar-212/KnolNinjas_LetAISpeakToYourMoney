import logging
import os

import click
from dotenv import load_dotenv

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCard, AgentCapabilities, AgentSkill

from agent_executor import RiskAnalyzerExecutor
from agent import risk_analyzer

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MissingAPIKeyError(Exception):
    """Exception for missing API key."""
    pass


@click.command()
@click.option('--host', default='localhost', help='Server host')
@click.option('--port', default=8069, help='Server port')
def main(host, port):
    try:
        # Check for API key only if Vertex AI is not configured
        if not os.getenv('GOOGLE_GENAI_USE_VERTEXAI') == 'TRUE':
            if not os.getenv('GOOGLE_API_KEY'):
                raise MissingAPIKeyError(
                    'GOOGLE_API_KEY environment variable not set and GOOGLE_GENAI_USE_VERTEXAI is not TRUE.'
                )

        capabilities = AgentCapabilities(streaming=True)

        skill_risk_analysis = AgentSkill(
            id="risk_analysis",
            name="Risk Analyzer",
            description="Evaluates investment opportunities and returns a recommendation (Invest/Skip) with justifications.",
            tags=["risk analysis", "investment", "recommendation", "portfolio", "A2A"],
            examples=[
                "Should I invest in Apple stock?",
                "Evaluate the investment risk of HDFC Bank.",
            ],
        )

        agent_card = AgentCard(
            name="Risk Analyzer Agent",
            description="""
                This agent performs end-to-end risk analysis on investment opportunities (e.g., stocks, ETFs, REITs).

                1. Analyzes historical and fundamental data from sources like yFinance, TwelveData, FMP.
                2. Provides a recommendation: **Invest** or **Skip**.
                3. Includes clear justifications for the decision.
                4. Normalizes the output into a well-structured JSON format using the RiskAnalysis schema.
            """,
            url=f"http://{host}:{port}/",
            version="1.0.0",
            defaultInputModes=risk_analyzer.SUPPORTED_CONTENT_TYPES,
            defaultOutputModes=risk_analyzer.SUPPORTED_CONTENT_TYPES,
            capabilities=capabilities,
            skills=[skill_risk_analysis],
        )

        request_handler = DefaultRequestHandler(
            agent_executor=RiskAnalyzerExecutor(),
            task_store=InMemoryTaskStore(),
        )

        server = A2AStarletteApplication(
            agent_card=agent_card,
            http_handler=request_handler,
        )

        import uvicorn
        uvicorn.run(server.build(), host=host, port=port)

    except MissingAPIKeyError as e:
        logger.error(f"Error: {e}")
        exit(1)
    except Exception as e:
        logger.error(f"An error occurred during server startup: {e}")
        exit(1)


if __name__ == "__main__":
    main()
