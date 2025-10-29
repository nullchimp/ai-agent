"""
Debug-related schema objects for session storage.
Defines DebugEvent nodes and related enums.
"""

from datetime import datetime, timezone
from typing import Dict, Any, Optional
from enum import Enum
import json
import uuid

from core.db.schemas import Node


class DebugEventType(str, Enum):
    """Types of debug events that can be captured"""
    AGENT_TO_MODEL = "agent_to_model"      # LLM request from agent
    MODEL_TO_AGENT = "model_to_agent"      # LLM response to agent
    TOOL_CALL = "tool_call"                # Local tool invocation
    TOOL_RESULT = "tool_result"            # Local tool result
    TOOL_ERROR = "tool_error"              # Local tool error
    MCP_CALL = "mcp_call"                  # MCP tool invocation
    MCP_RESULT = "mcp_result"              # MCP tool result
    SYSTEM_INFO = "system_info"            # System-level information
    ERROR = "error"                        # General error event


class DebugEvent(Node):
    """
    Represents a single debug capture event associated with a session.
    
    Attributes:
        event_id: Unique identifier for this event
        session_id: Reference to parent session
        event_type: Type of event (from DebugEventType enum)
        message: Human-readable event description
        data: Event-specific data (stored as JSON)
        timestamp: When the event occurred
    """
    
    def __init__(
        self,
        event_id: Optional[str] = None,
        session_id: Optional[str] = None,
        event_type: Optional[DebugEventType] = None,
        message: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None,
    ):
        super().__init__()
        self.event_id = event_id or str(uuid.uuid4())
        self.session_id = session_id
        self.event_type = event_type.value if isinstance(event_type, DebugEventType) else event_type
        self.message = message or ""
        self.data = data or {}
        self.timestamp = timestamp or datetime.now(timezone.utc)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert debug event to dictionary for storage"""
        result = super().to_dict()
        # Ensure data is JSON serializable
        if isinstance(result.get('data'), dict):
            result['data'] = json.dumps(result['data'])
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DebugEvent":
        """Create DebugEvent from dictionary"""
        data_copy = data.copy()
        
        # Parse JSON data field if it's a string
        if 'data' in data_copy and isinstance(data_copy['data'], str):
            try:
                data_copy['data'] = json.loads(data_copy['data'])
            except (json.JSONDecodeError, TypeError):
                data_copy['data'] = {}
        
        # Parse timestamp if it's a string
        if 'timestamp' in data_copy and isinstance(data_copy['timestamp'], str):
            try:
                data_copy['timestamp'] = datetime.fromisoformat(data_copy['timestamp'])
            except (ValueError, TypeError):
                data_copy['timestamp'] = datetime.now(timezone.utc)
        
        # Parse event_type to enum if needed
        if 'event_type' in data_copy and isinstance(data_copy['event_type'], str):
            try:
                data_copy['event_type'] = DebugEventType(data_copy['event_type'])
            except ValueError:
                # Keep as string if not a valid enum value
                pass
        
        return super().from_dict(data_copy)
