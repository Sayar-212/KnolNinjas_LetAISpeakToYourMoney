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
from agent import ReceiptProcessingAgent
from agent_executor import ReceiptProcessingAgentExecutor
from dotenv import load_dotenv


load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MissingAPIKeyError(Exception):
    """Exception for missing API key."""
    pass


@click.command()
@click.option('--host', default='localhost', help='Host to bind the server to')
@click.option('--port', default=9000, help='Port to bind the server to')
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
            supports_images=True,  # This agent can process images
            supports_structured_output=True  # Returns structured JSON data
        )
        
        # Define the primary skill for receipt processing
        receipt_skill = AgentSkill(
            id='process_gpay_receipt',
            name='GPay Receipt Processor',
            description='Analyzes Google Pay receipts to extract structured data and financial insights including merchant, amount, transaction IDs, spending category, and behavioral patterns.',
            tags=['receipt', 'gpay', 'financial-analysis', 'ocr', 'insights'],
            examples=[
                'Analyze this GPay receipt image',
                'Extract transaction details from my Google Pay receipt',
                'Process this receipt and tell me the spending category',
                'What insights can you provide from this payment receipt?'
            ],
        )
        
        # Additional skill for text-based receipt processing
        text_analysis_skill = AgentSkill(
            id='analyze_receipt_text',
            name='Receipt Text Analyzer',
            description='Analyzes receipt text data to extract structured information and spending insights.',
            tags=['receipt', 'text-analysis', 'financial-insights'],
            examples=[
                'Analyze this receipt text: "Paid ₹250 to Zomato via UPI"',
                'Extract details from this transaction text'
            ],
        )

        # Create agent card with comprehensive metadata
        agent_card = AgentCard(
            name='Smart Receipt Processor',
            description='An intelligent agent that processes Google Pay receipts using parallel field extraction and insight analysis. Extracts structured data (merchant, amount, date, transaction IDs) and provides semantic insights (category, behavioral tags, spending sentiment).',
            url=f'http://{host}:{port}/',
            version='1.0.0',
            defaultInputModes=['text', 'text/plain', 'image/jpeg', 'image/png'],  # Support both text and images
            defaultOutputModes=['application/json', 'text/plain'],  # Return structured data or text
            capabilities=capabilities,
            skills=[receipt_skill, text_analysis_skill],
        )
        
        # Set up request handler with the receipt processing executor
        request_handler = DefaultRequestHandler(
            agent_executor=ReceiptProcessingAgentExecutor(),
            task_store=InMemoryTaskStore(),
        )
        
        # Create the A2A server application
        server = A2AStarletteApplication(
            agent_card=agent_card, 
            http_handler=request_handler
        )
        
        # Start the server
        import uvicorn
        
        logger.info(f"Starting Smart Receipt Processor on {host}:{port}")
        logger.info("Agent capabilities:")
        logger.info("- GPay receipt image processing")
        logger.info("- Parallel field extraction and insight analysis")
        logger.info("- Structured JSON output with transaction details")
        logger.info("- Financial categorization and behavioral insights")
        logger.info(f"Agent card available at: http://{host}:{port}/.well-known/agent")
        logger.info(f"Tasks endpoint available at: http://{host}:{port}/tasks")
        
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