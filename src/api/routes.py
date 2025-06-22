import os
from fastapi import APIRouter

from api.auth import ApiKeyDep
from api.models import QueryRequest, QueryResponse
from agent import Agent
from core.mcp.sessions_manager import MCPSessionManager


router = APIRouter(prefix="/api")

# Global agent instance
agent = Agent()
session_manager = MCPSessionManager()

# Initialize MCP tools on startup
_initialized = False


async def _initialize_agent():
    global _initialized
    if _initialized:
        return
    
    try:
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config', 'mcp.json')
        await session_manager.discovery(config_path)
        for tool in session_manager.tools:
            agent.add_tool(tool)
        _initialized = True
    except Exception:
        # If MCP initialization fails, continue without it
        _initialized = True


@router.post("/ask", response_model=QueryResponse)
async def ask_agent(request: QueryRequest, api_key: ApiKeyDep) -> QueryResponse:
    await _initialize_agent()
    
    try:
        response = await agent.process_query(request.query)
        return QueryResponse(response=response)
    except Exception as e:
        return QueryResponse(response=f"Sorry, I encountered an error: {str(e)}")
