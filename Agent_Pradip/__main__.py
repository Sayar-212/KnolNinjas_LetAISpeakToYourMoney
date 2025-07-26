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
from agent import CSAAgent
from agent_executor import CSAAgentExecutor
from dotenv import load_dotenv


load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MissingAPIKeyError(Exception):
    """Exception for missing API key."""
    pass


@click.command()
@click.option('--host', default='localhost', help='Host to bind the server to')
@click.option('--port', default=9002, help='Port to bind the server to')
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
            supports_images=False,  # CSA processes text/JSON data only
            supports_structured_output=True  # Returns structured compliance reports
        )
        
        # Define the primary skill for compliance auditing
        compliance_audit_skill = AgentSkill(
            id='compliance_security_audit',
            name='Compliance & Security Audit',
            description='Audits outputs from other agents in the Fi MCP system to validate source trustworthiness, verify compliance with financial rules, and generate transparent trust reports for users.',
            tags=['compliance', 'security', 'audit', 'trust', 'validation', 'mcp'],
            examples=[
                'Audit this agent output: {"agent": "ReceiptProcessor", "action": "processed receipt", "sources": [...]}',
                'Validate compliance for this financial analysis result',
                'Check trust status for agent decision with these sources',
                'Generate audit report for this MCP agent output'
            ],
        )
        
        # Additional skill for source validation
        source_validation_skill = AgentSkill(
            id='source_trustworthiness_validation',
            name='Source Trustworthiness Validation',
            description='Validates the trustworthiness and reliability of sources used by other agents, checking against known trusted domains and compliance standards.',
            tags=['source-validation', 'trust-verification', 'url-checking'],
            examples=[
                'Validate these sources for trustworthiness',
                'Check if these URLs are from reliable financial institutions',
                'Verify source credibility for regulatory compliance'
            ],
        )

        # Additional skill for financial rule verification
        rule_verification_skill = AgentSkill(
            id='financial_rule_verification',
            name='Financial Rule Verification',
            description='Verifies that agent decisions comply with financial regulations and rules, cross-referencing against established compliance frameworks.',
            tags=['financial-rules', 'compliance-check', 'regulatory-verification'],
            examples=[
                'Verify compliance with these financial rule references',
                'Check if agent decision follows regulatory guidelines',
                'Validate rule adherence for financial recommendations'
            ],
        )

        # Create agent card with comprehensive metadata
        agent_card = AgentCard(
            name='CSA - Compliance & Security Agent',
            description='A specialized compliance and security agent for Project Arthasashtri that audits outputs from other agents in the Fi MCP ecosystem. Validates source trustworthiness, verifies financial rule compliance, analyzes data usage, and generates transparent trust reports to help users understand and trust agent decisions.',
            url=f'http://{host}:{port}/',
            version='1.0.0',
            defaultInputModes=['text', 'text/plain', 'application/json'],  # Support text and JSON input
            defaultOutputModes=['application/json', 'text/plain'],  # Return structured reports or text
            capabilities=capabilities,
            skills=[compliance_audit_skill, source_validation_skill, rule_verification_skill],
        )
        
        # Set up request handler with the CSA executor
        request_handler = DefaultRequestHandler(
            agent_executor=CSAAgentExecutor(),
            task_store=InMemoryTaskStore(),
        )
        
        # Create the A2A server application
        server = A2AStarletteApplication(
            agent_card=agent_card, 
            http_handler=request_handler
        )
        
        # Start the server
        import uvicorn
        
        logger.info(f"Starting CSA - Compliance & Security Agent on {host}:{port}")
        logger.info("Agent capabilities:")
        logger.info("- Fi MCP agent output auditing")
        logger.info("- Source trustworthiness validation")
        logger.info("- Financial rule compliance verification")
        logger.info("- Transparent trust report generation")
        logger.info("- JSON-structured compliance analysis")
        logger.info(f"Agent card available at: http://{host}:{port}/.well-known/agent")
        logger.info(f"Tasks endpoint available at: http://{host}:{port}/tasks")
        
        # Display supported input formats
        logger.info("Supported input formats:")
        logger.info("- Agent output JSON with fields: agent, action, decision, sources, used_fields, financial_rule_refs")
        logger.info("- Text descriptions of agent outputs for auditing")
        logger.info("- MCP agent response data for compliance checking")
        
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