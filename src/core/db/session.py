from typing import Optional, List, Dict, Any

from core.db import get_connection_pool, get_by_id, get_by_property, delete_by_id
from core.db.schemas import Node
from core.db.schemas.session_objects import Session


def create_session(
    session_id: Optional[str] = None, title: str = "New Session"
) -> Session:
    pool = get_connection_pool()
    with pool.get_connection() as db:
        session = Session(session_id=session_id, title=title)

        db._execute(*session.create())
        return session


def get_session_by_id(session_id: str) -> Optional[Session]:
    result = get_by_property(Session, "session_id", session_id, fetch_one=True)

    if not result:
        return None

    return Session.from_dict(result)


def get_all_sessions() -> List[Session]:
    results = get_by_property(Session, "is_active", True)

    if not results:
        return []

    return [Session.from_dict(session) for session in results]


def update_session(session: Session) -> None:
    pool = get_connection_pool()
    with pool.get_connection() as db:
        q = f"MATCH (n:`{Session.label()}` {{session_id: $session_id}}) SET n += $props RETURN n"
        db._execute(q, {"session_id": session.session_id, "props": session.to_dict()})


def save_session_state(
    session_id: str,
    conversation_history: List[Dict[str, Any]],
    enabled_tools: List[str],
    disabled_tools: List[str],
    mcp_initialized: bool,
    agent_config: Optional[Dict[str, Any]] = None,
) -> None:
    session = get_session_by_id(session_id)

    if not session:
        session = Session(session_id=session_id, title=f"Session {session_id[:8]}")
        pool = get_connection_pool()
        with pool.get_connection() as db:
            db._execute(*session.create())

    session.update_conversation_history(conversation_history)
    session.update_tool_states(enabled_tools, disabled_tools)
    session.set_mcp_initialized(mcp_initialized)
    if agent_config:
        session.update_agent_config(agent_config)

    update_session(session)


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
    session = get_session_by_id(session_id)
    if session:
        return delete_by_id(Session, str(session.id))
