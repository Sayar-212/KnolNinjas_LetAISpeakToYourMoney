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
from agent import investment_planner

logger = logging.getLogger(__name__)


class InvestmentPlannerAgentExecutor(AgentExecutor):
    """AgentExecutor for the Investment Planning Agent"""

    def __init__(self):
        # Initialize the investment planner agent
        self.agent = investment_planner()

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
                            'Investment planning failed: no content received',
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
                        name='investment_plan',
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
                    f'Investment planning failed: {str(e)}',
                    task.contextId,
                    task.id,
                ),
                final=True,
            )

    def _format_summary(self, plan: Dict[str, Any]) -> str:
        """Create a brief summary of the investment plan for user display."""
        try:
            # Example keys: allocation, optimization, recommendations
            sections = []
            if 'allocation' in plan:
                sections.append(f"Initial Allocation: {plan['allocation']}")
            if 'optimized_portfolio' in plan:
                sections.append(f"Optimized Portfolio: {plan['optimized_portfolio']}")
            if 'review' in plan:
                sections.append(f"Review Insights: {plan['review']}")
            return "Investment plan generated successfully!\n" + "\n".join(sections)
        except Exception:
            return 'Investment plan generated. See detailed output in artifact.'

    async def cancel(self, request: RequestContext, event_queue: EventQueue):
        # Cancellation not supported for investment planning
        return None
