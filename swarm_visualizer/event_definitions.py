from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import time

class BaseEvent(BaseModel):
    timestamp: float = Field(default_factory=time.time)
    event_type: str

class SwarmRunStartEvent(BaseEvent):
    event_type: str = "SWARM_RUN_START"
    config: Dict[str, Any]

class SwarmRunEndEvent(BaseEvent):
    event_type: str = "SWARM_RUN_END"
    final_result: Optional[Any] = None

class AgentDefinitionEvent(BaseEvent):
    event_type: str = "AGENT_DEFINITION"
    agent_id: str
    name: str
    description: Optional[str] = None
    instructions_hash: str # MD5 hash of instructions
    tools: List[str] # List of tool names

class AgentActivateEvent(BaseEvent):
    event_type: str = "AGENT_ACTIVATE"
    agent_id: str
    swarm_run_id: Optional[str] = None # Optional, if part of a larger run

class AgentDeactivateEvent(BaseEvent): # For completion or error
    event_type: str = "AGENT_DEACTIVATE"
    agent_id: str
    reason: str # e.g., "completed", "error"
    error_details: Optional[str] = None

class AgentHandoffEvent(BaseEvent):
    event_type: str = "AGENT_HANDOFF"
    source_agent_id: str
    target_agent_id: str
    task_description: str
    details: Dict[str, Any] # e.g., arguments passed

class ToolCallAttemptEvent(BaseEvent):
    event_type: str = "TOOL_CALL_ATTEMPT"
    agent_id: str
    tool_name: str
    arguments: Dict[str, Any]

class ToolCallResultEvent(BaseEvent):
    event_type: str = "TOOL_CALL_RESULT"
    agent_id: str
    tool_name: str
    result: Any
    error: Optional[str] = None

class LLMRequestEvent(BaseEvent):
    event_type: str = "LLM_REQUEST"
    agent_id: str
    model_name: str
    prompt: str # Could be large, consider truncation or hashing if needed for storage
    settings: Dict[str, Any] # e.g., temperature, max_tokens

class LLMResponseEvent(BaseEvent):
    event_type: str = "LLM_RESPONSE"
    agent_id: str
    model_name: str
    response_text: str # Could be large
    # Potentially add usage statistics if available (tokens, etc.)

class AgentMessageEvent(BaseEvent):
    event_type: str = "AGENT_MESSAGE" # For general messages from agents not covered by other events
    agent_id: str
    message_type: str # E.g. "thought", "status_update"
    content: str

class ErrorEvent(BaseEvent):
    event_type: str = "ERROR_EVENT"
    source: str # e.g., "Swarm", "Agent", "Tool"
    error_message: str
    error_details: Optional[Dict[str, Any]] = None
