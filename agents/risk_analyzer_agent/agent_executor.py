import json
import logging
from typing import Any, Dict

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import (
    DataPart,
    Part,
    TextPart,
    TaskState,
)
from a2a.utils import (
    new_agent_parts_message,
    new_agent_text_message,
    new_task,
)
from agent import risk_analyzer

logger = logging.getLogger(__name__)

class RiskAnalyzerExecutor(AgentExecutor):
    """AgentExecutor for the Risk Analyzer Agent"""

    def __init__(self):
        # Initialize the investment planner agent
        self.agent = risk_analyzer()
    
    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        user_input = context.get_user_input()
        task = context.current_task

        # Create a new task if none exists
        if not task:
            task = new_task(context.message)
            await event_queue.enqueue_event(task)

        updater = TaskUpdater(event_queue, task.id, task.contextId)

        try:
            # Inform user that processing has started
            await updater.update_status(
                TaskState.working,
                new_agent_text_message(
                    self.agent.get_processing_message(),
                    task.contextId,
                    task.id,
                ),
            )

            # Stream from the investment planner agent
            async for item in self.agent.stream(user_input, task.contextId):
                if not item.get('is_task_complete', False):
                    # Intermediate updates
                    updates = item.get('updates', '')
                    await updater.update_status(
                        TaskState.working,
                        new_agent_text_message(
                            updates,
                            task.contextId,
                            task.id,
                        ),
                    )
                    continue

                # Final response
                content = item.get('content')
                if content is None:
                    await updater.update_status(
                        TaskState.failed,
                        new_agent_text_message(
                            'Risk Analysis failed: no content received',
                            task.contextId,
                            task.id,
                        ),
                        final=True,
                    )
                    return

                # Try parsing JSON for structured output
                try:
                    parsed = json.loads(content) if isinstance(content, str) else content
                    # Add as structured data artifact
                    await updater.add_artifact(
                        [Part(root=DataPart(data=parsed))],
                        name='risk_analyze',
                    )
                    # Summarize for user
                    summary = self._format_summary(parsed)
                    await updater.update_status(
                        TaskState.completed,
                        new_agent_text_message(
                            summary,
                            task.contextId,
                            task.id,
                        ),
                        final=True,
                    )
                except (json.JSONDecodeError, TypeError):
                    # Return raw text if not JSON
                    await updater.add_artifact(
                        [Part(root=TextPart(text=str(content)))],
                        name='investment_plan_text',
                    )
                    await updater.update_status(
                        TaskState.completed,
                        new_agent_text_message(
                            str(content),
                            task.contextId,
                            task.id,
                        ),
                        final=True,
                    )
                break

        except Exception as e:
            logger.error(f"Error during investment planning: {e}")
            await updater.update_status(
                TaskState.failed,
                new_agent_text_message(
                    f'Risk Analyzing failed: {str(e)}',
                    task.contextId,
                    task.id,
                ),
                final=True,
            )

    def _format_summary(self, plan: Dict[str, Any]) -> str:
        """Summarize the normalized risk analysis result for the user."""
        try:
            # Extract the normalized risk output
            risk_output = plan.get("output_risk_analysis", {})

            recommendation = risk_output.get("recommendation", "No recommendation provided")
            justifications = risk_output.get("justification", [])

            summary = f"Recommendation: **{recommendation}**"

            if justifications and isinstance(justifications, list):
                summary += "\n\n🔍 Justifications:\n"
                for i, reason in enumerate(justifications, 1):
                    summary += f"{i}. {reason}\n"

            return summary.strip()

        except Exception as e:
            logger.warning(f"Error formatting summary: {e}")
            return "Risk analysis completed. See artifact for full details."

    async def cancel(self, request: RequestContext, event_queue: EventQueue):
        # Cancellation not supported for investment planning
        return None