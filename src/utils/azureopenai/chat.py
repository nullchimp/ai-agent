
import os
from dataclasses import dataclass
from typing import Any, Dict, List

from .client import Client


DEFAULT_TEMPERATURE = 0.5
DEFAULT_MAX_TOKENS = 500
DEFAULT_API_KEY_ENV = "AZURE_OPENAI_API_KEY"
DEFAULT_TIMEOUT = 30.0

class Chat:
    def __init__(self, client, tool_map: Dict[str, Any] = {}):
        self.client = client
        self.tools = [tool.define() for _, tool in tool_map.items() if hasattr(tool, "define")]
    
    @classmethod
    def create(cls, tool_map = {}) -> 'Chat':
        api_key = os.environ.get(DEFAULT_API_KEY_ENV)
        if not api_key:
            raise ValueError(f"{DEFAULT_API_KEY_ENV} environment variable is required")
        
        client = Client(api_key=api_key)
        return cls(client, tool_map)
    
    def send_messages(
        self,
        messages: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        resp = self.client.make_request(
            messages=messages,
            temperature=0.7,
            max_tokens=32000,
            tools=self.tools
        )
        
        return resp