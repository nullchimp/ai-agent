from datetime import datetime, timezone
from typing import Dict, Any, Optional

from .base import Node


class User(Node):
    def __init__(
        self,
        username: str,
        email: str = "",
        display_name: str = "",
    ):
        super().__init__()
        self.username = username
        self.email = email
        self.display_name = display_name or username


class Session(Node):
    def __init__(
        self,
        user_id: str,
        title: str = "New Session",
        agent_config: Optional[Dict[str, Any]] = None,
        is_active: bool = True,
    ):
        super().__init__()
        self.user_id = user_id
        self.title = title
        self.agent_config = agent_config or {}
        self.is_active = is_active
        self.last_activity = datetime.now(timezone.utc)

    def update_activity(self):
        self.last_activity = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)