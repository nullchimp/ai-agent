from fastapi import APIRouter, Depends, HTTPException

from api.auth import get_api_key
from api.models import (
    QueryRequest, QueryResponse, ToolsListResponse, ToolToggleRequest, 
    ToolToggleResponse, ToolInfo, DebugResponse, DebugRequest
)
from agent import agent_instance
from core.mcp.sessions_manager import MCPSessionManager
from core.debug_capture import debug_capture
import uuid

session_manager = MCPSessionManager()

router = APIRouter(prefix="/api", dependencies=[Depends(get_api_key)])

@router.post("/ask", response_model=QueryResponse)
async def ask_agent(request: QueryRequest) -> QueryResponse:
    try:
        # Generate a session ID for this request to track debug information
        session_id = str(uuid.uuid4())
        debug_capture.set_session_id(session_id)
        
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
            for info in tools_info
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

@router.get("/debug", response_model=DebugResponse)
async def get_debug_info(session_id: str = None) -> DebugResponse:
    try:
        events = debug_capture.get_events(session_id)
        debug_events = [
            {
                "event_type": event["event_type"],
                "message": event["message"],
                "data": event["data"],
                "timestamp": event["timestamp"],
                "session_id": event["session_id"]
            }
            for event in events
        ]
        return DebugResponse(events=debug_events, enabled=debug_capture.is_enabled())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving debug info: {str(e)}")

@router.post("/debug/toggle", response_model=DebugResponse)
async def toggle_debug(request: DebugRequest) -> DebugResponse:
    try:
        if request.enabled:
            debug_capture.enable()
        else:
            debug_capture.disable()
        
        return DebugResponse(events=[], enabled=debug_capture.is_enabled())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error toggling debug: {str(e)}")

@router.delete("/debug")
async def clear_debug(session_id: str = None):
    try:
        debug_capture.clear_events(session_id)
        return {"message": "Debug events cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing debug events: {str(e)}")
