from datetime import datetime, timezone
from typing import Optional

from core.db.schemas import Node


class User(Node):
    def __init__(
        self,
        user_token: str,
        email: Optional[str] = None,
        name: Optional[str] = None,
    ):
        super().__init__()
        self.user_token = user_token
        self.user_id = user_token
        self.email = email
        self.name = name
        self.last_login = datetime.now(timezone.utc)

    def update_last_login(self) -> None:
        self.last_login = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
