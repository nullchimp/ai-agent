from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

from core.db.schemas import Node


class Session(Node):
    def __init__(
        self,
        title: str = "New Session",
        is_active: bool = True,
        session_id: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        enabled_tools: Optional[List[str]] = None,
        disabled_tools: Optional[List[str]] = None,
        mcp_initialized: bool = False,
        agent_config: Optional[Dict[str, Any]] = None,
    ):
        super().__init__()
        self.title = title
        self.is_active = is_active
        self.session_id = session_id or str(self.id)
        self.last_activity = datetime.now(timezone.utc)
        self.conversation_count = 0
        self.conversation_history = conversation_history or []
        self.enabled_tools = enabled_tools or []
        self.disabled_tools = disabled_tools or []
        self.mcp_initialized = mcp_initialized
        self.agent_config = agent_config or {}

    def update_activity(self) -> None:
        self.last_activity = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

    def increment_conversation(self) -> None:
        self.conversation_count += 1
        self.update_activity()

    def update_conversation_history(self, history: List[Dict[str, Any]]) -> None:
        self.conversation_history = history
        self.update_activity()

    def update_tool_states(
        self, enabled_tools: List[str], disabled_tools: List[str]
    ) -> None:
        self.enabled_tools = enabled_tools
        self.disabled_tools = disabled_tools
        self.update_activity()

    def set_mcp_initialized(self, initialized: bool) -> None:
        self.mcp_initialized = initialized
        self.update_activity()

    def update_agent_config(self, config: Dict[str, Any]) -> None:
        self.agent_config = config
        self.update_activity()
