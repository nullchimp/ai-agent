"""
Database operations for debug events.
Provides CRUD operations for DebugEvent nodes and their relationships.
"""

import json
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from core.db import get_connection_pool
from core.db.schemas.debug_objects import DebugEvent, DebugEventType


def create_debug_event(
    session_id: str,
    event_type: DebugEventType,
    message: str,
    data: Optional[Dict[str, Any]] = None,
    timestamp: Optional[datetime] = None
) -> DebugEvent:
    """
    Create and persist a debug event to the database.
    
    Args:
        session_id: ID of the session this event belongs to
        event_type: Type of debug event
        message: Human-readable description
        data: Optional event-specific data
        timestamp: Optional event timestamp (defaults to now)
    
    Returns:
        Created DebugEvent instance
    """
    pool = get_connection_pool()
    
    event = DebugEvent(
        event_id=str(uuid.uuid4()),
        session_id=session_id,
        event_type=event_type,
        message=message,
        data=data or {},
        timestamp=timestamp or datetime.now(timezone.utc)
    )
    
    try:
        with pool.get_connection() as db:
            # Create event node
            create_query, params = event.create()
            db._cur.execute(create_query, params)
            
            # Create relationship to session
            rel_query = """
                MATCH (e:DEBUG_EVENT {event_id: $event_id})
                MATCH (s:SESSION {session_id: $session_id})
                MERGE (e)-[:BELONGS_TO]->(s)
            """
            db._cur.execute(rel_query, {
                "event_id": event.event_id,
                "session_id": session_id
            })
            
            db._conn.commit()
    except Exception as e:
        print(f"Warning: Failed to persist debug event: {e}")
        # Don't crash - debug events are non-critical
    
    return event


def get_debug_events_by_session(
    session_id: str,
    event_type: Optional[DebugEventType] = None,
    limit: int = 1000,
    offset: int = 0
) -> List[DebugEvent]:
    """
    Retrieve debug events for a session.
    
    Args:
        session_id: Session to get events for
        event_type: Optional filter by event type
        limit: Maximum number of events to return
        offset: Number of events to skip (for pagination)
    
    Returns:
        List of DebugEvent instances ordered by timestamp
    """
    pool = get_connection_pool()
    
    try:
        with pool.get_connection() as db:
            if event_type:
                query = """
                    MATCH (e:DEBUG_EVENT {session_id: $session_id, event_type: $event_type})
                    RETURN e
                    ORDER BY e.timestamp ASC
                    SKIP $offset
                    LIMIT $limit
                """
                params = {
                    "session_id": session_id,
                    "event_type": event_type.value if isinstance(event_type, DebugEventType) else event_type,
                    "limit": limit,
                    "offset": offset
                }
            else:
                query = """
                    MATCH (e:DEBUG_EVENT {session_id: $session_id})
                    RETURN e
                    ORDER BY e.timestamp ASC
                    SKIP $offset
                    LIMIT $limit
                """
                params = {
                    "session_id": session_id,
                    "limit": limit,
                    "offset": offset
                }
            
            db._cur.execute(query, params)
            results = [dict(row[0].properties) for row in db._cur.fetchall()]
            
            return [DebugEvent.from_dict(r) for r in results]
    except Exception as e:
        print(f"Warning: Failed to retrieve debug events: {e}")
        return []


def delete_debug_events_by_session(session_id: str) -> int:
    """
    Delete all debug events for a session.
    
    Args:
        session_id: Session whose events should be deleted
    
    Returns:
        Number of events deleted
    """
    pool = get_connection_pool()
    
    try:
        with pool.get_connection() as db:
            query = """
                MATCH (e:DEBUG_EVENT {session_id: $session_id})
                DETACH DELETE e
                RETURN count(e) as deleted_count
            """
            db._cur.execute(query, {"session_id": session_id})
            result = db._cur.fetchone()
            db._conn.commit()
            
            return result[0] if result else 0
    except Exception as e:
        print(f"Warning: Failed to delete debug events: {e}")
        return 0


def count_debug_events_by_session(session_id: str) -> int:
    """
    Count debug events for a session.
    
    Args:
        session_id: Session to count events for
    
    Returns:
        Number of events
    """
    pool = get_connection_pool()
    
    try:
        with pool.get_connection() as db:
            query = """
                MATCH (e:DEBUG_EVENT {session_id: $session_id})
                RETURN count(e) as event_count
            """
            db._cur.execute(query, {"session_id": session_id})
            result = db._cur.fetchone()
            
            return result[0] if result else 0
    except Exception as e:
        print(f"Warning: Failed to count debug events: {e}")
        return 0
