import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import threading
from enum import Enum

def safe_serialize(obj: Any, max_length: int = 50000) -> Any:
    """Safely serialize objects with color identifiers for important attributes"""
    
    # Color scheme mapping similar to pretty_print
    color_scheme = {
        "messages": "blue",
        "message": "blue", 
        "role": "cyan",
        "function": "green",
        "name": "yellow",
        "properties": "green",
        "arguments": "green",
        "parameters": "green", 
        "description": "green",
        "tools": "yellow",
        "tool_calls": "yellow",
        "tool_name": "yellow",
        "results": "yellow",
        "result": "yellow",
        "required": "red",
        "error": "red",
        "content": "magenta",
        "text": "magenta",
        "event_type": "cyan",
        "timestamp": "grey",
        "session_id": "grey",
        "payload": "blue",
        "response": "blue"
    }
    
    def should_truncate_key(key: str, value: Any) -> bool:
        """Determine if a key should be truncated based on importance"""
        if key in color_scheme:
            return False  # Important keys should not be truncated
        # Truncate large, less important data
        if isinstance(value, str) and len(value) > 200:
            return True
        elif isinstance(value, list) and len(value) > 20:
            return True
        elif isinstance(value, dict) and len(str(value)) > 1000:
            return True
        return False
    
    def truncate_json_strings(obj: Any, max_string_length: int = 100) -> Any:
        """Truncate long strings in JSON data recursively"""
        if isinstance(obj, str):
            if len(obj) > max_string_length:
                return obj[:max_string_length] + "...[truncated]"
            return obj
        
        if isinstance(obj, list):
            return [truncate_json_strings(item, max_string_length) for item in obj]
        
        if isinstance(obj, dict):
            result = {}
            for key, value in obj.items():
                result[key] = truncate_json_strings(value, max_string_length)
            return result
        
        return obj
    
    def serialize_with_colors(obj: Any, max_len: int, key_path: str = "") -> tuple[Any, dict]:
        """Serialize object and return both the serialized object and collected color metadata"""
        try:
            if isinstance(obj, str):
                if len(obj) > max_len:
                    return obj[:max_len] + "...[truncated]", {}
                return obj, {}
            elif isinstance(obj, dict):
                result = {}
                all_color_metadata = {}
                
                for key, value in obj.items():
                    current_key_path = f"{key_path}_{key}" if key_path else key
                    
                    if should_truncate_key(key, value):
                        result[key] = "...[truncated]"
                    else:
                        serialized_value, nested_colors = serialize_with_colors(value, max(max_len // 5, 1000), current_key_path)
                        result[key] = serialized_value
                        all_color_metadata.update(nested_colors)
                        
                    # Track color information for this key at current path
                    if key in color_scheme:
                        all_color_metadata[f"_{current_key_path}_color"] = color_scheme[key]
                
                return result, all_color_metadata
            elif isinstance(obj, list):
                if len(obj) > 50:  # Limit array size for unimportant lists
                    items = []
                    all_colors = {}
                    for item in obj[:10]:
                        serialized_item, item_colors = serialize_with_colors(item, max_len // 20, key_path)
                        items.append(serialized_item)
                        all_colors.update(item_colors)
                    items.append("...[truncated]")
                    return items, all_colors
                else:
                    items = []
                    all_colors = {}
                    for item in obj:
                        serialized_item, item_colors = serialize_with_colors(item, max(max_len // 5, 1000), key_path)
                        items.append(serialized_item)
                        all_colors.update(item_colors)
                    return items, all_colors
            else:
                # For other types, convert to string and check length
                str_repr = str(obj)
                if len(str_repr) > max_len:
                    return str_repr[:max_len] + "...[truncated]", {}
                return obj, {}
        except Exception:
            return "[Error serializing object]", {}
    
    # First truncate long strings, then apply serialization with color metadata
    truncated_obj = truncate_json_strings(obj, 100)
    serialized_result, color_metadata = serialize_with_colors(truncated_obj, max_length, "")
    
    # Add color metadata to the root level only if we have any
    if color_metadata and isinstance(serialized_result, dict):
        serialized_result["_debug_colors"] = color_metadata
    
    return serialized_result

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
        session_id: str,
        data: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None
    ):
        self.event_type = event_type
        self.message = message
        self.data = data or {}
        self.timestamp = timestamp or datetime.now()
        self.session_id = session_id

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
    _lock = threading.Lock()

    def __init__(self, session_id: str):
        self.session_id = session_id
        self._events = []
        self._max_events = 1000
        self._enabled = False

    def enable(self):
        self._enabled = True

    def disable(self):
        self._enabled = False

    def is_enabled(self) -> bool:
        return self._enabled

    def get_current_session_id(self) -> str:
        return self.session_id

    def capture_event(
        self,
        event_type: DebugEventType,
        message: str,
        data: Optional[Dict[str, Any]] = None
    ):
        if not self._enabled:
            return

        safe_data = safe_serialize(data) if data else {}
        
        event = DebugEvent(event_type, message, self.session_id, safe_data)
        
        with self._lock:
            self._events.append(event)
            if len(self._events) > self._max_events:
                self._events = self._events[-self._max_events:]

    def get_events(self) -> List[Dict[str, Any]]:
        with self._lock:
            return [event.to_dict() for event in self._events]

    def clear_events(self):
        with self._lock:
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


# Global session management
_debug_sessions = {}

def get_debug_capture_instance(session_id: str) -> DebugCapture:
    if not session_id:
        raise ValueError("Session ID must be provided to get debug capture instance.")
    
    if session_id not in _debug_sessions:
        _debug_sessions[session_id] = DebugCapture(session_id)
    
    return _debug_sessions[session_id]

def delete_debug_capture_instance(session_id: str) -> bool:
    if session_id in _debug_sessions:
        del _debug_sessions[session_id]
        return True
    return False

def get_all_debug_events(session_id: Optional[str] = None) -> List[Dict[str, Any]]:
    if session_id:
        if session_id in _debug_sessions:
            return _debug_sessions[session_id].get_events()
        return []
    
    all_events = []
    for capture in _debug_sessions.values():
        all_events.extend(capture.get_events())
    
    all_events.sort(key=lambda x: x['timestamp'])
    return all_events

def clear_all_debug_events(session_id: Optional[str] = None):
    if session_id:
        if session_id in _debug_sessions:
            _debug_sessions[session_id].clear_events()
    else:
        for capture in _debug_sessions.values():
            capture.clear_events()