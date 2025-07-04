from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime


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


class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    timestamp: datetime
    used_tools: List[str] = []


class SessionInfoResponse(BaseModel):
    session_id: str
    title: str
    status: str
    created_at: datetime
    last_activity: datetime
    message_count: int
    conversation_history: List[MessageResponse]


class SessionListResponse(BaseModel):
    sessions: List[SessionInfoResponse]


class MemoryContextResponse(BaseModel):
    working_memory: List[str]
    episodic_memory: List[str] 
    semantic_memory: List[str]
    recent_messages: List[Dict[str, str]]
