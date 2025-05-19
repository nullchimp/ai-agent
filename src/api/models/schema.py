from typing import List, Optional
from pydantic import BaseModel, Field

class Message(BaseModel):
    role: str = Field(..., description="Role of the message sender (user, assistant, system)")
    content: str = Field(..., description="Content of the message")

class ChatRequest(BaseModel):
    messages: List[Message] = Field(..., description="List of messages in the conversation")
    max_tokens: Optional[int] = Field(None, description="Maximum number of tokens to generate")
    temperature: Optional[float] = Field(0.7, description="Temperature for response generation")

class ChatResponse(BaseModel):
    response: str = Field(..., description="Generated response from the AI agent")
    conversation_id: Optional[str] = Field(None, description="Unique identifier for the conversation")

class ToolRequest(BaseModel):
    tool_name: str = Field(..., description="Name of the tool to execute")
    parameters: dict = Field({}, description="Parameters for the tool execution")

class ToolResponse(BaseModel):
    result: dict = Field(..., description="Result of the tool execution")
    status: str = Field(..., description="Status of the tool execution")
