from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union
import httpx
import os

from core import pretty_print, colorize_text, get_debug_capture

TIMEOUT = 30.0 # seconds

from core import is_debug
class Client:
    def __init__(
        self, 
        model: str,
        endpoint: str,
        timeout: Optional[float] = None
    ):
        self.api_key = os.environ.get("AZURE_OPENAI_API_KEY")
        self.model = model
        self.endpoint = endpoint

        if not (self.api_key and self.model and self.endpoint):
            raise ValueError("API key, model, and endpoint must be provided")

        self.timeout = timeout or TIMEOUT
        self.http_client = httpx.AsyncClient(timeout=self.timeout)

        if is_debug():
            print(colorize_text(f"<Client Initialized>", "grey"))
            print(colorize_text(f"<Timeout: {timeout}>", "grey"))
            print(colorize_text(f"<Model: {self.model}>\n", "grey"))
    
    async def make_request(
        self,
        messages: List[Dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        top_p: float = 1.0,
        tools: Optional[Any] = None
    ) -> Dict[str, Any]:
        raise NotImplementedError("Subclasses should implement this method")
    

class EmbeddingsClient(Client):
    def __init__(
        self,
        model: str = None,
        timeout: Optional[float] = None
    ):
        self.model = os.environ.get("AZURE_OPENAI_EMBEDDINGS_MODEL", model)
        self.endpoint = os.environ.get("AZURE_OPENAI_EMBEDDINGS_ENDPOINT", None)
        super().__init__(self.model, self.endpoint, timeout)

    async def make_request(
        self,
        messages: List[Dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        top_p: float = 1.0,
        tools: Optional[Any] = None
    ) -> Dict[str, Any]:
        """Make a request to the Azure OpenAI embeddings endpoint."""
        
        payload = {
            "input": messages[0],
            "model": self.model
        }
        
        headers = {
            "Content-Type": "application/json",
            "api-key": self.api_key
        }
        
        if is_debug():
            pretty_print("Agent -> Embeddings Model", payload, "magenta")
        debug_capture = get_debug_capture()
        if debug_capture:
            debug_capture.capture_llm_request(payload)
        
        response = await self.http_client.post(
            self.endpoint,
            headers=headers,
            json=payload
        )
        
        if response.status_code != 200:
            response_data = response.json()
            error_msg = "Unknown error"
            if response_data and "error" in response_data:
                error_msg = response_data["error"].get("message", "Unknown error")
            
            raise Exception(f"Embeddings API error ({response.status_code}): {error_msg}")
        
        response_json = response.json()
        if is_debug():
            pretty_print("Embeddings Model -> Agent", response_json, "cyan")
        debug_capture = get_debug_capture()
        if debug_capture:
            debug_capture.capture_llm_response(response_json)
            
        return response_json

class ChatClient(Client):
    def __init__(
        self,
        model: str = None,
        timeout: Optional[float] = None
    ):
        self.model = os.environ.get("AZURE_OPENAI_CHAT_MODEL", model)
        self.endpoint = os.environ.get("AZURE_OPENAI_CHAT_ENDPOINT", None)
        super().__init__(self.model, self.endpoint, timeout)

    async def make_request(
        self,
        messages: List[Dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        top_p: float = 1.0,
        tools: Optional[Any] = None
    ):
        if len(messages) == 1 and hasattr(messages[0], "raw_messages"):
            message_data = messages[0].raw_messages
        else:
            message_data = []
            for msg in messages:
                message = {"role": msg["role"]}
                
                # Only include content if it's not None
                if msg.get("content", None):
                    message["content"] = msg["content"]
                
                # Add other fields if they exist
                if msg.get("name", None):
                    message["name"] = msg["name"]
                    
                if msg.get("tool_call_id", None):
                    message["tool_call_id"] = msg["tool_call_id"]
                    
                if msg.get("tool_calls", None):
                    message["tool_calls"] = msg["tool_calls"]
                
                message_data.append(message)

        payload = {
            "model": self.model,
            "messages": message_data,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": top_p
        }
        
        if tools:
            payload["tools"] = tools

        headers = {
            "Content-Type": "application/json",
            "api-key": self.api_key
        }

        if is_debug():
            pretty_print("Agent -> Model", payload, "magenta")
        debug_capture = get_debug_capture()
        if debug_capture:
            debug_capture.capture_llm_request(payload)

        response = await self.http_client.post(
            self.endpoint,
            headers=headers,
            json=payload
        )

        if response.status_code != 200:
            response_data = response.json()
            error_msg = "Unknown error"
            if response_data and "error" in response_data:
                error_msg = response_data["error"].get("message", "Unknown error")
            
            raise Exception(f"API error ({response.status_code}): {error_msg}")
        
        response_json = response.json()
        if is_debug():
            pretty_print("Model -> Agent", response_json, "cyan")
        debug_capture = get_debug_capture()
        if debug_capture:
            debug_capture.capture_llm_response(response_json)

        return response_json