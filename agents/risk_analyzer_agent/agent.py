from google.adk.agents import SequentialAgent

from subagent.analyser import risk_agent
from subagent.normalized_output import risk_output_normalizer

from typing import Any, AsyncIterable #, Optional
# from google.adk.agents.llm_agent import LlmAgent
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
# from google.adk.tools.tool_context import ToolContext
from google.genai import types

class risk_analyzer:
    SUPPORTED_CONTENT_TYPES = ['text', 'text/plain']

    def __init__(self):
        self._agent = self._build_agent()
        self._user_id = 'remote_agent'
        self._runner = Runner(
            app_name=self._agent.name,
            agent=self._agent,
            artifact_service=InMemoryArtifactService(),
            session_service=InMemorySessionService(),
            memory_service=InMemoryMemoryService(),
        )
    
    def get_processing_message(self) -> str:
        return 'Processing the risk analyzer request...'
    
    def _build_agent(self) -> str:
        return SequentialAgent(
            name="risk_agent_output",
            sub_agents=[
                risk_agent,
                risk_output_normalizer,
            ],
            description="""This agent performs end-to-end risk analysis on a given investment opportunity such as a stock, ETF, or REIT.

            Workflow:
            1. It uses the `risk_agent`, powered by Gemini 2.5 Pro, to evaluate the opportunity based on historical and fundamental data from sources like TwelveData, yFinance, and FMP APIs.
            2. The agent provides a clear recommendation—either "Invest" or "Skip"—with justifications grounded in market data and practical reasoning.
            3. The output is then passed to the `risk_output_normalizer`, powered by Gemini 2.0 Flash, which transforms the raw response into a structured JSON format compliant with the A2A protocol.
            4. Final output adheres to the `RiskAnalysis` schema, containing a `recommendation` and a list of `justification` strings.

            This agent ensures a data-informed, decisive, and protocol-compliant investment recommendation for integration into autonomous agent ecosystems.
            """,
        )
    
    async def stream(self, query: str, session_id: str) -> AsyncIterable[dict[str, Any]]:
        session = await self._runner.session_service.get_session(
            app_name=self._agent.name,
            user_id=self._user_id,
            session_id=session_id,
        )

        if session is None:
            session = await self._runner.session_service.create_session(
                app_name=self._agent.name,
                user_id=self._user_id,
                state={},
                session_id=session_id,
            )

        content = types.Content(role='user', parts=[types.Part.from_text(text=query)])
        full_response = []

        async for event in self._runner.run_async(
            user_id=self._user_id,
            session_id=session.id,
            new_message=content
        ):
            if event.is_final_response():
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.text:
                            full_response.append(part.text)
                        elif part.function_response:
                            full_response.append(str(part.function_response.model_dump()))
            else:
                yield {
                    'is_task_complete': False,
                    'updates': self.get_processing_message(),
                }

        # After all agents finish
        if full_response:
            yield {
                'is_task_complete': True,
                'content': "\n".join(full_response),
            }
        else:
            yield {
                'is_task_complete': True,
                'content': 'Risk analysis completed but no output was generated.',
            }
