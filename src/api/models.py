from pydantic import BaseModel
from typing import List, Optional

class QueryRequest(BaseModel):
    query: str


class QueryResponse(BaseModel):
    response: str
    used_tools: Optional[List[str]] = []


class ToolInfo(BaseModel):
    name: str
    description: str
    enabled: bool
    parameters: dict


class ToolsListResponse(BaseModel):
    tools: List[ToolInfo]


class ToolToggleRequest(BaseModel):
    tool_name: str
    enabled: bool


class ToolToggleResponse(BaseModel):
    tool_name: str
    enabled: bool
    message: str
