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
from agent import FinancialAnalysisAgent
from agent_executor import FinancialAnalysisAgentExecutor
from dotenv import load_dotenv


load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MissingAPIKeyError(Exception):
    """Exception for missing API key."""
    pass


@click.command()
@click.option('--host', default='localhost', help='Host to bind the server to')
@click.option('--port', default=9001, help='Port to bind the server to')
def main(host, port):
    try:
        # Check for API key only if Vertex AI is not configured
        if not os.getenv('GOOGLE_GENAI_USE_VERTEXAI') == 'TRUE':
            if not os.getenv('GOOGLE_API_KEY'):
                raise MissingAPIKeyError(
                    'GOOGLE_API_KEY environment variable not set and GOOGLE_GENAI_USE_VERTEXAI is not TRUE.'
                )

        # Define agent capabilities
        capabilities = AgentCapabilities(
            streaming=True,
            supports_images=False,  # This agent processes text queries only
            supports_structured_output=True  # Returns structured JSON data
        )
        
        # Define the primary skill for market analysis
        market_analysis_skill = AgentSkill(
            id='market_predictive_analysis',
            name='Market & Predictive Analysis',
            description='Performs comprehensive market analysis using real-time Google search data, analyzes historical trends, and provides personalized financial recommendations based on user financial profile.',
            tags=['market-analysis', 'financial-planning', 'predictive-analysis', 'google-search', 'affordability'],
            examples=[
                'Should I buy a car next month?',
                'Is this a good time to invest in gold?',
                'Can I afford to buy a house this year?',
                'What are the market trends for smartphones?',
                'Should I wait to buy a laptop or buy now?'
            ],
        )
        
        # Additional skill for investment analysis
        investment_analysis_skill = AgentSkill(
            id='investment_feasibility',
            name='Investment Feasibility Analysis',
            description='Analyzes investment opportunities, market timing, and provides data-driven recommendations based on current financial position.',
            tags=['investment', 'feasibility', 'market-timing', 'financial-health'],
            examples=[
                'Is it a good time to invest in mutual funds?',
                'Should I increase my stock portfolio?',
                'Analyze cryptocurrency investment opportunities'
            ],
        )

        # Additional skill for purchase planning
        purchase_planning_skill = AgentSkill(
            id='purchase_planning',
            name='Smart Purchase Planning',
            description='Evaluates purchase decisions by analyzing market trends, pricing patterns, and personal financial capacity to recommend optimal timing.',
            tags=['purchase-planning', 'market-trends', 'affordability', 'timing'],
            examples=[
                'When should I buy a new phone?',
                'Is this a good time to purchase property?',
                'Should I wait for festival sales?'
            ],
        )

        # Create agent card with comprehensive metadata
        agent_card = AgentCard(
            name='Smart Financial Advisor',
            description='An intelligent financial analysis agent that combines real-time market research with personalized financial assessment. Uses Google search for current pricing, analyzes 10-15 year historical trends, and provides data-driven recommendations based on your financial profile including income, savings, investments, and monthly obligations.',
            url=f'http://{host}:{port}/',
            version='1.0.0',
            defaultInputModes=['text', 'text/plain'],  # Support text queries
            defaultOutputModes=['application/json', 'text/plain'],  # Return structured data or text
            capabilities=capabilities,
            skills=[market_analysis_skill, investment_analysis_skill, purchase_planning_skill],
        )
        
        # Set up request handler with the financial analysis executor
        request_handler = DefaultRequestHandler(
            agent_executor=FinancialAnalysisAgentExecutor(),
            task_store=InMemoryTaskStore(),
        )
        
        # Create the A2A server application
        server = A2AStarletteApplication(
            agent_card=agent_card, 
            http_handler=request_handler
        )
        
        # Start the server
        import uvicorn
        
        logger.info(f"Starting Smart Financial Advisor on {host}:{port}")
        logger.info("Agent capabilities:")
        logger.info("- Real-time market data research via Google Search")
        logger.info("- Comprehensive historical trend analysis (10-15 years)")
        logger.info("- Personalized affordability assessment")
        logger.info("- Data-driven purchase and investment recommendations")
        logger.info("- Structured JSON output with detailed analysis")
        logger.info(f"Agent card available at: http://{host}:{port}/.well-known/agent")
        logger.info(f"Tasks endpoint available at: http://{host}:{port}/tasks")
        
        # Display user financial profile being used
        from agent import USER_FINANCIAL_DATA
        logger.info("Current user financial profile:")
        logger.info(f"- Monthly Income: ₹{USER_FINANCIAL_DATA['income']:,}")
        logger.info(f"- Monthly EMI: ₹{USER_FINANCIAL_DATA['emi']:,}")
        logger.info(f"- Disposable Income: ₹{USER_FINANCIAL_DATA['income'] - USER_FINANCIAL_DATA['emi']:,}")
        logger.info(f"- Total Assets: ₹{sum(v for k, v in USER_FINANCIAL_DATA.items() if k not in ['income', 'emi']):,}")
        
        uvicorn.run(server.build(), host=host, port=port)
        
    except MissingAPIKeyError as e:
        logger.error(f'Configuration Error: {e}')
        logger.error('Please set GOOGLE_API_KEY or configure GOOGLE_GENAI_USE_VERTEXAI=TRUE')
        exit(1)
    except Exception as e:
        logger.error(f'An error occurred during server startup: {e}')
        exit(1)


if __name__ == '__main__':
    main()