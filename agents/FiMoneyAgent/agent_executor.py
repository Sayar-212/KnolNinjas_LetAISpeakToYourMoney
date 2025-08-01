from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import (
    Part,
    TaskState,
    TextPart,
    DataPart,
    UnsupportedOperationError,
)
from a2a.utils import new_agent_text_message, new_task, new_agent_parts_message
from a2a.utils.errors import ServerError
import json


from agent import FiMoneyAgent


class FiMoneyAgentExecutor(AgentExecutor):
    def __init__(self):
        self.agent = FiMoneyAgent()

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        query = context.get_user_input()
        task = context.current_task

        # This agent always produces Task objects. If this request does
        # not have current task, create a new one and use it.
        if not task:
            task = new_task(context.message)
            await event_queue.enqueue_event(task)
        updater = TaskUpdater(event_queue, task.id, task.context_id)
        # invoke the underlying agent, using streaming results. The streams
        # now are update events.
        async for item in self.agent.stream(query, task.context_id):
            is_task_complete = item["is_task_complete"]
            artifacts = None
            if not is_task_complete:
                await updater.update_status(
                    TaskState.working,
                    new_agent_text_message(item["updates"], task.context_id, task.id),
                )
                continue
            # If the response is a dictionary, assume its a form
            if isinstance(item["content"], dict):
                # Verify it is a valid form
                if (
                    "response" in item["content"]
                    and "result" in item["content"]["response"]
                ):
                    data = json.loads(item["content"]["response"]["result"])
                    await updater.update_status(
                        TaskState.input_required,
                        new_agent_parts_message(
                            [Part(root=DataPart(data=data))],
                            task.context_id,
                            task.id,
                        ),
                        final=True,
                    )
                    continue
                await updater.update_status(
                    TaskState.failed,
                    new_agent_text_message(
                        "Reaching an unexpected state",
                        task.context_id,
                        task.id,
                    ),
                    final=True,
                )
                break
            # Emit the appropriate events
            await updater.add_artifact(
                [Part(root=TextPart(text=item["content"]))], name="form"
            )
            await updater.complete()
            break

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise ServerError(error=UnsupportedOperationError())
