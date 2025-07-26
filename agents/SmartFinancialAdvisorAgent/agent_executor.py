import json
import logging
from typing import Any, Dict

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import (
    DataPart,
    Part,
    Task,
    TaskState,
    TextPart,
    UnsupportedOperationError,
)
from a2a.utils import (
    new_agent_parts_message,
    new_agent_text_message,
    new_task,
)
from a2a.utils.errors import ServerError
from agent import FinancialAnalysisAgent

logger = logging.getLogger(__name__)


class FinancialAnalysisAgentExecutor(AgentExecutor):
    """Financial Analysis AgentExecutor for predictive market analysis."""

    def __init__(self):
        self.agent = FinancialAnalysisAgent()

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        user_input = context.get_user_input()
        task = context.current_task

        # Create a new task if one doesn't exist
        if not task:
            task = new_task(context.message)
            await event_queue.enqueue_event(task)
        
        updater = TaskUpdater(event_queue, task.id, task.contextId)
        
        try:
            # Validate that we have a financial query
            if not self._is_financial_query(user_input):
                await updater.update_status(
                    TaskState.input_required,
                    new_agent_text_message(
                        "Please provide a financial analysis query about products, investments, or market trends.",
                        task.contextId,
                        task.id,
                    ),
                    final=True,
                )
                return

            # Start processing the financial analysis
            await updater.update_status(
                TaskState.working,
                new_agent_text_message(
                    "Analyzing market data and performing financial assessment...",
                    task.contextId,
                    task.id,
                ),
            )

            # Stream responses from the financial analysis agent
            async for item in self.agent.stream(user_input, task.contextId, context.message):
                is_complete = item.get('is_task_complete', False)
                
                if not is_complete:
                    # Handle progress updates from different stages
                    stage = item.get('stage', 'processing')
                    status_message = self._get_stage_message(stage, item.get('updates', ''))
                    
                    await updater.update_status(
                        TaskState.working,
                        new_agent_text_message(
                            status_message, task.contextId, task.id
                        ),
                    )
                    continue
                
                # Handle final response
                content = item.get('content')
                
                if content is None:
                    await updater.update_status(
                        TaskState.failed,
                        new_agent_text_message(
                            'Failed to process financial analysis - no content received',
                            task.contextId,
                            task.id,
                        ),
                        final=True,
                    )
                    break
                
                # Try to parse as JSON for structured financial data
                try:
                    if isinstance(content, str):
                        parsed_content = json.loads(content)
                    else:
                        parsed_content = content
                    
                    # Validate that we have the expected financial analysis structure
                    if self._is_valid_financial_output(parsed_content):
                        # Return structured financial analysis data
                        await updater.add_artifact(
                            [Part(root=DataPart(data=parsed_content))], 
                            name='financial_analysis'
                        )
                        await updater.update_status(
                            TaskState.completed,
                            new_agent_text_message(
                                self._format_analysis_summary(parsed_content),
                                task.contextId,
                                task.id,
                            ),
                            final=True,
                        )
                    else:
                        # Return as text if not valid JSON structure
                        await updater.add_artifact(
                            [Part(root=TextPart(text=str(content)))], 
                            name='market_analysis'
                        )
                        await updater.complete()
                    break
                    
                except json.JSONDecodeError:
                    # Handle non-JSON responses
                    await updater.add_artifact(
                        [Part(root=TextPart(text=str(content)))], 
                        name='market_analysis'
                    )
                    await updater.complete()
                    break
                    
        except Exception as e:
            logger.error(f"Error processing financial analysis: {e}")
            await updater.update_status(
                TaskState.failed,
                new_agent_text_message(
                    f'Financial analysis failed: {str(e)}',
                    task.contextId,
                    task.id,
                ),
                final=True,
            )

    def _is_financial_query(self, text: str) -> bool:
        """Check if text input looks like a financial query."""
        financial_indicators = [
            'price', 'buy', 'purchase', 'invest', 'market', 'trend', 'analysis',
            'afford', 'cost', 'expensive', 'cheap', 'stock', 'mutual fund',
            'savings', 'budget', 'financial', 'money', 'rupees', '₹', 'car',
            'house', 'property', 'gold', 'silver', 'cryptocurrency', 'bitcoin'
        ]
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in financial_indicators)

    def _get_stage_message(self, stage: str, updates: str) -> str:
        """Generate appropriate status message based on processing stage."""
        stage_messages = {
            'market_research': 'Searching for current market data and pricing...',
            'trend_analysis': 'Analyzing historical trends and patterns...',
            'financial_assessment': 'Calculating affordability and financial impact...',
            'recommendation_generation': 'Generating personalized recommendations...',
            'processing': updates or 'Processing financial analysis...'
        }
        return stage_messages.get(stage, updates or 'Analyzing...')

    def _is_valid_financial_output(self, data: Any) -> bool:
        """Validate that the output contains expected financial analysis fields."""
        if not isinstance(data, dict):
            return False
        
        expected_sections = {
            'user_financial_data', 'query_analysis', 'market_analysis',
            'financial_analysis', 'final_recommendation'
        }
        
        return all(section in data for section in expected_sections)

    def _format_analysis_summary(self, analysis_data: Dict[str, Any]) -> str:
        """Format a human-readable summary of the financial analysis."""
        query_analysis = analysis_data.get('query_analysis', {})
        market_analysis = analysis_data.get('market_analysis', {})
        recommendation = analysis_data.get('final_recommendation', {})
        
        product = query_analysis.get('product_identified', 'Unknown product')
        price_range = market_analysis.get('current_price_range', 'Unknown')
        feasible = recommendation.get('feasible', 'Unknown')
        timing = recommendation.get('recommended_timing', 'Unknown')
        confidence = recommendation.get('confidence_level', 'Unknown')
        
        return (f"Financial Analysis Complete!\n"
                f"Product: {product}\n"
                f"Current Price Range: {price_range}\n"
                f"Feasible: {feasible}\n"
                f"Recommended Timing: {timing}\n"
                f"Confidence Level: {confidence}\n"
                f"Full structured analysis available in artifact.")

    async def cancel(
        self, request: RequestContext, event_queue: EventQueue
    ) -> Task | None:
        raise ServerError(error=UnsupportedOperationError("Financial analysis cannot be cancelled"))