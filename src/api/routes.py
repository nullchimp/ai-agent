from fastapi import APIRouter, Depends, HTTPException, Response
import uuid

from agent import get_agent_instance, Agent, delete_agent_instance
from api.auth import get_api_key
from api.models import (
    QueryRequest, QueryResponse, ToolsListResponse, ToolToggleRequest,
    ToolToggleResponse, ToolInfo, DebugResponse, DebugRequest, NewSessionResponse
)
from core.debug_capture import get_debug_capture_instance, get_all_debug_events, clear_all_debug_events, delete_debug_capture_instance

session_router = APIRouter(prefix="/api")
api_router = APIRouter(prefix="/api/{session_id}", dependencies=[Depends(get_api_key)])

@session_router.get("/session/{session_id}", response_model=NewSessionResponse)
async def get_session(session_id: str):
    try:
        if session_id == "new":
            session_id = str(uuid.uuid4())

        await get_agent_instance(session_id)
        get_debug_capture_instance(session_id)
        return NewSessionResponse(session_id=session_id, message="Session is active")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error initializing agent: {str(e)}")


@session_router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    if delete_agent_instance(session_id):
        # Also clean up the debug capture instance for this session
        delete_debug_capture_instance(session_id)
        return Response(status_code=204)
    else:
        raise HTTPException(status_code=404, detail="Session not found")


@api_router.post("/ask", response_model=QueryResponse)
async def ask_agent(session_id: str, request: QueryRequest, agent_instance: Agent = Depends(get_agent_instance)) -> QueryResponse:
    try:
        # Debug capture is now per-session, no need to set session_id
        response, used_tools = await agent_instance.process_query(request.query)
        return QueryResponse(
            response=response,
            used_tools=list(used_tools)
        )
    except Exception as e:
        return QueryResponse(response=f"Sorry, I encountered an error: {str(e)}")


@api_router.get("/tools", response_model=ToolsListResponse)
async def list_tools(agent_instance: Agent = Depends(get_agent_instance)) -> ToolsListResponse:
    try:
        tools_info = agent_instance.get_tools()
        tools = [
            ToolInfo(
                name=info.name,
                description=info.description,
                enabled=info.enabled,
                source=info.source,
            )
            for info in tools_info
        ]
        return ToolsListResponse(tools=tools)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing tools: {str(e)}")


@api_router.post("/tools/toggle", response_model=ToolToggleResponse)
async def toggle_tool(request: ToolToggleRequest, agent_instance: Agent = Depends(get_agent_instance)) -> ToolToggleResponse:
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


@api_router.get("/debug", response_model=DebugResponse)
async def get_debug_info(session_id: str) -> DebugResponse:
    try:
        events = get_all_debug_events(session_id)
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
        # For checking if enabled, use the specific session
        capture = get_debug_capture_instance(session_id)
        return DebugResponse(events=debug_events, enabled=capture.is_enabled())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving debug info: {str(e)}")


@api_router.post("/debug/toggle", response_model=DebugResponse)
async def toggle_debug(session_id: str, request: DebugRequest) -> DebugResponse:
    try:
        capture = get_debug_capture_instance(session_id)
        if request.enabled:
            capture.enable()
        else:
            capture.disable()

        return DebugResponse(events=[], enabled=capture.is_enabled())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error toggling debug: {str(e)}")


@api_router.delete("/debug")
async def clear_debug_events(session_id: str) -> Response:
    try:
        clear_all_debug_events(session_id)
        return Response(status_code=204)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing debug events: {str(e)}")
