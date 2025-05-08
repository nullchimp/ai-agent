"""
Client module for Azure OpenAI API integration.
"""
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union
import json
import httpx


# Constants for API configuration
DEFAULT_TIMEOUT = 30.0  # seconds
DEFAULT_ENDPOINT = "https://timo-m6qhelh2-eastus2.cognitiveservices.azure.com/openai/deployments/custom-gpt-4.1/chat/completions?api-version=2025-01-01-preview"
DEFAULT_MODEL = "custom-gpt-4.1"


@dataclass
class Message:
    """Represents a chat message in the OpenAI API format."""
    role: str
    content: Optional[str] = None
    raw_messages: Optional[List[Dict[str, Any]]] = None


@dataclass
class ResponseChoice:
    """Represents a completion choice in the API response."""
    message: Dict[str, Any]


class ErrorResponse:
    """Represents an error from the API."""
    def __init__(self, error_data: Dict[str, Any]):
        self.message = error_data.get("message", "")


class Response:
    """Represents the API response structure."""
    def __init__(self, response_data: Dict[str, Any]):
        self.choices = []
        for choice_data in response_data.get("choices", []):
            message_data = choice_data.get("message", {})
            self.choices.append(ResponseChoice(message=message_data))
        
        error_data = response_data.get("error")
        self.error = ErrorResponse(error_data) if error_data else None

    def to_json(self) -> str:
        """Converts the response to a JSON string."""
        result = {
            "choices": [
                {
                    "message": choice.message
                } for choice in self.choices
            ]
        }
        if self.error:
            result["error"] = {"message": self.error.message}
        
        return json.dumps(result)

class Client:
    """Azure OpenAI API client."""
    
    def __init__(
        self, 
        api_key: str, 
        endpoint: Optional[str] = None, 
        timeout: Optional[float] = None
    ):
        self.api_key = api_key
        self.endpoint = endpoint or DEFAULT_ENDPOINT
        self.timeout = timeout or DEFAULT_TIMEOUT
        self.http_client = httpx.Client(timeout=self.timeout)
    
    def make_request(
        self,
        messages: List[Message],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        top_p: float = 1.0,
        tools: Optional[Any] = None
    ) -> Response:
        if len(messages) == 1 and messages[0].raw_messages:
            message_data = messages[0].raw_messages
        else:
            message_data = [
                {
                    "role": msg.role,
                    "content": msg.content
                } for msg in messages
            ]
        
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
        response = self.http_client.post(
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
        
        response_data = response.json()
        return Response(response_data)
    
    def get_completion(
        self,
        messages: List[Message],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        top_p: float = 1.0,
        tools: Optional[Any] = None
    ) -> str:
        response = self.make_request(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            tools=tools
        )
        
        if not response.choices:
            raise Exception("No completion choices returned")
        
        return response.choices[0].message.get("content", "")