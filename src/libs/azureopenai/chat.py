"""
Chat module for Azure OpenAI API integration.
"""
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol
import time

from src.azureopenai.client import Client, Message, Response


# Default chat options
DEFAULT_TEMPERATURE = 0.5
DEFAULT_MAX_TOKENS = 500
DEFAULT_API_KEY_ENV = "AZURE_OPENAI_API_KEY"
DEFAULT_TIMEOUT = 30.0  # seconds


class ChatClient(Protocol):
    """Protocol defining the methods required for chat functionality."""
    
    def get_completion(
        self,
        messages: List[Message],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        top_p: float = 1.0,
        tools: Optional[Any] = None
    ) -> str:
        """Gets a completion from the model."""
        ...
    
    def make_request(
        self,
        messages: List[Message],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        top_p: float = 1.0,
        tools: Optional[Any] = None
    ) -> Response:
        """Makes a request to the API and returns the full response."""
        ...


@dataclass
class ResponseOptions:
    """Contains optional parameters for the chat response."""
    temperature: float = DEFAULT_TEMPERATURE
    max_tokens: int = DEFAULT_MAX_TOKENS
    tools: Optional[Any] = None


class Chat:
    """Simple interface for chat completions."""
    
    def __init__(self, client: ChatClient):
        """
        Initialize a Chat instance with the provided client.
        
        Args:
            client: A client implementing the ChatClient protocol
        """
        self.client = client
    
    @classmethod
    def create(cls) -> 'Chat':
        """
        Creates a new Chat instance with API key from environment variable.
        
        Returns:
            A new Chat instance
            
        Raises:
            ValueError: If the API key environment variable is not set
        """
        # Get API key from environment variable
        api_key = os.environ.get(DEFAULT_API_KEY_ENV)
        if not api_key:
            raise ValueError(f"{DEFAULT_API_KEY_ENV} environment variable is required")
        
        # Create a new client with default options
        client = Client(api_key=api_key)
        
        return cls(client)
    
    def send_prompt(self, system_role: str, user_prompt: str) -> str:
        """
        Sends a user prompt to the API and returns the response.
        
        Args:
            system_role: The system role/instructions
            user_prompt: The user's prompt/query
            
        Returns:
            The model's text response
        """
        # Create a messages array with system and user messages
        messages = [
            Message(role="system", content=system_role),
            Message(role="user", content=user_prompt)
        ]
        
        # Get just the completion text with the convenience method
        return self.client.get_completion(
            messages=messages,
            temperature=DEFAULT_TEMPERATURE,
            max_tokens=DEFAULT_MAX_TOKENS
        )
    
    def send_prompt_with_options(
        self,
        system_role: str,
        user_prompt: str,
        opts: ResponseOptions
    ) -> str:
        """
        Sends a user prompt with additional options and returns the full response.
        
        Args:
            system_role: The system role/instructions
            user_prompt: The user's prompt/query
            opts: Additional response options
            
        Returns:
            JSON string representing the full response
        """
        # Create a messages array with system and user messages
        messages = [
            Message(role="system", content=system_role),
            Message(role="user", content=user_prompt)
        ]
        
        # Make the request to get full response
        resp = self.client.make_request(
            messages=messages,
            temperature=opts.temperature,
            max_tokens=opts.max_tokens,
            tools=opts.tools
        )
        
        # Convert the full response to JSON
        return resp.to_json()
    
    def send_followup(
        self,
        messages: List[Dict[str, Any]],
        user_prompt: str
    ) -> str:
        """
        Sends a follow-up conversation with tool results.
        
        Args:
            messages: Previous conversation messages
            user_prompt: The user's follow-up prompt
            
        Returns:
            The model's text response
        """
        # Make the raw request with the provided messages
        resp = self.client.make_request(
            messages=[
                Message(
                    role="user",
                    content=user_prompt,
                    raw_messages=messages
                )
            ],
            temperature=DEFAULT_TEMPERATURE,
            max_tokens=DEFAULT_MAX_TOKENS
        )
        
        if not resp.choices:
            return ""
            
        return resp.choices[0].message.get("content", "")