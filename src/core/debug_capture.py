import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import threading
from enum import Enum

def safe_serialize(obj: Any, max_length: int = 50000) -> Any:
    """Safely serialize objects, truncating if too large"""
    try:
        if isinstance(obj, str):
            if len(obj) > max_length:
                return obj[:max_length] + "... [truncated]"
            return obj
        elif isinstance(obj, dict):
            result = {}
            for key, value in obj.items():
                result[key] = safe_serialize(value, max_length // 10)
            return result
        elif isinstance(obj, list):
            if len(obj) > 100:  # Limit array size
                return [safe_serialize(item, max_length // 20) for item in obj[:100]] + ["... [truncated]"]
            return [safe_serialize(item, max_length // 10) for item in obj]
        else:
            # For other types, convert to string and check length
            str_repr = str(obj)
            if len(str_repr) > max_length:
                return str_repr[:max_length] + "... [truncated]"
            return obj
    except Exception:
        return "[Error serializing object]"

class DebugEventType(str, Enum):
    AGENT_TO_MODEL = "agent_to_model"
    MODEL_TO_AGENT = "model_to_agent"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    TOOL_ERROR = "tool_error"
    MCP_CALL = "mcp_call"
    MCP_RESULT = "mcp_result"
    SYSTEM_INFO = "system_info"
    ERROR = "error"

class DebugEvent:
    def __init__(
        self,
        event_type: DebugEventType,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None
    ):
        self.event_type = event_type
        self.message = message
        self.data = data or {}
        self.timestamp = timestamp or datetime.now()
        self.session_id = DebugCapture.get_current_session_id()

    def to_dict(self) -> Dict[str, Any]:
        try:
            return {
                "event_type": self.event_type,
                "message": self.message,
                "data": self.data,
                "timestamp": self.timestamp.isoformat(),
                "session_id": self.session_id
            }
        except Exception as e:
            # Fallback in case of serialization issues
            return {
                "event_type": self.event_type,
                "message": self.message,
                "data": {"error": f"Failed to serialize data: {str(e)}"},
                "timestamp": self.timestamp.isoformat(),
                "session_id": self.session_id
            }

class DebugCapture:
    _instance = None
    _lock = threading.Lock()
    _session_id = None

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(DebugCapture, cls).__new__(cls)
                    cls._instance._events = []
                    cls._instance._max_events = 1000
                    cls._instance._enabled = False
        return cls._instance

    def enable(self):
        self._enabled = True

    def disable(self):
        self._enabled = False

    def is_enabled(self) -> bool:
        return self._enabled

    def set_session_id(self, session_id: str):
        DebugCapture._session_id = session_id

    @classmethod
    def get_current_session_id(cls) -> Optional[str]:
        return cls._session_id

    def capture_event(
        self,
        event_type: DebugEventType,
        message: str,
        data: Optional[Dict[str, Any]] = None
    ):
        if not self._enabled:
            return

        # Safely serialize the data to prevent encoding issues
        safe_data = safe_serialize(data) if data else {}
        
        event = DebugEvent(event_type, message, safe_data)
        
        with self._lock:
            self._events.append(event)
            # Keep only the last max_events
            if len(self._events) > self._max_events:
                self._events = self._events[-self._max_events:]

    def get_events(self, session_id: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._lock:
            events = self._events
            if session_id:
                events = [e for e in events if e.session_id == session_id]
            return [event.to_dict() for event in events]

    def clear_events(self, session_id: Optional[str] = None):
        with self._lock:
            if session_id:
                self._events = [e for e in self._events if e.session_id != session_id]
            else:
                self._events = []

    def capture_llm_request(self, payload: Dict[str, Any]):
        self.capture_event(
            DebugEventType.AGENT_TO_MODEL,
            "LLM Request",
            {"payload": payload}
        )

    def capture_llm_response(self, response: Dict[str, Any]):
        self.capture_event(
            DebugEventType.MODEL_TO_AGENT,
            "LLM Response",
            {"response": response}
        )

    def capture_tool_call(self, tool_name: str, arguments: Dict[str, Any]):
        self.capture_event(
            DebugEventType.TOOL_CALL,
            f"Tool Call: {tool_name}",
            {"tool_name": tool_name, "arguments": arguments}
        )

    def capture_tool_result(self, tool_name: str, result: Any):
        self.capture_event(
            DebugEventType.TOOL_RESULT,
            f"Tool Result: {tool_name}",
            {"tool_name": tool_name, "result": result}
        )

    def capture_tool_error(self, tool_name: str, error: str):
        self.capture_event(
            DebugEventType.TOOL_ERROR,
            f"Tool Error: {tool_name}",
            {"tool_name": tool_name, "error": error}
        )

    def capture_mcp_call(self, tool_name: str, arguments: Dict[str, Any]):
        self.capture_event(
            DebugEventType.MCP_CALL,
            f"MCP Tool Call: {tool_name}",
            {"tool_name": tool_name, "arguments": arguments}
        )

    def capture_mcp_result(self, tool_name: str, result: Any):
        self.capture_event(
            DebugEventType.MCP_RESULT,
            f"MCP Tool Result: {tool_name}",
            {"tool_name": tool_name, "result": result}
        )

debug_capture = DebugCapture()