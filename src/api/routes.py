from fastapi import APIRouter, Depends

from api.auth import get_api_key
from api.models import QueryRequest, QueryResponse
from agent import Agent
from core.mcp.sessions_manager import MCPSessionManager

agent = Agent()
session_manager = MCPSessionManager()

router = APIRouter(prefix="/api", dependencies=[Depends(get_api_key)])

@router.post("/ask", response_model=QueryResponse)
async def ask_agent(request: QueryRequest) -> QueryResponse:
    try:
        response = await agent.process_query(request.query)
        return QueryResponse(response=response)
    except Exception as e:
        return QueryResponse(response=f"Sorry, I encountered an error: {str(e)}")
