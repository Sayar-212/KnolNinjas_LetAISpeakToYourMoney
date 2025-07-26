import base64
import json
from uuid import uuid4

import httpx

from a2a.client import A2ACardResolver
from a2a.types import (
    AgentCard,
    DataPart,
    Message,
    MessageSendConfiguration,
    MessageSendParams,
    Part,
    Task,
    TaskState,
    TextPart,
    Role,
)
from google.adk import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.agents.readonly_context import ReadonlyContext
from google.adk.tools.tool_context import ToolContext
from google.genai import types

from remote_agent_connections import RemoteAgentConnections, TaskUpdateCallback


class HostAgent:
    """The host agent.

    This is the agent responsible for choosing which remote agents to send
    tasks to and coordinate their work.
    """

    def __init__(
        self,
        remote_agent_addresses: list[str],
        httpx_client: httpx.AsyncClient,
        task_callback: TaskUpdateCallback | None = None,
    ):
        self.remote_agent_addresses = remote_agent_addresses
        self.task_callback = task_callback
        self.httpx_client = httpx_client
        self.remote_agent_connections: dict[str, RemoteAgentConnections] = {}
        self.cards: dict[str, AgentCard] = {}

    async def get_addresses(self):
        for address in self.remote_agent_addresses:
            card_resolver = A2ACardResolver(
                httpx_client=self.httpx_client, base_url=address
            )
            card = await card_resolver.get_agent_card()

            remote_connection = RemoteAgentConnections(self.httpx_client, card)

            self.remote_agent_connections[card.name] = remote_connection
            self.cards[card.name] = card

        self.agents = "\n".join(json.dumps(ra) for ra in self.list_remote_agents())

    def register_agent_card(self, card: AgentCard):
        remote_connection = RemoteAgentConnections(self.httpx_client, card)
        self.remote_agent_connections[card.name] = remote_connection
        self.cards[card.name] = card
        agent_info = []
        for ra in self.list_remote_agents():
            agent_info.append(json.dumps(ra))
        self.agents = "\n".join(agent_info)

    def create_agent(self) -> Agent:
        return Agent(
            model="gemini-2.0-flash",
            name="host_agent",
            instruction=self.root_instruction,
            before_model_callback=self.before_model_callback,
            description=(
                "This agent orchestrates the decomposition of the user request into"
                " tasks that can be performed by the child agents."
            ),
            tools=[
                self.list_remote_agents,
                self.send_message,
            ],
        )

    def root_instruction(self, context: ReadonlyContext) -> str:
        current_agent = self.check_state(context)
        return f"""You are an expert delegator that can delegate the user request to the
                appropriate remote agents.

                Discovery:
                - You can use `list_remote_agents` to list the available remote agents you
                can use to delegate the task.

                Execution:
                - For actionable requests, you can use `send_message` to interact with remote agents to take action.

                Be sure to include the remote agent name when you respond to the user.

                Please rely on tools to address the request, and don't make up the response. If you are not sure, please ask the user for more details.
                Focus on the most recent parts of the conversation primarily.

                Agents:
                {self.agents}

                Current agent: {current_agent["active_agent"]}
            """

    def check_state(self, context: ReadonlyContext):
        state = context.state
        if (
            "context_id" in state
            and "session_active" in state
            and state["session_active"]
            and "agent" in state
        ):
            return {"active_agent": f"{state['agent']}"}
        return {"active_agent": "None"}

    def before_model_callback(self, callback_context: CallbackContext, llm_request):
        state = callback_context.state
        if "session_active" not in state or not state["session_active"]:
            state["session_active"] = True

    def list_remote_agents(self):
        """List the available remote agents you can use to delegate the task."""
        if not self.remote_agent_connections:
            return []

        remote_agent_info = []
        for card in self.cards.values():
            remote_agent_info.append(
                {"name": card.name, "description": card.description}
            )
        return remote_agent_info

    async def send_message(
        self, agent_name: str, message: str, tool_context: ToolContext
    ):
        """
        Sends a task either streaming (if supported) or non-streaming.

        This will send a message to the remote agent named agent_name.

        Args:
          agent_name: The name of the agent to send the task to.
          message: The message to send to the agent for the task.
          tool_context: The tool context this method runs in.

        Yields:
          A dictionary of JSON data.
        """
        if agent_name not in self.remote_agent_connections:
            raise ValueError(f"Agent {agent_name} not found")

        # extract the state for the context
        state = tool_context.state
        print("State: ", state)

        # put the agent name in the state
        state["agent"] = agent_name

        # from the maintained list of connections fetch the client_connection
        client = self.remote_agent_connections[agent_name]
        if not client:
            raise ValueError(f"Client not available for {agent_name}")

        # extract 'task_id' 'context_id' and 'message_id' from the state
        taskId = state.get("task_id", None)
        contextId = state.get("context_id", None)
        messageId = state.get("message_id", None)

        print("taskId", taskId, "contextId", contextId, "messageId", messageId)

        task: Task
        if not messageId:
            # if no message id is given then just crate one
            messageId = str(uuid4())

        # create a user message and the message params
        request: MessageSendParams = MessageSendParams(
            message=Message(
                message_id=messageId,
                role=Role.user,
                parts=[Part(root=TextPart(text=message))],
                context_id=contextId,
                task_id=taskId,
            ),
            configuration=MessageSendConfiguration(
                accepted_output_modes=[
                    "text",
                    "text/plain",
                ],  # for now our host agent only supports text messages
            ),
        )

        # get the response
        response = await client.send_message(request, self.task_callback)
        print("response came", response)

        if response is None:
            # if no response came just return saying nothing came
            return "No response came"

        if isinstance(response, Task):
            task: Task = response
            print("response is a task")

            task_state = task.status.state
            # Assume completion unless a state returns that isn't complete
            state["session_active"] = task_state not in [
                TaskState.completed,
                TaskState.canceled,
                TaskState.failed,
                TaskState.unknown,
            ]
            if task.contextId:
                # if contextId is given save it to the state
                state["context_id"] = task.contextId

            state["task_id"] = task.id  # save task id to the state

            if task_state == TaskState.input_required:
                # Force user input back
                tool_context.actions.skip_summarization = True
                tool_context.actions.escalate = True

            elif task_state == TaskState.canceled:
                # handle cancelled tasks
                raise ValueError(f"Agent {agent_name} task {task.id} is cancelled")

            elif task_state == TaskState.failed:
                # handle failed tasks
                raise ValueError(f"Agent {agent_name} task {task.id} is failed")

            res: list[Part] = []

            if task.status.message:
                res.extend(task.status.message.parts)

            if task.artifacts:
                for artifacts in task.artifacts:
                    res.extend(artifacts.parts)

            return "\n".join(r.root.text for r in res if isinstance(r.root, TextPart))
        else:
            print("Response is not a task")

        print("response:", response)
        # then response is a Message just return it
        return response


async def convert_parts(parts: list[Part], tool_context: ToolContext):
    rval = []
    for p in parts:
        rval.append(await convert_part(p, tool_context))
    return rval


async def convert_part(part: Part, tool_context: ToolContext):
    if part.root.kind == "text":
        return part.root.text
    elif part.root.kind == "data":
        return part.root.data
    elif part.root.kind == "file":
        # Repackage A2A FilePart to google.genai Blob
        # Currently not considering plain text as files
        file_id = part.root.file.name
        file_bytes = base64.b64decode(part.root.file.bytes)
        file_part = types.Part(
            inline_data=types.Blob(mime_type=part.root.file.mimeType, data=file_bytes)
        )
        await tool_context.save_artifact(file_id or str(uuid4()), file_part)
        tool_context.actions.skip_summarization = True
        tool_context.actions.escalate = True
        return DataPart(data={"artifact-file-id": file_id})
    return f"Unknown type: {part.root.kind}"
