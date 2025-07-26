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
from agent import ReceiptProcessingAgent

logger = logging.getLogger(__name__)


class ReceiptProcessingAgentExecutor(AgentExecutor):
    """Receipt Processing AgentExecutor for GPay receipt analysis."""

    def __init__(self):
        self.agent = ReceiptProcessingAgent()

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
            # Check if input contains image data for receipt processing
            has_image = self._has_image_input(context)
            
            if not has_image and not self._is_text_receipt(user_input):
                await updater.update_status(
                    TaskState.input_required,
                    new_agent_text_message(
                        "Please provide a GPay receipt image or receipt text for processing.",
                        task.contextId,
                        task.id,
                    ),
                    final=True,
                )
                return

            # Process the receipt through the agent pipeline
            await updater.update_status(
                TaskState.working,
                new_agent_text_message(
                    "Processing receipt through field extraction and insight analysis...",
                    task.contextId,
                    task.id,
                ),
            )

            # Stream responses from the receipt processing agent
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
                            'Failed to process receipt - no content received',
                            task.contextId,
                            task.id,
                        ),
                        final=True,
                    )
                    break
                
                # Try to parse as JSON for structured receipt data
                try:
                    if isinstance(content, str):
                        parsed_content = json.loads(content)
                    else:
                        parsed_content = content
                    
                    # Validate that we have the expected receipt fields
                    if self._is_valid_receipt_output(parsed_content):
                        # Return structured receipt data
                        await updater.add_artifact(
                            [Part(root=DataPart(data=parsed_content))], 
                            name='processed_receipt'
                        )
                        await updater.update_status(
                            TaskState.completed,
                            new_agent_text_message(
                                self._format_receipt_summary(parsed_content),
                                task.contextId,
                                task.id,
                            ),
                            final=True,
                        )
                    else:
                        # Return as text if not valid JSON structure
                        await updater.add_artifact(
                            [Part(root=TextPart(text=str(content)))], 
                            name='receipt_analysis'
                        )
                        await updater.complete()
                    break
                    
                except json.JSONDecodeError:
                    # Handle non-JSON responses
                    await updater.add_artifact(
                        [Part(root=TextPart(text=str(content)))], 
                        name='receipt_analysis'
                    )
                    await updater.complete()
                    break
                    
        except Exception as e:
            logger.error(f"Error processing receipt: {e}")
            await updater.update_status(
                TaskState.failed,
                new_agent_text_message(
                    f'Receipt processing failed: {str(e)}',
                    task.contextId,
                    task.id,
                ),
                final=True,
            )

    def _has_image_input(self, context: RequestContext) -> bool:
        """Check if the request contains image data."""
        if hasattr(context.message, 'parts'):
            for part in context.message.parts:
                if hasattr(part, 'root') and hasattr(part.root, 'mime_type'):
                    if part.root.mime_type and part.root.mime_type.startswith('image/'):
                        return True
        return False

    def _is_text_receipt(self, text: str) -> bool:
        """Check if text input looks like receipt data."""
        receipt_indicators = ['transaction', 'amount', 'merchant', 'upi', 'google pay', 'paid', '₹']
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in receipt_indicators)

    def _get_stage_message(self, stage: str, updates: str) -> str:
        """Generate appropriate status message based on processing stage."""
        stage_messages = {
            'field_extraction': 'Extracting fields from receipt...',
            'insight_analysis': 'Analyzing spending insights...',
            'parallel_processing': 'Running field extraction and insight analysis...',
            'merging': 'Combining extracted data and insights...',
            'processing': updates or 'Processing receipt...'
        }
        return stage_messages.get(stage, updates or 'Processing...')

    def _is_valid_receipt_output(self, data: Any) -> bool:
        """Validate that the output contains expected receipt fields."""
        if not isinstance(data, dict):
            return False
        
        expected_fields = {
            'merchant', 'amount', 'date', 'time', 
            'upi_transaction_id', 'google_transaction_id',
            'category', 'behavioral_tag', 'sentiment'
        }
        
        return all(field in data for field in expected_fields)

    def _format_receipt_summary(self, receipt_data: Dict[str, Any]) -> str:
        """Format a human-readable summary of the processed receipt."""
        merchant = receipt_data.get('merchant', 'Unknown')
        amount = receipt_data.get('amount', 'Unknown')
        category = receipt_data.get('category', 'Unknown')
        date = receipt_data.get('date', 'Unknown')
        
        return (f"Receipt processed successfully!\n"
                f"Merchant: {merchant}\n"
                f"Amount: {amount}\n"
                f"Category: {category}\n"
                f"Date: {date}\n"
                f"Full structured data available in artifact.")

    async def cancel(
        self, request: RequestContext, event_queue: EventQueue
    ) -> Task | None:
        raise ServerError(error=UnsupportedOperationError("Receipt processing cannot be cancelled"))