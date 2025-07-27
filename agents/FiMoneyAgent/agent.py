from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from google.adk.tools.mcp_tool.mcp_session_manager import (
    StreamableHTTPConnectionParams,
)
from uuid import uuid4

from collections.abc import AsyncIterable


from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from typing import Any


toolset = MCPToolset(
    connection_params=StreamableHTTPConnectionParams(
        url="https://mcp.fi.money:8080/mcp/stream",
        headers={"mcp_session_id": str(uuid4())},
    )
)

root_agent = LlmAgent(
    model="gemini-2.0-flash",
    name="fi_money_agent",
    instruction="Helps user on their money, using fi money mcp server",
    tools=[toolset],
)


class FiMoneyAgent:
    SUPPERTED_CONTENT_TYPES = ["text", "text/plain"]

    def __init__(self):
        self._agent = self._build_agent()
        self._user_id = "remote_agent"
        self._runner = Runner(
            app_name=self._agent.name,
            agent=self._agent,
            artifact_service=InMemoryArtifactService(),
            session_service=InMemorySessionService(),
            memory_service=InMemoryMemoryService(),
        )

    def get_processing_message(self) -> str:
        return "Processing the call"

    def _build_agent(self) -> LlmAgent:
        return LlmAgent(
            model="gemini-2.0-flash",
            name="fi_money_agent",
            instruction="You are a helpful agent that uses fi mcp server to helps user with their money related issues",
            tools=[toolset],
        )

    async def stream(self, query, session_id) -> AsyncIterable[dict[str, Any]]:
        session = await self._runner.session_service.get_session(
            app_name=self._agent.name,
            user_id=self._user_id,
            session_id=session_id,
        )
        content = types.Content(role="user", parts=[types.Part.from_text(text=query)])
        if session is None:
            session = await self._runner.session_service.create_session(
                app_name=self._agent.name,
                user_id=self._user_id,
                state={},
                session_id=session_id,
            )
        async for event in self._runner.run_async(
            user_id=self._user_id, session_id=session.id, new_message=content
        ):
            if event.is_final_response():
                response = ""
                if (
                    event.content
                    and event.content.parts
                    and event.content.parts[0].text
                ):
                    response = "\n".join(
                        [p.text for p in event.content.parts if p.text]
                    )
                elif (
                    event.content
                    and event.content.parts
                    and any([True for p in event.content.parts if p.function_response])
                ):
                    response = next(
                        p.function_response.model_dump() for p in event.content.parts
                    )
                yield {
                    "is_task_complete": True,
                    "content": response,
                }
            else:
                yield {
                    "is_task_complete": False,
                    "updates": self.get_processing_message(),
                }
