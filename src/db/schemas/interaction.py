import hashlib

from .base import Node


class Interaction(Node):
    def __init__(
        self,
        session_id: str,
        content: str,
        role: str,                   # "user", "assistant", "system", …
    ):
        super().__init__()
        self.session_id = session_id
        self.content = content
        self.content_hash = hashlib.sha256(content.encode()).hexdigest()
        self.role = role