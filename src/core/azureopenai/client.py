from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union
import httpx
import os

from core import pretty_print, colorize_text

DEFAULT_TIMEOUT = 30.0 # seconds
DEFAULT_ENDPOINT = os.environ.get("AZURE_OPENAI_ENDPOINT", "https://api.azure.com/openai/v1")
DEFAULT_MODEL = os.environ.get("AZURE_OPENAI_MODEL", "GPT-4o")
DEFAULT_VERSION = os.environ.get("AZURE_OPENAI_VERSION", "2025-01-01-preview")

DEFAULT_URL = f"{DEFAULT_ENDPOINT}/{DEFAULT_MODEL}/#METOD_TYPE#?api-version={DEFAULT_VERSION}"
print("Default URL:", DEFAULT_URL)

from core import DEBUG
class Client:
    debug = DEBUG

    def __init__(
        self, 
        api_key: str, 
        endpoint: Optional[str] = None, 
        timeout: Optional[float] = None
    ):
        self.api_key = api_key
        self.endpoint = endpoint or DEFAULT_ENDPOINT
        self.timeout = timeout or DEFAULT_TIMEOUT
        self.http_client = httpx.AsyncClient(timeout=self.timeout)

        if Client.debug:
            print(colorize_text(f"<Client Initialized>", "grey"))
            print(colorize_text(f"<Endpoint: {endpoint or DEFAULT_ENDPOINT}>", "grey"))
            print(colorize_text(f"<Timeout: {timeout or DEFAULT_TIMEOUT}>", "grey"))
            print(colorize_text(f"<Model: {DEFAULT_MODEL}>\n", "grey"))
    
    def make_url(self, method: str) -> str:
        """Construct the endpoint URL based on the method."""
        url = DEFAULT_URL
        if "#METOD_TYPE#" in url:
            # Replace the placeholder with the actual method type
            print("URL1:", url)
            url = url.replace("#METOD_TYPE#", method)
            print("URL2:", url)
            return url
        else:
            raise ValueError("Endpoint does not contain #METOD_TYPE# placeholder")

    async def make_request(
        self,
        messages: List[Dict[str, Any]],
        model: Optional[str] = None,
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
            "model": model or DEFAULT_MODEL,
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

        if Client.debug:
            pretty_print("Agent -> Model", payload, "magenta")

        response = await self.http_client.post(
            self.make_url("chat/completions"),
            headers=headers,
            json=payload
        )

        if response.status_code != 200:
            response_data = response.json()
            error_msg = "Unknown error"
            if response_data and "error" in response_data:
                error_msg = response_data["error"].get("message", "Unknown error")
            
            raise Exception(f"API error ({response.status_code}): {error_msg}")
        
        if Client.debug:
            pretty_print("Model -> Agent", response.json(), "cyan")

        return response.json()
        
    async def get_completion(
        self,
        messages: List[Dict[str, Any]],
        **kwargs
    ) -> str:
        """Get just the completion text from a chat request."""
        response = await self.make_request(messages, **kwargs)
        
        if not response.get("choices") or len(response["choices"]) == 0:
            raise Exception("No completion choices returned from API")
            
        return response["choices"][0]["message"]["content"]
    
    async def make_embeddings_request(
        self,
        input: Union[str, List[str]],
        model: str = "text-embedding-ada-002"
    ) -> Dict[str, Any]:
        """Make a request to the Azure OpenAI embeddings endpoint."""
        
        payload = {
            "input": input,
            "model": model
        }
        
        headers = {
            "Content-Type": "application/json",
            "api-key": self.api_key
        }
        
        if Client.debug:
            pretty_print("Agent -> Embeddings Model", payload, "magenta")
        
        response = await self.http_client.post(
            self.make_url("embeddings"),
            headers=headers,
            json=payload
        )
        
        if response.status_code != 200:
            response_data = response.json()
            error_msg = "Unknown error"
            if response_data and "error" in response_data:
                error_msg = response_data["error"].get("message", "Unknown error")
            
            raise Exception(f"Embeddings API error ({response.status_code}): {error_msg}")
        
        if Client.debug:
            pretty_print("Embeddings Model -> Agent", response.json(), "cyan")
            
        return response.json()