import os
import json
import re
import logging
from typing import Any, AsyncIterable, Dict, Optional

from google.adk.agents import Agent
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Load JSON from MCP folder
def load_fi_mcp_json(file_path: str) -> dict:
    """Load JSON data from Fi MCP folder."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"MCP JSON file not found: {file_path}")
        return {}
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in file: {file_path}")
        return {}

# Tool 2: Convert CSA Trust Report to JSON
def convert_trust_report_to_json(report: str) -> dict:
    """Convert CSA trust report text to structured JSON."""
    result = {}

    try:
        # Extract sections with regex
        agent_match = re.search(r"Agent:\s*(.*)", report)
        result["agent"] = agent_match.group(1).strip() if agent_match else "Unknown"
        
        action_match = re.search(r"Action:\s*(.*)", report)
        result["action"] = action_match.group(1).strip() if action_match else "Unknown"

        # Sources Used
        sources = re.findall(r"\d+\.\s*(http[^\n]+)", report)
        result["sources_used"] = sources

        # Source Trust
        trust = re.search(r"Sources:\s*(✅ Trustable|❌ Unverified)", report)
        result["sources_trust"] = trust.group(1).strip() if trust else "❓ Unknown"

        # Rules Referenced
        if "Rules Referenced:" in report and "Data Analyzed:" in report:
            rules_section = report.split("Rules Referenced:")[1].split("Data Analyzed:")[0]
            rules = re.findall(r"-\s*(.+)", rules_section)
            result["rules_referenced"] = [r.strip() for r in rules]
        else:
            result["rules_referenced"] = []

        # Data Analyzed
        if "Data Analyzed:" in report and "Reason:" in report:
            data_block = report.split("Data Analyzed:")[1].split("Reason:")[0]
            data_lines = re.findall(r"-\s*(.+?):\s*(.+)", data_block)
            result["data_analyzed"] = {k.strip(): v.strip() for k, v in data_lines}
        else:
            result["data_analyzed"] = {}

        # Reason
        reason = re.search(r"Reason:\s*\n(.*?)\n\s*\nStatus:", report, re.DOTALL)
        result["reason"] = reason.group(1).strip() if reason else ""

        # Status
        status = re.search(r"Status:\s*(✅ Approved|❌ Not Approved)", report)
        result["status"] = status.group(1).strip() if status else "❓ Unknown"

    except Exception as e:
        logger.error(f"Error parsing trust report: {e}")
        # Return basic structure with error info
        result = {
            "agent": "Unknown",
            "action": "Parsing Error",
            "sources_used": [],
            "sources_trust": "❓ Unknown",
            "rules_referenced": [],
            "data_analyzed": {},
            "reason": f"Error parsing report: {str(e)}",
            "status": "❌ Not Approved"
        }

    return result

# Define the CSA Agent (ADK style)
csa_agent = Agent(
    name="CSA",
    model="gemini-2.0-flash",
    description="Compliance and Security Agent that audits outputs of other agents from Fi MCP data",
    instruction="""
You are CSA - the Compliance and Security Agent for Project Arthasashtri. Building trust for agents that sources are legal and trustable.

Your job is to analyze any agent's response coming from Fi MCP output JSON and generate a **clear, transparent trust report** for users.

Instructions:
- Accept various input formats:
  - A2A artifact JSON with financial analysis data
  - Direct agent output JSON with fields: agent, action, decision, sources, used_fields, financial_rule_refs
  - Text descriptions of agent outputs

- Extract relevant information from the input:
  - If A2A artifact format: extract from artifact.parts[0].data
  - If direct agent JSON: use fields directly
  - If text format: parse for agent details

Your main job is to help users trust every agent's response by:
- Showing the sources used 
- Validating the sources are trustable or not
- Validating the data used
- Explaining the decision in simple terms in points
- Verifying compliance with financial rules
- Displaying the links to MCP or external docs

For A2A Financial Analysis artifacts, extract:
- Agent: "SmartFinancialAdvisor" (or from context)
- Action: Financial analysis and market research
- Sources: Extract from search_links array
- Data: Extract from financial_analysis and market_analysis
- Rules: Look for financial rule references

Format your output exactly like this:

Agent: CSA

Action: [Agent Action Summary]  
 
Sources Used:  
1. [URL 1 or source description]  
2. [URL 2 or source description]  
...  

 
Sources: ✅ Trustable or ❌ Unverified  


Rules Referenced:  
- [Rule 1 or "Standard financial analysis practices"]  
- [Rule 2 or "Market research protocols"]  
...  


Data Analyzed:  
- key1: value1  
- key2: value2  
...  


Reason:  
[Short human-readable explanation in bullet points or paragraph]  
 

Status: ✅ Approved or ❌ Not Approved  


Think step-by-step:
- Parse the input format (A2A artifact, direct JSON, or text)
- Extract agent name, actions, and data sources
- Validate each source for trustworthiness
- Cross-check rule references or apply standard practices
- Summarize key data points analyzed
- Explain reasoning in plain English
- Decide final status: Approved or Not Approved

Please use the tool `convert_trust_report_to_json` to convert the above formatted output into JSON format.

Give final output of `convert_trust_report_to_json` format.
""",
    tools=[load_fi_mcp_json, convert_trust_report_to_json]
)


class CSAAgent:
    """Wrapper for the CSA agent to work with A2A framework."""

    SUPPORTED_CONTENT_TYPES = ['text', 'text/plain', 'application/json']

    def __init__(self):
        self._agent = csa_agent
        self._user_id = 'csa_auditor'
        self._runner = Runner(
            app_name=self._agent.name,
            agent=self._agent,
            artifact_service=InMemoryArtifactService(),
            session_service=InMemorySessionService(),
            memory_service=InMemoryMemoryService(),
        )

    def get_processing_message(self) -> str:
        return 'Auditing agent output for compliance and security validation...'

    async def stream(self, query: str, session_id: str, message: Any = None) -> AsyncIterable[Dict[str, Any]]:
        """Stream processing results from the CSA compliance audit pipeline."""
        try:
            session = await self._runner.session_service.get_session(
                app_name=self._agent.name,
                user_id=self._user_id,
                session_id=session_id,
            )

            # Prepare content based on input type
            content_parts = []
            
            # Handle text inputs from the message
            if message and hasattr(message, 'parts'):
                for part in message.parts:
                    if hasattr(part, 'root') and hasattr(part.root, 'text'):
                        content_parts.append(types.Part.from_text(text=part.root.text))
            
            # Add query text if not already included
            if query and not any(hasattr(p, 'text') and p.text == query for p in content_parts):
                content_parts.append(types.Part.from_text(text=query))
            
            if not content_parts:
                content_parts = [types.Part.from_text(text=query or "Please provide agent output data for compliance audit")]

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
                'stage': 'source_validation',
                'updates': 'Validating source trustworthiness and credibility...'
            }

            tool_call_count = 0
            async for event in self._runner.run_async(
                user_id=self._user_id, 
                session_id=session.id, 
                new_message=content
            ):
                # Track tool usage progress
                if hasattr(event, 'content') and event.content:
                    for part in event.content.parts:
                        if hasattr(part, 'function_call') and part.function_call:
                            tool_call_count += 1
                            if part.function_call.name == 'load_fi_mcp_json':
                                yield {
                                    'is_task_complete': False,
                                    'stage': 'data_analysis',
                                    'updates': 'Loading and analyzing MCP data references...'
                                }
                            elif part.function_call.name == 'convert_trust_report_to_json':
                                yield {
                                    'is_task_complete': False,
                                    'stage': 'report_generation',
                                    'updates': 'Converting trust report to structured JSON format...'
                                }

                if event.is_final_response():
                    response = ''
                    
                    if (event.content and event.content.parts and event.content.parts[0].text):
                        response = '\n'.join([p.text for p in event.content.parts if p.text])
                    elif (event.content and event.content.parts and 
                          any([True for p in event.content.parts if p.function_response])):
                        # Get the function response (should be the JSON from convert_trust_report_to_json)
                        for p in event.content.parts:
                            if p.function_response:
                                response = p.function_response.model_dump()
                                break
                    
                    # The response should already be in the expected JSON format from convert_trust_report_to_json
                    try:
                        if isinstance(response, str):
                            # Try to parse if it's a string
                            parsed_response = json.loads(response)
                        elif isinstance(response, dict):
                            # If it's already a dict (from function response)
                            parsed_response = response
                        else:
                            # Handle other formats
                            parsed_response = {"error": "Unexpected response format", "raw_response": str(response)}
                            
                        # Validate expected compliance audit fields
                        if self._is_valid_compliance_data(parsed_response):
                            yield {
                                'is_task_complete': True,
                                'content': parsed_response,
                            }
                        else:
                            # If not valid, try to create a basic structure
                            fallback_response = {
                                "agent": "CSA",
                                "action": "Compliance audit attempted",
                                "sources_used": [],
                                "sources_trust": "❓ Unknown",
                                "rules_referenced": [],
                                "data_analyzed": {},
                                "reason": f"Audit completed with response: {str(response)[:200]}...",
                                "status": "❌ Not Approved"
                            }
                            yield {
                                'is_task_complete': True,
                                'content': fallback_response,
                            }
                    except (json.JSONDecodeError, TypeError) as e:
                        logger.error(f"JSON parsing error: {e}")
                        yield {
                            'is_task_complete': True,
                            'content': str(response),
                        }
                else:
                    # Yield intermediate progress updates for non-tool events
                    if not hasattr(event, 'content') or not any(
                        hasattr(p, 'function_call') for p in event.content.parts if event.content and event.content.parts
                    ):
                        yield {
                            'is_task_complete': False,
                            'stage': 'rule_verification',
                            'updates': 'Verifying compliance with financial rules and regulations...',
                        }

        except Exception as e:
            logger.error(f"Error in CSA compliance audit stream: {e}")
            yield {
                'is_task_complete': True,
                'content': f"Error processing compliance audit: {str(e)}",
            }

    def _is_valid_compliance_data(self, data: Any) -> bool:
        """Check if the response contains valid compliance audit structure."""
        if not isinstance(data, dict):
            return False
        
        # Check for key compliance audit fields
        required_fields = ['agent', 'action', 'status']
        return all(field in data for field in required_fields)