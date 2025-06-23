from pydantic import BaseModel
from typing import List, Optional

class QueryRequest(BaseModel):
    query: str


class QueryResponse(BaseModel):
    response: str
    used_tools: Optional[List[str]] = []
