import json
import logging
from typing import Any, Dict

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import (
    DataPart,
    Part,
    Task,
    TaskState,
    TextPart,
    UnsupportedOperationError,
)
from a2a.utils import (
    new_agent_parts_message,
    new_agent_text_message,
    new_task,
)
from a2a.utils.errors import ServerError
from agent import CSAAgent

logger = logging.getLogger(__name__)


class CSAAgentExecutor(AgentExecutor):
    """CSA AgentExecutor for compliance and security auditing."""

    def __init__(self):
        self.agent = CSAAgent()

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        user_input = context.get_user_input()
        task = context.current_task

        # Create a new task if one doesn't exist
        if not task:
            task = new_task(context.message)
            await event_queue.enqueue_event(task)
        
        updater = TaskUpdater(event_queue, task.id, task.contextId)
        
        try:
            # Check if input contains agent output data for compliance checking
            has_agent_data = self._has_agent_output_data(context, user_input)
            
            if not has_agent_data:
                await updater.update_status(
                    TaskState.input_required,
                    new_agent_text_message(
                        "Please provide agent output data for compliance audit. Supported formats:\n" +
                        "1. A2A artifact JSON (like financial analysis results)\n" +
                        "2. Direct agent output JSON with fields: agent, action, sources, etc.\n" +
                        "3. Text description of agent outputs\n" +
                        "Example: Paste the financial analysis artifact JSON for audit.",
                        task.contextId,
                        task.id,
                    ),
                    final=True,
                )
                return

            # Process the compliance audit through the CSA pipeline
            await updater.update_status(
                TaskState.working,
                new_agent_text_message(
                    "Analyzing agent output for compliance and security validation...",
                    task.contextId,
                    task.id,
                ),
            )

            # Stream responses from the CSA agent
            async for item in self.agent.stream(user_input, task.contextId, context.message):
                is_complete = item.get('is_task_complete', False)
                
                if not is_complete:
                    # Handle progress updates from different stages
                    stage = item.get('stage', 'processing')
                    status_message = self._get_stage_message(stage, item.get('updates', ''))
                    
                    await updater.update_status(
                        TaskState.working,
                        new_agent_text_message(
                            status_message, task.contextId, task.id
                        ),
                    )
                    continue
                
                # Handle final response
                content = item.get('content')
                
                if content is None:
                    await updater.update_status(
                        TaskState.failed,
                        new_agent_text_message(
                            'Failed to process compliance audit - no content received',
                            task.contextId,
                            task.id,
                        ),
                        final=True,
                    )
                    break
                
                # Try to parse as JSON for structured compliance data
                try:
                    if isinstance(content, str):
                        parsed_content = json.loads(content)
                    else:
                        parsed_content = content
                    
                    # Validate that we have the expected compliance audit structure
                    if self._is_valid_compliance_output(parsed_content):
                        # Return structured compliance audit data
                        await updater.add_artifact(
                            [Part(root=DataPart(data=parsed_content))], 
                            name='compliance_audit'
                        )
                        await updater.update_status(
                            TaskState.completed,
                            new_agent_text_message(
                                self._format_compliance_summary(parsed_content),
                                task.contextId,
                                task.id,
                            ),
                            final=True,
                        )
                    else:
                        # Return as text if not valid JSON structure
                        await updater.add_artifact(
                            [Part(root=TextPart(text=str(content)))], 
                            name='audit_report'
                        )
                        await updater.complete()
                    break
                    
                except json.JSONDecodeError:
                    # Handle non-JSON responses
                    await updater.add_artifact(
                        [Part(root=TextPart(text=str(content)))], 
                        name='audit_report'
                    )
                    await updater.complete()
                    break
                    
        except Exception as e:
            logger.error(f"Error processing compliance audit: {e}")
            await updater.update_status(
                TaskState.failed,
                new_agent_text_message(
                    f'Compliance audit failed: {str(e)}',
                    task.contextId,
                    task.id,
                ),
                final=True,
            )

    def _has_agent_output_data(self, context: RequestContext, user_input: str) -> bool:
        """Check if the request contains agent output data for auditing."""
        # Check for JSON data in message parts
        if hasattr(context.message, 'parts'):
            for part in context.message.parts:
                if hasattr(part, 'root') and hasattr(part.root, 'text'):
                    text = part.root.text
                    if self._is_agent_output_json(text):
                        return True
        
        # Check user input for agent output indicators
        return self._is_agent_output_json(user_input)

    def _is_agent_output_json(self, text: str) -> bool:
        """Check if text contains agent output JSON structure."""
        if not text:
            return False
            
        # Look for JSON structure with expected fields
        try:
            if '{' in text and '}' in text:
                # Try to extract JSON
                start = text.find('{')
                end = text.rfind('}') + 1
                if start != -1 and end != -1:
                    json_str = text[start:end]
                    parsed = json.loads(json_str)
                    
                    # Check for A2A artifact structure
                    if 'artifact' in parsed and 'parts' in parsed['artifact']:
                        return True
                    
                    # Check for expected agent output fields
                    expected_fields = ['agent', 'action', 'sources', 'user_financial_data', 'market_analysis']
                    return any(field in parsed for field in expected_fields)
        except (json.JSONDecodeError, ValueError):
            pass
        
        # Check for text indicators of agent output
        agent_indicators = [
            'agent:', 'action:', 'decision:', 'sources:', 'used_fields:', 'financial_rule_refs:',
            'artifact', 'financial_analysis', 'market_analysis', 'search_links', 'contextid', 'taskid'
        ]
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in agent_indicators)

    def _get_stage_message(self, stage: str, updates: str) -> str:
        """Generate appropriate status message based on processing stage."""
        stage_messages = {
            'source_validation': 'Validating source trustworthiness...',
            'rule_verification': 'Verifying compliance with financial rules...',
            'data_analysis': 'Analyzing referenced data fields...',
            'report_generation': 'Generating compliance trust report...',
            'processing': updates or 'Processing compliance audit...'
        }
        return stage_messages.get(stage, updates or 'Auditing...')

    def _is_valid_compliance_output(self, data: Any) -> bool:
        """Validate that the output contains expected compliance audit fields."""
        if not isinstance(data, dict):
            return False
        
        expected_fields = {
            'agent', 'action', 'sources_used', 'sources_trust',
            'rules_referenced', 'data_analyzed', 'reason', 'status'
        }
        
        return all(field in data for field in expected_fields)

    def _format_compliance_summary(self, audit_data: Dict[str, Any]) -> str:
        """Format a human-readable summary of the compliance audit."""
        agent = audit_data.get('agent', 'Unknown')
        action = audit_data.get('action', 'Unknown')
        sources_trust = audit_data.get('sources_trust', 'Unknown')
        status = audit_data.get('status', 'Unknown')
        sources_count = len(audit_data.get('sources_used', []))
        rules_count = len(audit_data.get('rules_referenced', []))
        
        return (f"Compliance Audit Complete!\n"
                f"Agent Audited: {agent}\n"
                f"Action: {action}\n"
                f"Sources Validated: {sources_count} ({sources_trust})\n"
                f"Rules Checked: {rules_count}\n"
                f"Final Status: {status}\n"
                f"Full audit report available in artifact.")

    async def cancel(
        self, request: RequestContext, event_queue: EventQueue
    ) -> Task | None:
        raise ServerError(error=UnsupportedOperationError("Compliance audit cannot be cancelled"))