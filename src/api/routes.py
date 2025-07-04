from fastapi import APIRouter, Depends, HTTPException, Response
from typing import Optional
import uuid

from agent import get_agent_instance, Agent, delete_agent_instance
from api.auth import get_api_key
from api.models import (
    QueryRequest, QueryResponse, ToolsListResponse, ToolToggleRequest,
    ToolToggleResponse, ToolInfo, DebugResponse, DebugRequest, NewSessionResponse,
    SessionInfoResponse, SessionListResponse, MessageResponse, MemoryContextResponse
)
from core.debug_capture import get_debug_capture_instance, get_all_debug_events, clear_all_debug_events, delete_debug_capture_instance
from core.storage.session_manager import get_session_manager

session_router = APIRouter(prefix="/api")
api_router = APIRouter(prefix="/api/{session_id}", dependencies=[Depends(get_api_key)])

@session_router.get("/session/{session_id}", response_model=NewSessionResponse)
async def get_session(session_id: str):
    try:
        session_manager = get_session_manager()
        
        if session_id == "new":
            # Create a new persistent session
            session = await session_manager.create_session()
            session_id = session.session_id
        else:
            # Check if session exists in persistent storage
            session = await session_manager.get_session(session_id)
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")

        # Initialize agent and debug capture for the session
        await get_agent_instance(session_id)
        get_debug_capture_instance(session_id)
        
        return NewSessionResponse(session_id=session_id, message="Session is active")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error initializing session: {str(e)}")


@session_router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    try:
        session_manager = get_session_manager()
        
        # Delete from persistent storage
        deleted = await session_manager.delete_session(session_id)
        
        # Clean up in-memory instances
        delete_agent_instance(session_id)
        delete_debug_capture_instance(session_id)
        
        if deleted:
            return Response(status_code=204)
        else:
            raise HTTPException(status_code=404, detail="Session not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting session: {str(e)}")


@session_router.get("/session/{session_id}/info", response_model=SessionInfoResponse)
async def get_session_info(session_id: str):
    try:
        session_manager = get_session_manager()
        session = await session_manager.get_session(session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        conversation_history = [
            MessageResponse(
                id=msg.id,
                role=msg.role,
                content=msg.content,
                timestamp=msg.timestamp,
                used_tools=msg.used_tools
            )
            for msg in session.conversation_history
        ]
        
        return SessionInfoResponse(
            session_id=session.session_id,
            title=session.title,
            status=session.status.value,
            created_at=session.created_at,
            last_activity=session.last_activity,
            message_count=len(session.conversation_history),
            conversation_history=conversation_history
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving session info: {str(e)}")


@session_router.get("/sessions", response_model=SessionListResponse)
async def list_sessions(user_id: Optional[str] = None, limit: int = 50):
    try:
        session_manager = get_session_manager()
        sessions = await session_manager.storage_manager.session_repo.list_sessions(
            user_id=user_id, 
            limit=limit
        )
        
        session_responses = []
        for session in sessions:
            session_responses.append(SessionInfoResponse(
                session_id=session.session_id,
                title=session.title,
                status=session.status.value,
                created_at=session.created_at,
                last_activity=session.last_activity,
                message_count=len(session.conversation_history),
                conversation_history=[]  # Don't include full history in list view
            ))
        
        return SessionListResponse(sessions=session_responses)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing sessions: {str(e)}")


@api_router.get("/memory/context", response_model=MemoryContextResponse)
async def get_memory_context(session_id: str, query: str = ""):
    try:
        session_manager = get_session_manager()
        context = await session_manager.get_context_for_response(session_id, query)
        
        return MemoryContextResponse(
            working_memory=context["memory_context"]["working_memory"],
            episodic_memory=context["memory_context"]["episodic_memory"],
            semantic_memory=context["memory_context"]["semantic_memory"],
            recent_messages=context["recent_messages"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving memory context: {str(e)}")


@api_router.post("/ask", response_model=QueryResponse)
async def ask_agent(session_id: str, request: QueryRequest, agent_instance: Agent = Depends(get_agent_instance)) -> QueryResponse:
    try:
        session_manager = get_session_manager()
        
        # Add user message to persistent storage
        await session_manager.add_message(
            session_id=session_id,
            role="user",
            content=request.query
        )
        
        # Get memory context for the response
        context = await session_manager.get_context_for_response(session_id, request.query)
        
        # Process query with agent (this could be enhanced to use memory context)
        response, used_tools = await agent_instance.process_query(request.query)
        
        # Add agent response to persistent storage  
        await session_manager.add_message(
            session_id=session_id,
            role="assistant",
            content=response,
            used_tools=list(used_tools)
        )
        
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
