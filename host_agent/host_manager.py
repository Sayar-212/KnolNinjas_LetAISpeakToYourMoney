import base64
import datetime
import json
import os
import uuid

from typing import Optional

import httpx

from a2a.types import (
    AgentCard,
    Artifact,
    DataPart,
    FilePart,
    FileWithBytes,
    FileWithUri,
    Message,
    Part,
    Role,
    Task,
    TaskArtifactUpdateEvent,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
    TextPart,
)
from google.adk import Runner
from google.adk.artifacts import InMemoryArtifactService
from google.adk.events.event import Event as ADKEvent
from google.adk.events.event_actions import EventActions as ADKEventActions
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.genai import types
from host_agent import HostAgent
from remote_agent_connections import (
    TaskCallbackArg,
)
from utils.agent_card import get_agent_card

from application_manager import ApplicationManager, Conversation, Event


class ADKHostManager(ApplicationManager):
    """Manages host agent, conversations, tasks and events."""

    def __init__(
        self,
        http_client: httpx.AsyncClient,
        api_key: str = "",
        uses_vertex_ai: bool = False,
    ):
        # initialize all the internal state variables
        self._conversations: list[Conversation] = []
        self._messages: list[Message] = []
        self._tasks: list[Task] = []
        self._events: dict[str, Event] = {}
        self._pending_message_ids: list[str] = []
        self._agents: list[AgentCard] = []
        self._artifact_chunks: dict[str, list[Artifact]] = {}

        # ADK services for session, memory and artifacts
        self._session_service = InMemorySessionService()
        self._artifact_service = InMemoryArtifactService()
        self._memory_service = InMemoryMemoryService()

        # host agent initialization
        self._host_agent = HostAgent([], http_client, self.task_callback)
        self._context_to_conversation: dict[str, str] = {}
        self.user_id = "test_user"
        self.app_name = "A2A"

        # handle environment api key setup
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY", "")
        self.uses_vertex_ai = (
            uses_vertex_ai
            or os.environ.get("GOOGLE_GENAI_USE_VERTEXAI", "").upper() == "TRUE"
        )

        # Set environment variables based on auth method
        if self.uses_vertex_ai:
            os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "TRUE"

        elif self.api_key:
            # Use API key authentication
            os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "FALSE"
            os.environ["GOOGLE_API_KEY"] = self.api_key

        # runner agent setup
        self._initialize_host()

        # Map of message id to task id
        self._task_map: dict[str, str] = {}
        # Map to manage 'lost' message ids until protocol level id is introduced
        self._next_id: dict[
            str, str
        ] = {}  # dict[str, str]: previous message to next message

    def _initialize_host(self):
        """Creates and sets up the ADK runner with current host agent."""
        agent = self._host_agent.create_agent()
        self._host_runner = Runner(
            app_name=self.app_name,
            agent=agent,
            artifact_service=self._artifact_service,
            session_service=self._session_service,
            memory_service=self._memory_service,
        )

    async def create_conversation(self) -> Conversation:
        """Creates a new conversation session nd returns it."""
        session = await self._session_service.create_session(
            app_name=self.app_name, user_id=self.user_id
        )
        conversation_id = session.id
        c = Conversation(conversation_id=conversation_id, is_active=True)
        self._conversations.append(c)
        return c

    def update_api_key(self, api_key: str):
        """Update the API key and reinitialize the host if needed"""
        if api_key and api_key != self.api_key:
            self.api_key = api_key

            # Only update if not using Vertex AI
            if not self.uses_vertex_ai:
                os.environ["GOOGLE_API_KEY"] = api_key
                # Reinitialize host with new API key
                self._initialize_host()

                # Map of message id to task id
                self._task_map = {}

    def sanitize_message(self, message: Message) -> Message:
        """Attempts to attach existing task context to a new message"""
        if message.contextId:
            conversation = self.get_conversation(message.contextId)
            if not conversation:
                return message
            # Check if the last event in the conversation was tied to a task.
            if conversation.messages:
                task_id = conversation.messages[-1].taskId
                if task_id and task_still_open(
                    next(
                        filter(lambda x: x and x.id == task_id, self._tasks),
                        None,
                    )
                ):
                    message.taskId = task_id
        return message

    async def process_message(self, message: Message):
        """Main message processing loop: queues, stores and passes to ADK"""
        message_id = message.message_id  # get message_id
        context_id = message.context_id or str(uuid.uuid4())  # get message context_id
        task_id = message.task_id

        if message_id:
            # append it to pending message list.. for this messages response hasn't been fully generated yet
            self._pending_message_ids.append(message_id)

        self._messages.append(message)  # append it to global message history
        conversation = self.get_conversation(context_id)  # get the current conversation
        if conversation:
            # append the message to the current conversation
            conversation.messages.append(message)

        # add user message to event log
        self.add_event(
            Event(
                id=str(uuid.uuid4()),
                actor="user",
                content=message,
                timestamp=datetime.datetime.now(datetime.timezone.utc).timestamp(),
            )
        )

        # Retrieve user's current session
        session = await self._session_service.get_session(
            app_name="A2A", user_id="test_user", session_id=context_id
        )
        if session is None:
            # for now just keep it to return
            return

        # Update state must happen in an event
        state_update: dict[str, object] = {
            "task_id": task_id,
            "context_id": context_id,
            "message_id": message_id,
        }
        # Need to upsert session state now, only way is to append an event.
        await self._session_service.append_event(
            session,
            ADKEvent(
                # id=ADKEvent.new_id(),
                author="host_agent",
                invocation_id=ADKEvent.new_id(),
                actions=ADKEventActions(state_delta=state_update),
            ),
        )

        # ADK run loop and collect agent responses
        final_event = None
        response: Message | None = None

        async for event in self._host_runner.run_async(
            user_id=self.user_id,
            session_id=context_id,
            new_message=self.adk_content_from_message(message),
        ):
            # extract the updated task_id if present
            task_id = event.actions.state_delta.get("task_id", task_id)

            # covert ADK content to internal message format
            content_message = await self.adk_content_to_message(
                event.content or types.Content(), context_id, str(task_id)
            )

            # log response as event
            self.add_event(
                Event(
                    id=event.id,
                    actor=event.author,
                    content=content_message,
                    timestamp=event.timestamp,
                )
            )
            final_event = event

        # process the final response from event if any
        if final_event:
            if final_event.actions.state_delta:
                task_id = str(
                    final_event.actions.state_delta.get("task_id", message.task_id)
                )

            if final_event.content:
                final_event.content.role = "model"
                response = await self.adk_content_to_message(
                    final_event.content, context_id, str(task_id)
                )
                self._messages.append(response)

            if conversation and response:
                conversation.messages.append(response)

        # cleanup: remove from pending once processing is complete
        if message_id and self._pending_message_ids:
            self._pending_message_ids.remove(message_id)

    def add_task(self, task: Task):
        self._tasks.append(task)

    def update_task(self, task: Task):
        for i, t in enumerate(self._tasks):
            if t.id == task.id:
                self._tasks[i] = task
                return

    def task_callback(self, task: TaskCallbackArg, agent_card: AgentCard):
        self.emit_event(task, agent_card)
        if isinstance(task, TaskStatusUpdateEvent):
            current_task = self.add_or_get_task(task)
            current_task.status = task.status
            self.attach_message_to_task(task.status.message, current_task.id)
            self.insert_message_history(current_task, task.status.message)
            self.update_task(current_task)
            return current_task
        elif isinstance(task, TaskArtifactUpdateEvent):
            current_task = self.add_or_get_task(task)
            self.process_artifact_event(current_task, task)
            self.update_task(current_task)
            return current_task
        # Otherwise this is a Task, either new or updated
        elif not any(
            filter(lambda x: x and isinstance(x, Task) and x.id == task.id, self._tasks)
        ):
            self.attach_message_to_task(task.status.message, task.id)
            self.add_task(task)
            return task
        else:
            self.attach_message_to_task(task.status.message, task.id)
            self.update_task(task)
            return task

    def emit_event(self, task: TaskCallbackArg, agent_card: AgentCard):
        content = None
        context_id = task.contextId
        if isinstance(task, TaskStatusUpdateEvent):
            if task.status.message:
                content = task.status.message
            else:
                content = Message(
                    parts=[Part(root=TextPart(text=str(task.status.state)))],
                    role=Role.agent,
                    message_id=str(uuid.uuid4()),
                    context_id=context_id,
                    task_id=task.taskId,
                )
        elif isinstance(task, TaskArtifactUpdateEvent):
            content = Message(
                parts=task.artifact.parts,
                role=Role.agent,
                message_id=str(uuid.uuid4()),
                context_id=context_id,
                task_id=task.taskId,
            )
        elif task.status and task.status.message:
            content = task.status.message
        elif task.artifacts:
            parts = []
            for a in task.artifacts:
                parts.extend(a.parts)
            content = Message(
                parts=parts,
                role=Role.agent,
                message_id=str(uuid.uuid4()),
                task_id=task.id,
                context_id=context_id,
            )
        else:
            content = Message(
                parts=[Part(root=TextPart(text=str(task.status.state)))],
                role=Role.agent,
                message_id=str(uuid.uuid4()),
                task_id=task.id,
                context_id=context_id,
            )
        if content:
            self.add_event(
                Event(
                    id=str(uuid.uuid4()),
                    actor=agent_card.name,
                    content=content,
                    timestamp=datetime.datetime.utcnow().timestamp(),
                )
            )

    def attach_message_to_task(self, message: Message | None, task_id: str):
        if message:
            self._task_map[message.messageId] = task_id

    def insert_message_history(self, task: Task, message: Message | None):
        if not message:
            return
        if task.history is None:
            task.history = []
        message_id = message.messageId
        if not message_id:
            return
        if task.history and (
            task.status.message
            and task.status.message.messageId not in [x.messageId for x in task.history]
        ):
            task.history.append(task.status.message)
        elif not task.history and task.status.message:
            task.history = [task.status.message]
        else:
            print(
                "Message id already in history",
                task.status.message.messageId if task.status.message else "",
                task.history,
            )

    def add_or_get_task(self, event: TaskCallbackArg):
        task_id = None
        if isinstance(event, Message):
            task_id = event.taskId
        elif isinstance(event, Task):
            task_id = event.id
        else:
            task_id = event.taskId
        if not task_id:
            task_id = str(uuid.uuid4())
        current_task = next(filter(lambda x: x.id == task_id, self._tasks), None)
        if not current_task:
            context_id = event.contextId
            current_task = Task(
                id=task_id,
                # initialize with submitted
                status=TaskStatus(state=TaskState.submitted),
                artifacts=[],
                context_id=context_id,
            )
            self.add_task(current_task)
            return current_task

        return current_task

    def process_artifact_event(
        self, current_task: Task, task_update_event: TaskArtifactUpdateEvent
    ):
        artifact = task_update_event.artifact
        if not task_update_event.append:
            # received the first chunk or entire payload for an artifact
            if task_update_event.lastChunk is None or task_update_event.lastChunk:
                # lastChunk bit is missing or is set to true, so this is the entire payload
                # add this to artifacts
                if not current_task.artifacts:
                    current_task.artifacts = []
                current_task.artifacts.append(artifact)
            else:
                # this is a chunk of an artifact, stash it in temp store for assembling
                if artifact.artifactId not in self._artifact_chunks:
                    self._artifact_chunks[artifact.artifactId] = []
                self._artifact_chunks[artifact.artifactId].append(artifact)
        else:
            # we received an append chunk, add to the existing temp artifact
            current_temp_artifact = self._artifact_chunks[artifact.artifactId][-1]
            # TODO handle if current_temp_artifact is missing
            current_temp_artifact.parts.extend(artifact.parts)
            if task_update_event.lastChunk:
                if current_task.artifacts:
                    current_task.artifacts.append(current_temp_artifact)
                else:
                    current_task.artifacts = [current_temp_artifact]
                del self._artifact_chunks[artifact.artifactId][-1]

    def add_event(self, event: Event):
        self._events[event.id] = event

    def get_conversation(
        self, conversation_id: Optional[str]
    ) -> Optional[Conversation]:
        if not conversation_id:
            return None
        return next(
            filter(
                lambda c: c and c.conversation_id == conversation_id,
                self._conversations,
            ),
            None,
        )

    def get_pending_messages(self) -> list[tuple[str, str]]:
        rval = []
        for message_id in self._pending_message_ids:
            if message_id in self._task_map:
                task_id = self._task_map[message_id]
                task = next(filter(lambda x: x.id == task_id, self._tasks), None)
                if not task:
                    rval.append((message_id, ""))
                elif task.history and task.history[-1].parts:
                    if len(task.history) == 1:
                        rval.append((message_id, "Working..."))
                    else:
                        part = task.history[-1].parts[0]
                        rval.append(
                            (
                                message_id,
                                part.root.text
                                if part.root.kind == "text"
                                else "Working...",
                            )
                        )
            else:
                rval.append((message_id, ""))
        return rval

    def register_agent(self, url):
        agent_data = get_agent_card(url)
        if not agent_data.url:
            agent_data.url = url
        self._agents.append(agent_data)
        self._host_agent.register_agent_card(agent_data)
        # Now update the host agent definition
        self._initialize_host()

    @property
    def agents(self) -> list[AgentCard]:
        return self._agents

    @property
    def conversations(self) -> list[Conversation]:
        return self._conversations

    @property
    def tasks(self) -> list[Task]:
        return self._tasks

    @property
    def events(self) -> list[Event]:
        return sorted(self._events.values(), key=lambda x: x.timestamp)

    def adk_content_from_message(self, message: Message) -> types.Content:
        parts: list[types.Part] = []
        for p in message.parts:
            part = p.root
            if part.kind == "text":
                parts.append(types.Part.from_text(text=part.text))
            elif part.kind == "data":
                json_string = json.dumps(part.data)
                parts.append(types.Part.from_text(text=json_string))
            elif part.kind == "file":
                if isinstance(part.file, FileWithUri):
                    parts.append(
                        types.Part.from_uri(
                            file_uri=part.file.uri,
                            mime_type=part.file.mimeType,
                        )
                    )
                else:
                    parts.append(
                        types.Part.from_bytes(
                            data=part.file.bytes.encode("utf-8"),
                            mime_type=part.file.mimeType,
                        )
                    )
        return types.Content(parts=parts, role=message.role)

    async def adk_content_to_message(
        self,
        content: types.Content,
        context_id: str | None,
        task_id: str | None,
    ) -> Message:
        """
        Converts ADK's internal `Content` object into a unified `Message` format.

        For each part in the ADK content, determines its type and converts it into
        a proper `Part` variant:
        - If `text` is present: Attempts to parse it as JSON (DataPart), else as plain text (TextPart).
        - If `inline_data` and `file_data` are present: Encodes file data to base64 and wraps it as a FilePart.
        - If only `file_data` is present: Wraps file URI and MIME type as a FilePart with URI.
        - Internal types like `video_metadata`, `function_call`, `function_response`, `executable_code`, etc.,
          are flattened into DataPart or processed accordingly (like calling `_handle_function_response`).
        - If no known type is found, raises an error.

        Args:
            content (types.Content): The ADK content to convert.
            context_id (str | None): Context/session identifier.
            task_id (str | None): Task identifier.

        Returns:
            Message: A transformed Message object with appropriate Parts and metadata.
        """
        parts: list[Part] = []
        if not content.parts:
            return Message(
                parts=[],
                role=Role.user if content.role == Role.user else Role.agent,
                context_id=context_id,
                task_id=task_id,
                message_id=str(uuid.uuid4()),
            )

        for part in content.parts:
            if part.text:
                # try parse as data
                try:
                    data = json.loads(part.text)
                    parts.append(Part(root=DataPart(data=data)))
                except Exception:
                    parts.append(Part(root=TextPart(text=part.text)))

            elif part.inline_data:
                if part.file_data:
                    parts.append(
                        Part(
                            root=FilePart(
                                file=FileWithBytes(
                                    bytes=base64.b64encode(
                                        part.inline_data.data or b""
                                    ).decode("utf-8"),
                                    mime_type=part.file_data.mime_type,
                                ),
                            )
                        )
                    )
            elif part.file_data:
                parts.append(
                    Part(
                        root=FilePart(
                            file=FileWithUri(
                                uri=part.file_data.file_uri or "",
                                mime_type=part.file_data.mime_type,
                            )
                        )
                    )
                )
            # These aren't managed by the A2A message structure, these are internal
            # details of ADK, we will simply flatten these to json representations.
            elif part.video_metadata:
                parts.append(Part(root=DataPart(data=part.video_metadata.model_dump())))
            elif part.thought:
                parts.append(Part(root=TextPart(text="thought")))
            elif part.executable_code:
                parts.append(
                    Part(root=DataPart(data=part.executable_code.model_dump()))
                )
            elif part.function_call:
                parts.append(Part(root=DataPart(data=part.function_call.model_dump())))
            elif part.function_response:
                parts.extend(
                    await self._handle_function_response(part, context_id, task_id)
                )
            else:
                raise ValueError("Unexpected content, unknown type")
        return Message(
            role=Role.user if content.role == Role.user else Role.agent,
            parts=parts,
            context_id=context_id,
            task_id=task_id,
            message_id=str(uuid.uuid4()),
        )

    async def _handle_function_response(
        self, part: types.Part, context_id: str | None, task_id: str | None
    ) -> list[Part]:
        """
        Processes a function response from a Part and returns a list of Part objects.
        Supports handling of:
        - plain strings
        - dictionaries (including file-type indicators)
        - DataPart and associated artifact loading
        - fallback to DataPart for unknown types or exceptions
        """
        parts = []
        try:
            result = (
                part.function_response
                and part.function_response.response
                and part.function_response.response.get("result", [])
                or []
            )

            for p in result:
                if isinstance(p, str):
                    # simple text result
                    parts.append(Part(root=TextPart(text=p)))

                elif isinstance(p, dict):
                    # check if it's a file-type dictionary
                    if p.get("kind") == "file":
                        parts.append(Part(root=FilePart(**p)))
                    else:
                        parts.append(Part(root=DataPart(data=p)))

                elif isinstance(p, DataPart):
                    # handle file loading from artifact service
                    if "artifact-file-id" in p.data:
                        file_part = await self._artifact_service.load_artifact(
                            user_id=self.user_id,
                            session_id=context_id or "",
                            app_name=self.app_name,
                            filename=p.data["artifact-file-id"],
                        )
                        if file_part and file_part.inline_data:
                            file_data = file_part.inline_data.data
                            if file_data:
                                base64_data = base64.b64encode(file_data).decode(
                                    "utf-8"
                                )
                                parts.append(
                                    Part(
                                        root=FilePart(
                                            file=FileWithBytes(
                                                bytes=base64_data,
                                                mime_type=file_part.file_data.mime_type
                                                if file_part.file_data
                                                else None,
                                                name="artifact_file",
                                            )
                                        )
                                    )
                                )
                    else:
                        parts.append(Part(root=DataPart(data=p.data)))
                else:
                    parts.append(
                        Part(root=TextPart(text="Unknown content type encountered"))
                    )

        except Exception as e:
            print("Couldn't convert to messages:", e)
            res = part.function_response
            parts.append(Part(root=DataPart(data=res.model_dump() if res else {})))

        # finally return the parts
        return parts


def get_message_id(m: Message | None) -> str | None:
    if not m or not m.metadata or "message_id" not in m.metadata:
        return None
    return m.metadata["message_id"]


def task_still_open(task: Task | None) -> bool:
    if not task:
        return False
    return task.status.state in [
        TaskState.submitted,
        TaskState.working,
        TaskState.input_required,
    ]
