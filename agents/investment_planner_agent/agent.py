from google.adk.agents import SequentialAgent

from subagent.get_user_details import user_details_agent
from subagent.web_search import web_search_agent
from subagent.allocation.agent import allocate_agent
from subagent.portfolio_optimizer import optimize_portfolio_agent
from subagent.review import review_agent
from subagent.output.agent import output_normalizer_agent

# import json
# import random
from typing import Any, AsyncIterable #, Optional
# from google.adk.agents.llm_agent import LlmAgent
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
# from google.adk.tools.tool_context import ToolContext
from google.genai import types

class investment_planner:
    """An agent that handles agent planning"""

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
        return 'Processing the investment planner request...'
    
    def _build_agent(self) -> str:
        return SequentialAgent(
            name="investment_planning_agent",
            sub_agents=[
                user_details_agent,
                web_search_agent,
                allocate_agent,
                optimize_portfolio_agent,
                review_agent,
                output_normalizer_agent,
            ],
            description="""
            A comprehensive financial planning agent that guides users through the entire investment lifecycle.

            1. **User Profiling** - Collects key financial and demographic details including income, age, goals, and risk tolerance.
            2. **Opportunity Discovery** - Searches the web and financial APIs to identify investment opportunities aligned with the user's profile.
            3. **Initial Allocation** - Distributes available capital across assets based on the user's risk profile and liquidity needs.
            4. **Portfolio Optimization** - Refines the allocation using financial modeling principles such as Modern Portfolio Theory (MPT), ensuring better diversification and risk-adjusted return.
            5. **Review & Recommendation** - Evaluates the optimized portfolio using current market trends and provides final actionable suggestions or rebalancing advice.
            6. **Output Normalization** - Normalizes the final output to json format using defined output schemas for a2a compatibility.

            The pipeline ensures structured, explainable, a2a compatibility, and market-aware investment planning tailored to individual user needs.
            """
        )
    
    async def stream(self, query, session_id) -> AsyncIterable[dict[str, Any]]:
        session = await self._runner.session_service.get_session(
            app_name=self._agent.name,
            user_id=self._user_id,
            session_id=session_id,
        )

        content = types.Content(role='user', parts=[types.Part.from_text(text=query)])

        if session is None:
            session = await self._runner.session_service.create_session(
                app_name=self._agent.name,
                user_id=self._user_id,
                state={},
                session_id=session_id,
            )

        full_response = []

        async for event in self._runner.run_async(
            user_id=self._user_id, session_id=session.id, new_message=content
        ):
            if event.is_final_response():
                response = ''
                if event.content and event.content.parts:
                    for p in event.content.parts:
                        if p.text:
                            full_response.append(p.text)
                        elif p.function_response:
                            full_response.append(str(p.function_response.model_dump()))

            else:
                yield {
                    'is_task_complete': False,
                    'updates': self.get_processing_message(),
                }

        # After all agents are done
        if full_response:
            yield {
                'is_task_complete': True,
                'content': "\n".join(full_response),
            }

