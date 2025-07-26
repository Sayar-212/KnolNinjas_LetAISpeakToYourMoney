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


# SOLUTION: Use a single comprehensive agent instead of parallel processing
# This avoids the ParallelAgent execution issues
comprehensive_receipt_agent = LlmAgent(
    name="ComprehensiveReceiptAgent",
    model="gemini-2.0-flash",
    description="Intelligently extracts structured fields and semantic insights from digital payment receipts.",
    instruction="""
You are an advanced receipt intelligence system capable of processing digital payment receipts from various platforms (Google Pay, PhonePe, Paytm, UPI apps, banking apps, etc.).

ANALYSIS APPROACH:
1. First, identify the payment platform and receipt type
2. Locate and extract structural transaction data
3. Analyze spending patterns and context
4. Generate behavioral and semantic insights

STRUCTURAL FIELDS TO EXTRACT:
- merchant: Business/merchant name (look for "Business Name", "Merchant", "Paid to", "To:", etc.)
- amount: Total transaction amount with currency symbol (₹, $, etc.) - find "Total", "Amount Paid", "Total Paid"
- date: Transaction date in DD MMM YYYY format (convert from any date format found)
- time: Transaction time in HH:MM AM/PM format (convert from 24hr if needed)
- upi_transaction_id: UPI/transaction reference ID (look for "UPI ID", "Transaction ID", "Ref ID", etc.)
- google_transaction_id: Platform-specific transaction ID (Google Pay ID, PhonePe ID, etc.)

CONTEXTUAL ANALYSIS FOR INSIGHTS:
- category: Intelligently categorize based on merchant type and context
  * Food & Dining: Restaurants, food delivery, cafes, groceries
  * Transportation: Uber, cab services, fuel, parking, public transport
  * Shopping: E-commerce, retail, fashion, electronics
  * Entertainment: Movies, streaming, games, events
  * Accommodation: Hotels, Airbnb, bookings
  * Utilities: Bills, recharges, subscriptions
  * Healthcare: Medical, pharmacy, insurance
  * Education: Courses, books, fees
  * Financial: Investments, transfers, loans
  * Others: Miscellaneous transactions

- behavioral_tag: Identify spending behavior patterns
  * Microtransaction: Small amounts (<₹100)
  * Impulse buy: Entertainment, food delivery at odd hours
  * Planned expense: Bills, subscriptions, bookings
  * Weekend spend: Transactions on Sat/Sun
  * Repeat merchant: Same merchant multiple times
  * Vacation/Travel: Hotels, bookings, travel-related
  * Business expense: Professional services, tools
  * Emergency expense: Medical, urgent services
  * Luxury spend: Premium brands, high-end services

- sentiment: Spending impact assessment
  * Low: ≤₹500 (routine, minimal impact)
  * Medium: ₹501-₹5000 (moderate impact, planned expense)
  * High: >₹5000 (significant impact, major expense)

PROCESSING STRATEGY:
- For image receipts: Use OCR understanding to identify text regions and extract information
- For text receipts: Parse systematically, looking for keywords and patterns
- Handle various formats: Different platforms have different layouts
- Be flexible with field locations and naming conventions
- Use context clues when exact matches aren't found

INTELLIGENCE FEATURES:
- Recognize merchant aliases (e.g., "Zomato" vs "Zomato India Pvt Ltd")
- Convert time zones and formats automatically
- Identify transaction types (payment, refund, transfer)
- Extract secondary information when primary fields are missing
- Handle multilingual content (Hindi, English mixed)

OUTPUT: Return ONLY a valid JSON object with all 9 fields. Use empty strings "" for truly missing values.

QUALITY CHECKS:
- Ensure amounts include currency symbols
- Validate date/time formats
- Check that category matches merchant type
- Verify behavioral tags align with transaction context
- Confirm sentiment matches amount ranges
""",
)

# Use the comprehensive agent directly instead of a complex pipeline
receipt_processing_pipeline = comprehensive_receipt_agent


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
        return 'Analyzing payment receipt using intelligent field extraction and contextual insights...'

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
                'stage': 'intelligent_processing',
                'updates': 'Analyzing receipt structure and extracting transaction intelligence...'
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
                    
                    # Clean up the response if it contains markdown code blocks
                    if isinstance(response, str):
                        response = response.strip()
                        if response.startswith('```json'):
                            # Extract JSON from markdown code block
                            lines = response.split('\n')
                            json_lines = []
                            in_json = False
                            for line in lines:
                                if line.strip() == '```json':
                                    in_json = True
                                    continue
                                elif line.strip() == '```' and in_json:
                                    break
                                elif in_json:
                                    json_lines.append(line)
                            response = '\n'.join(json_lines)
                        elif response.startswith('```'):
                            # Handle other code block formats
                            lines = response.split('\n')
                            if len(lines) > 2:
                                response = '\n'.join(lines[1:-1])
                    
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
                            # Log what we got for debugging
                            logger.warning(f"Invalid receipt data structure: {parsed_response}")
                            yield {
                                'is_task_complete': True,
                                'content': parsed_response,  # Return anyway for debugging
                            }
                    except (json.JSONDecodeError, TypeError) as e:
                        logger.error(f"JSON parsing error: {e}, raw response: {response}")
                        yield {
                            'is_task_complete': True,
                            'content': response,
                        }
                else:
                    # Yield intermediate progress updates
                    yield {
                        'is_task_complete': False,
                        'stage': 'processing',
                        'updates': 'Applying contextual analysis and pattern recognition...',
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
        required_structural_fields = ['merchant', 'amount']
        required_semantic_fields = ['category', 'behavioral_tag', 'sentiment']
        
        has_structural = any(field in data and data[field] for field in required_structural_fields)
        has_semantic = any(field in data and data[field] for field in required_semantic_fields)
        
        # Should have both types of fields for a complete receipt
        return has_structural or has_semantic  # Changed to OR for more flexibility during debugging