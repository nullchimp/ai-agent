from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class SessionStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class ConversationMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    role: str
    content: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)
    used_tools: List[str] = Field(default_factory=list)


class AgentSession(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: Optional[str] = None
    title: str = "New Session"
    status: SessionStatus = SessionStatus.ACTIVE
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_activity: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)
    conversation_history: List[ConversationMessage] = Field(default_factory=list)
    
    def add_message(self, role: str, content: str, used_tools: List[str] = None) -> ConversationMessage:
        message = ConversationMessage(
            role=role,
            content=content,
            used_tools=used_tools or []
        )
        self.conversation_history.append(message)
        self.last_activity = datetime.now(timezone.utc)
        return message
    
    def get_recent_messages(self, count: int = 10) -> List[ConversationMessage]:
        return self.conversation_history[-count:] if self.conversation_history else []
    
    def update_activity(self) -> None:
        self.last_activity = datetime.now(timezone.utc)