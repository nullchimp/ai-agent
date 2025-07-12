from datetime import datetime, timezone

from core.db.schemas import Node

class Session(Node):
    def __init__(
        self,
        title: str = "New Session",
        is_active: bool = True
    ):
        super().__init__()
        self.title = title
        self.is_active = is_active
        self.last_activity = datetime.now(timezone.utc)
        self.conversation_count = 0
        
    def update_activity(self) -> None:
        self.last_activity = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
        
    def increment_conversation(self) -> None:
        self.conversation_count += 1
        self.update_activity()