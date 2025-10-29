from typing import Optional, List, Dict, Any
import time

from core.db import get_connection_pool, get_by_id, get_by_property, delete_by_id
from core.db.schemas import Node
from core.db.schemas.session_objects import Session


def retry_with_exponential_backoff(func, max_retries=3, initial_delay=0.1):
    """
    Retry a function with exponential backoff (T078).
    
    Args:
        func: Function to retry
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
    
    Returns:
        Result of the function call
    """
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            delay = initial_delay * (2 ** attempt)
            print(f"Retry attempt {attempt + 1}/{max_retries} after {delay}s delay: {e}")
            time.sleep(delay)
    return None


def create_session(
    session_id: Optional[str] = None, title: str = "New Session", user_id: Optional[str] = None
) -> Session:
    pool = get_connection_pool()
    with pool.get_connection() as db:
        session = Session(session_id=session_id, title=title, user_id=user_id)

        db._execute(*session.create())
        return session


def create_db_session(
    session_id: str,
    user_id: Optional[str] = None,
    title: str = "New Session",
    conversation_history: Optional[List[Dict[str, Any]]] = None,
    enabled_tools: Optional[List[str]] = None,
    disabled_tools: Optional[List[str]] = None,
    mcp_initialized: bool = False,
    agent_config: Optional[Dict[str, Any]] = None,
) -> Session:
    """
    Create a new session in the database with full initialization.
    
    Args:
        session_id: Unique session identifier
        user_id: Optional user identifier for multi-user scenarios
        title: Session title
        conversation_history: Initial conversation history
        enabled_tools: List of enabled tools
        disabled_tools: List of disabled tools
        mcp_initialized: Whether MCP is initialized
        agent_config: Agent configuration dictionary
    
    Returns:
        Created Session instance
    """
    pool = get_connection_pool()
    with pool.get_connection() as db:
        session = Session(
            session_id=session_id,
            user_id=user_id,
            title=title,
            conversation_history=conversation_history or [],
            enabled_tools=enabled_tools or [],
            disabled_tools=disabled_tools or [],
            mcp_initialized=mcp_initialized,
            agent_config=agent_config or {},
        )

        db._execute(*session.create())
        return session


def get_session_by_id(session_id: str) -> Optional[Session]:
    result = get_by_property(Session, "session_id", session_id, fetch_one=True)

    if not result:
        return None

    return Session.from_dict(result)


def get_all_sessions(user_id: Optional[str] = None) -> List[Session]:
    if user_id:
        pool = get_connection_pool()
        with pool.get_connection() as db:
            q = "MATCH (n:`SESSION` {is_active: $is_active, user_id: $user_id}) RETURN n"
            db._cur.execute(q, {"is_active": True, "user_id": user_id})
            results = [dict(row[0].properties) for row in db._cur.fetchall()]
    else:
        results = get_by_property(Session, "is_active", True)

    if not results:
        return []

    return [Session.from_dict(session) for session in results]


def update_session(session: Session) -> None:
    pool = get_connection_pool()
    with pool.get_connection() as db:
        q = f"MATCH (n:`{Session.label()}` {{session_id: $session_id}}) SET n += $props RETURN n"
        props = session.to_dict()
        db._execute(q, {"session_id": str(session.session_id), "props": props})


def save_session_state(
    session_id: str,
    conversation_history: List[Dict[str, Any]],
    enabled_tools: List[str],
    disabled_tools: List[str],
    mcp_initialized: bool,
    agent_config: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Save session state to database with logging and error handling (T077, T079).
    """
    try:
        session = get_session_by_id(session_id)

        if not session:
            session = Session(session_id=session_id, title=f"Session {session_id[:8]}")
            pool = get_connection_pool()
            with pool.get_connection() as db:
                db._execute(*session.create())
            print(f"Created new session in database: {session_id}")

        session.update_conversation_history(conversation_history)
        session.update_tool_states(enabled_tools, disabled_tools)
        session.set_mcp_initialized(mcp_initialized)
        if agent_config:
            session.update_agent_config(agent_config)

        update_session(session)
        print(f"Saved session state for {session_id}: {len(conversation_history)} messages")
    except Exception as e:
        print(f"Error saving session state for {session_id}: {e}")
        # Graceful degradation - continue with in-memory state
        raise


def restore_session_state(session_id: str) -> Optional[Dict[str, Any]]:
    session = get_session_by_id(session_id)

    if not session:
        return None

    return {
        "session_id": session.session_id,
        "title": session.title,
        "conversation_history": session.conversation_history,
        "enabled_tools": session.enabled_tools,
        "disabled_tools": session.disabled_tools,
        "mcp_initialized": session.mcp_initialized,
        "agent_config": session.agent_config,
        "last_activity": session.last_activity,
        "conversation_count": session.conversation_count,
    }


def delete_session(session_id: str) -> None:
    """
    Delete a session and cascade delete associated debug events (T040).
    """
    from core.db.debug import delete_debug_events_by_session
    
    # First delete associated debug events
    try:
        deleted_count = delete_debug_events_by_session(session_id)
        print(f"Deleted {deleted_count} debug events for session {session_id}")
    except Exception as e:
        print(f"Warning: Failed to delete debug events: {e}")
    
    # Then delete the session
    session = get_session_by_id(session_id)
    if session:
        return delete_by_id(Session, str(session.id))
