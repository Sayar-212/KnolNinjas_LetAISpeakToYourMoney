import json
import logging
from typing import Any, AsyncIterable, Dict, Optional

from google.adk.agents.llm_agent import LlmAgent
from google.adk.agents import ParallelAgent, SequentialAgent
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

logger = logging.getLogger(__name__)


# Your original agent pipeline
field_extractor_agent = LlmAgent(
    name="FieldExtractorAgent",
    model="gemini-2.0-flash",
    description="Extracts structured fields from a GPay receipt.",
    instruction="""
You are a receipt field extraction expert.

You will be given a Google Pay receipt image. Extract the following fields:
- merchant
- amount (include ₹ symbol)
- date (DD MMM YYYY)
- time (hh:mm am/pm)
- upi_transaction_id
- google_transaction_id

Output only valid JSON with exactly those keys. If any field is missing, leave it as an empty string.
""",
    output_key="extracted_fields"
)

insight_agent = LlmAgent(
    name="InsightAgent",
    model="gemini-2.0-flash",
    description="Analyzes receipt for semantic insights (e.g., category, behavioral tags).",
    instruction="""
You are a financial insight assistant.

You will be given a Google Pay receipt image or its extracted text.

Determine the following:
- category (e.g., Food, Transport, Shopping, Utilities)
- behavioral_tag (e.g., Microtransaction, Weekend spend, Repeat merchant)
- sentiment (Low/Medium/High spend)

Output only a valid JSON object with keys: category, behavioral_tag, sentiment.
""",
    output_key="semantic_insights"
)

parallel_receipt_agent = ParallelAgent(
    name="ParallelReceiptAnalyzers",
    sub_agents=[field_extractor_agent, insight_agent],
    description="Runs field extraction and insight analysis in parallel."
)

merger_agent = LlmAgent(
    name="ReceiptMergerAgent",
    model="gemini-2.0-flash",
    description="Merges structured fields and semantic insights into unified JSON.",
    instruction="""
You are an AI assistant merging structured and semantic receipt data.

You will be given:
- Extracted receipt fields (from field extractor)
- Semantic insights (from insight agent)

Combine them into one enriched JSON object with all fields from both inputs:
{
  merchant, amount, date, time,
  upi_transaction_id, google_transaction_id,
  category, behavioral_tag, sentiment
}

Use empty strings if anything is missing. Output only the final JSON object.
"""
)

receipt_processing_pipeline = SequentialAgent(
    name="SmartReceiptProcessor",
    description="Extracts and enriches GPay receipt data using parallel agents, then merges results.",
    sub_agents=[parallel_receipt_agent, merger_agent]
)


class ReceiptProcessingAgent:
    """Wrapper for the receipt processing pipeline to work with A2A framework."""

    SUPPORTED_CONTENT_TYPES = ['text', 'text/plain', 'image/jpeg', 'image/png']

    def __init__(self):
        self._agent = receipt_processing_pipeline
        self._user_id = 'receipt_processor'
        self._runner = Runner(
            app_name=self._agent.name,
            agent=self._agent,
            artifact_service=InMemoryArtifactService(),
            session_service=InMemorySessionService(),
            memory_service=InMemoryMemoryService(),
        )

    def get_processing_message(self) -> str:
        return 'Processing GPay receipt through field extraction and insight analysis...'

    async def stream(self, query: str, session_id: str, message: Any = None) -> AsyncIterable[Dict[str, Any]]:
        """Stream processing results from the receipt pipeline."""
        try:
            session = await self._runner.session_service.get_session(
                app_name=self._agent.name,
                user_id=self._user_id,
                session_id=session_id,
            )

            # Prepare content based on input type
            content_parts = []
            
            # Handle image inputs from the message
            if message and hasattr(message, 'parts'):
                for part in message.parts:
                    if hasattr(part, 'root'):
                        if hasattr(part.root, 'mime_type') and part.root.mime_type.startswith('image/'):
                            # Image data
                            content_parts.append(
                                types.Part(
                                    inline_data=types.Blob(
                                        mime_type=part.root.mime_type,
                                        data=part.root.data
                                    )
                                )
                            )
                        elif hasattr(part.root, 'text'):
                            # Text data
                            content_parts.append(types.Part.from_text(text=part.root.text))
            
            # Add query text if not already included
            if query and not any(hasattr(p, 'text') and p.text == query for p in content_parts):
                content_parts.append(types.Part.from_text(text=query))
            
            if not content_parts:
                content_parts = [types.Part.from_text(text=query or "Please process this receipt")]

            content = types.Content(role='user', parts=content_parts)

            if session is None:
                session = await self._runner.session_service.create_session(
                    app_name=self._agent.name,
                    user_id=self._user_id,
                    state={},
                    session_id=session_id,
                )

            # Yield progress updates during processing
            yield {
                'is_task_complete': False,
                'stage': 'parallel_processing',
                'updates': 'Starting parallel field extraction and insight analysis...'
            }

            async for event in self._runner.run_async(
                user_id=self._user_id, 
                session_id=session.id, 
                new_message=content
            ):
                if event.is_final_response():
                    response = ''
                    
                    if (event.content and event.content.parts and event.content.parts[0].text):
                        response = '\n'.join([p.text for p in event.content.parts if p.text])
                    elif (event.content and event.content.parts and 
                          any([True for p in event.content.parts if p.function_response])):
                        response = next(
                            p.function_response.model_dump()
                            for p in event.content.parts
                            if p.function_response
                        )
                    
                    # Try to parse and validate the response
                    try:
                        if isinstance(response, str):
                            parsed_response = json.loads(response)
                        else:
                            parsed_response = response
                            
                        # Validate expected receipt fields
                        if self._is_valid_receipt_data(parsed_response):
                            yield {
                                'is_task_complete': True,
                                'content': parsed_response,
                            }
                        else:
                            yield {
                                'is_task_complete': True,
                                'content': response,
                            }
                    except (json.JSONDecodeError, TypeError):
                        yield {
                            'is_task_complete': True,
                            'content': response,
                        }
                else:
                    # Yield intermediate progress updates
                    yield {
                        'is_task_complete': False,
                        'stage': 'processing',
                        'updates': self.get_processing_message(),
                    }

        except Exception as e:
            logger.error(f"Error in receipt processing stream: {e}")
            yield {
                'is_task_complete': True,
                'content': f"Error processing receipt: {str(e)}",
            }

    def _is_valid_receipt_data(self, data: Any) -> bool:
        """Check if the response contains valid receipt structure."""
        if not isinstance(data, dict):
            return False
        
        # Check for key receipt fields
        required_fields = ['merchant', 'amount']
        return any(field in data for field in required_fields)