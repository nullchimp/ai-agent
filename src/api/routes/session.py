from fastapi import APIRouter, Depends, HTTPException, Response
import uuid

from agent import get_agent_instance, Agent, delete_agent_instance
from api.auth import get_api_key
from api.models import (
    QueryRequest,
    QueryResponse,
    ToolsListResponse,
    ToolToggleRequest,
    ToolToggleResponse,
    ToolInfo,
    DebugResponse,
    DebugRequest,
    NewSessionResponse,
    SessionListResponse,
    SessionInfo,
    SessionSwitchRequest,
    SessionSwitchResponse,
    SessionUpdateRequest,
    SessionUpdateResponse,
)
from core.debug_capture import (
    get_debug_capture_instance,
    get_all_debug_events,
    clear_all_debug_events,
    delete_debug_capture_instance,
)
from core.db.session import (
    get_all_sessions,
    restore_session_state,
    get_session_by_id,
    update_session,
)

router = APIRouter(
    prefix="/api/session/{session_id}", dependencies=[Depends(get_api_key)]
)
sessions_router = APIRouter(prefix="/api/sessions", dependencies=[Depends(get_api_key)])


@router.get("", response_model=NewSessionResponse)
async def get_session(session_id: str):
    try:
        if session_id == "new":
            session_id = str(uuid.uuid4())

        await get_agent_instance(session_id)
        get_debug_capture_instance(session_id)
        return NewSessionResponse(session_id=session_id, message="Session is active")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error initializing agent: {str(e)}"
        )


@router.delete("")
async def delete_session(session_id: str):
    if delete_agent_instance(session_id):
        # Also clean up the debug capture instance for this session
        delete_debug_capture_instance(session_id)
        return Response(status_code=204)
    else:
        raise HTTPException(status_code=404, detail="Session not found")


@router.post("/ask", response_model=QueryResponse)
async def ask_agent(
    session_id: str,
    request: QueryRequest,
    agent_instance: Agent = Depends(get_agent_instance),
) -> QueryResponse:
    try:
        # Debug capture is now per-session, no need to set session_id
        response, used_tools = await agent_instance.process_query(request.query)
        return QueryResponse(response=response, used_tools=list(used_tools))
    except Exception as e:
        return QueryResponse(response=f"Sorry, I encountered an error: {str(e)}")


@router.get("/tools", response_model=ToolsListResponse)
async def list_tools(
    agent_instance: Agent = Depends(get_agent_instance),
) -> ToolsListResponse:
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


@router.post("/tools/toggle", response_model=ToolToggleResponse)
async def toggle_tool(
    request: ToolToggleRequest, agent_instance: Agent = Depends(get_agent_instance)
) -> ToolToggleResponse:
    try:
        if request.enabled:
            success = agent_instance.enable_tool(request.tool_name)
            action = "enabled"
        else:
            success = agent_instance.disable_tool(request.tool_name)
            action = "disabled"

        if not success:
            raise HTTPException(
                status_code=404, detail=f"Tool '{request.tool_name}' not found"
            )

        return ToolToggleResponse(
            tool_name=request.tool_name,
            enabled=request.enabled,
            message=f"Tool '{request.tool_name}' has been {action}",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error toggling tool: {str(e)}")


@router.get("/debug", response_model=DebugResponse)
async def get_debug_info(session_id: str) -> DebugResponse:
    try:
        events = get_all_debug_events(session_id)
        debug_events = [
            {
                "event_type": event["event_type"],
                "message": event["message"],
                "data": event["data"],
                "timestamp": event["timestamp"],
                "session_id": event["session_id"],
            }
            for event in events
        ]
        # For checking if enabled, use the specific session
        capture = get_debug_capture_instance(session_id)
        return DebugResponse(events=debug_events, enabled=capture.is_enabled())
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving debug info: {str(e)}"
        )


@router.post("/debug/toggle", response_model=DebugResponse)
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


@router.delete("/debug")
async def clear_debug_events(session_id: str) -> Response:
    try:
        clear_all_debug_events(session_id)
        return Response(status_code=204)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error clearing debug events: {str(e)}"
        )


@sessions_router.get("", response_model=SessionListResponse)
async def list_all_sessions() -> SessionListResponse:
    try:
        sessions = get_all_sessions()
        session_infos = [
            SessionInfo(
                session_id=session.session_id,
                title=session.title,
                last_activity=session.last_activity.isoformat(),
                conversation_count=session.conversation_count,
                is_active=session.is_active,
            )
            for session in sessions
        ]
        return SessionListResponse(sessions=session_infos)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing sessions: {str(e)}")


@sessions_router.post("/switch", response_model=SessionSwitchResponse)
async def switch_session(request: SessionSwitchRequest) -> SessionSwitchResponse:
    try:
        session_state = restore_session_state(request.session_id)

        if not session_state:
            raise HTTPException(
                status_code=404, detail=f"Session {request.session_id} not found"
            )

        agent = await get_agent_instance(request.session_id)

        return SessionSwitchResponse(
            session_id=session_state["session_id"],
            title=session_state["title"],
            message=f"Successfully switched to session {session_state['title']}",
            conversation_history=session_state["conversation_history"],
            enabled_tools=session_state["enabled_tools"],
            mcp_initialized=session_state["mcp_initialized"],
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error switching session: {str(e)}"
        )


@router.patch("", response_model=SessionUpdateResponse)
async def update_session_metadata(
    session_id: str, request: SessionUpdateRequest
) -> SessionUpdateResponse:
    try:
        session = get_session_by_id(session_id)

        if not session:
            raise HTTPException(
                status_code=404, detail=f"Session {session_id} not found"
            )

        if request.title:
            session.title = request.title
            session.update_activity()
            update_session(session)

        return SessionUpdateResponse(
            session_id=session.session_id,
            title=session.title,
            message="Session updated successfully",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating session: {str(e)}")
