from fastapi import APIRouter, Depends, HTTPException

from api.auth import get_api_key
from api.models import QueryRequest, QueryResponse, ToolsListResponse, ToolToggleRequest, ToolToggleResponse, ToolInfo
from agent import agent_instance
from core.mcp.sessions_manager import MCPSessionManager

session_manager = MCPSessionManager()

router = APIRouter(prefix="/api", dependencies=[Depends(get_api_key)])

@router.post("/ask", response_model=QueryResponse)
async def ask_agent(request: QueryRequest) -> QueryResponse:
    try:
        response, used_tools = await agent_instance.process_query(request.query)
        return QueryResponse(
            response=response, 
            used_tools=list(used_tools)
        )
    except Exception as e:
        return QueryResponse(response=f"Sorry, I encountered an error: {str(e)}")


@router.get("/tools", response_model=ToolsListResponse)
async def list_tools() -> ToolsListResponse:
    try:
        tools_info = agent_instance.get_tools()
        tools = [
            ToolInfo(
                name=info.name,
                description=info.description,
                enabled=info.enabled,
                parameters=info.parameters
            )
            for info in tools_info.values()
        ]
        return ToolsListResponse(tools=tools)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing tools: {str(e)}")


@router.post("/tools/toggle", response_model=ToolToggleResponse)
async def toggle_tool(request: ToolToggleRequest) -> ToolToggleResponse:
    try:
        if request.enabled:
            success = agent_instance.enable_tool(request.tool_name)
            action = "enabled"
        else:
            success = agent_instance.disable_tool(request.tool_name)
            action = "disabled"
        
        if not success:
            raise HTTPException(
                status_code=404, 
                detail=f"Tool '{request.tool_name}' not found"
            )
        
        return ToolToggleResponse(
            tool_name=request.tool_name,
            enabled=request.enabled,
            message=f"Tool '{request.tool_name}' has been {action}"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error toggling tool: {str(e)}")
