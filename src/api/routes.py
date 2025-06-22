import os
from fastapi import APIRouter

from api.auth import ApiKeyDep
from api.models import QueryRequest, QueryResponse
from agent import Agent
from core.mcp.sessions_manager import MCPSessionManager

agent = Agent()
session_manager = MCPSessionManager()

router = APIRouter(prefix="/api")

@router.post("/ask", response_model=QueryResponse)
async def ask_agent(request: QueryRequest, api_key: ApiKeyDep) -> QueryResponse:
    try:
        response = await agent.process_query(request.query)
        return QueryResponse(response=response)
    except Exception as e:
        return QueryResponse(response=f"Sorry, I encountered an error: {str(e)}")
