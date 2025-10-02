from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class QueryRequest(BaseModel):
    query: str


class QueryResponse(BaseModel):
    response: str
    used_tools: Optional[List[str]] = []


class ToolInfo(BaseModel):
    name: str
    description: str
    enabled: bool
    source: str


class ToolsListResponse(BaseModel):
    tools: List[ToolInfo]


class ToolToggleRequest(BaseModel):
    tool_name: str
    enabled: bool


class ToolToggleResponse(BaseModel):
    tool_name: str
    enabled: bool
    message: str


class DebugEvent(BaseModel):
    event_type: str
    message: str
    data: Dict[str, Any]
    timestamp: str
    session_id: Optional[str] = None


class DebugResponse(BaseModel):
    events: List[DebugEvent]
    enabled: bool


class DebugRequest(BaseModel):
    enabled: bool


class NewSessionResponse(BaseModel):
    session_id: str
    message: str


class SessionInfo(BaseModel):
    session_id: str
    title: str
    last_activity: str
    conversation_count: int
    is_active: bool


class SessionListResponse(BaseModel):
    sessions: List[SessionInfo]


class SessionSwitchRequest(BaseModel):
    session_id: str


class SessionSwitchResponse(BaseModel):
    session_id: str
    title: str
    message: str
    conversation_history: List[Dict[str, Any]]
    enabled_tools: List[str]
    mcp_initialized: bool


class SessionUpdateRequest(BaseModel):
    title: Optional[str] = None


class SessionUpdateResponse(BaseModel):
    session_id: str
    title: str
    message: str
