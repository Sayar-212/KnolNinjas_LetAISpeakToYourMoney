from typing import Callable
import httpx
from a2a.client import A2AClient
from a2a.types import (
    AgentCard,
    Task,
    Message,
    TextPart,
    MessageSendParams,
    TaskStatusUpdateEvent,
    TaskArtifactUpdateEvent,
    SendMessageRequest,
    SendStreamingMessageRequest,
    JSONRPCErrorResponse,
    Role,
    Part,
)
from uuid import uuid4

TaskCallbackArg = Task | TaskStatusUpdateEvent | TaskArtifactUpdateEvent
TaskUpdateCallback = Callable[[TaskCallbackArg, AgentCard], Task]


class RemoteAgentConnections:
    """A class to hold the connections to the remote agents."""

    def __init__(self, client: httpx.AsyncClient, agent_card: AgentCard):
        self.agent_client = A2AClient(client, agent_card)
        self.card = agent_card
        self.pending_tasks = set()

    def get_agent(self) -> AgentCard:
        return self.card

    async def send_message(
        self,
        request: MessageSendParams,
        task_callback: TaskUpdateCallback | None,
    ) -> Task | Message | None:
        if self.card.capabilities.streaming:
            task = None
            async for response in self.agent_client.send_message_streaming(
                SendStreamingMessageRequest(id=str(uuid4()), params=request)
            ):
                if isinstance(response.root, JSONRPCErrorResponse):
                    error_message = response.root.error.message
                    return Message(
                        parts=[
                            Part(
                                root=TextPart(
                                    text=error_message if error_message else ""
                                )
                            )
                        ],
                        role=Role.agent,
                        message_id=str(uuid4()),
                    )
                # In the case a message is returned, that is the end of the interaction.
                event = response.root.result
                if isinstance(event, Message):
                    return event

                if task_callback and event:
                    task = task_callback(event, self.card)

                # Otherwise we are in the Task + TaskUpdate cycle.
                if task_callback and event:
                    task = task_callback(event, self.card)

                if isinstance(event, TaskStatusUpdateEvent) and event.final:
                    break
            return task

        else:  # Non-streaming
            response = await self.agent_client.send_message(
                SendMessageRequest(id=str(uuid4()), params=request)
            )
            if isinstance(response.root, JSONRPCErrorResponse):
                error_message = response.root.error.message
                return Message(
                    parts=[
                        Part(root=TextPart(text=error_message if error_message else ""))
                    ],
                    role=Role.agent,
                    message_id=str(uuid4()),
                )

            if isinstance(response.root.result, Message):
                return response.root.result

            if task_callback:
                task_callback(response.root.result, self.card)
            return response.root.result
