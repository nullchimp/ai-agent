# Quickstart Guide: Database-Backed Session Storage

**Feature**: 001-session-storage  
**Date**: 2025-10-29  
**Target Audience**: Developers implementing this feature

---

## Overview

This guide walks you through implementing database-backed session storage that persists agent conversations and debug events to Memgraph. After completing this implementation, sessions will survive server restarts and support multi-user scenarios.

**Estimated Implementation Time**: 6-8 hours

---

## Prerequisites

### Required Knowledge
- Python 3.9+ and async/await patterns
- FastAPI framework basics
- Graph database concepts (nodes, relationships, Cypher queries)
- pytest for test-driven development

### Required Tools
- Docker and docker-compose (for Memgraph database)
- Python virtual environment (`.venv`)
- Memgraph Lab (for database visualization) - optional but recommended

### Required Files
All files listed in this guide exist in the repository. You'll be modifying existing files and creating new ones.

---

## Setup

### 1. Start Memgraph Database

```bash
# From repository root
cd docker
docker-compose up -d memgraph memgraph-lab

# Verify Memgraph is running
docker ps | grep memgraph

# Check logs
docker logs ai-agent-memgraph
```

**Expected Output**:
```
You are running Memgraph v2.x.x
Bolt server is listening on 0.0.0.0:7687
```

### 2. Verify Database Connection

```bash
# From repository root
python -c "
from src.core.db import get_connection_pool
pool = get_connection_pool()
with pool.get_connection() as db:
    result = db._execute('RETURN 1')
    print('✅ Database connection successful')
"
```

### 3. Create Database Indexes

```bash
# Create indexes for performance (run once)
python scripts/create_indexes.py
```

Or manually in Memgraph Lab (http://localhost:3000):
```cypher
CREATE INDEX ON :SESSION(session_id);
CREATE INDEX ON :SESSION(user_id);
CREATE INDEX ON :SESSION(is_active);
CREATE INDEX ON :SESSION(last_activity);
CREATE INDEX ON :DEBUG_EVENT(event_id);
CREATE INDEX ON :DEBUG_EVENT(session_id);
CREATE INDEX ON :DEBUG_EVENT(event_type);
CREATE INDEX ON :DEBUG_EVENT(timestamp);
```

---

## Implementation Workflow (TDD)

### Phase 1: Debug Event Persistence (New Functionality)

#### Step 1.1: Write Tests First

**File**: `tests/unit/test_debug_db_operations.py`

```python
import pytest
from datetime import datetime
from src.core.db.debug import (
    create_debug_event,
    get_debug_events_by_session,
    delete_debug_events_by_session
)
from src.core.db.schemas.debug_objects import DebugEvent, DebugEventType

class TestDebugEventPersistence:
    def test_create_debug_event(self):
        """Test creating a debug event in the database"""
        event = create_debug_event(
            session_id="test-session-001",
            event_type=DebugEventType.TOOL_CALL,
            message="Test tool call",
            data={"tool_name": "google_search", "query": "test"}
        )
        
        assert event.session_id == "test-session-001"
        assert event.event_type == DebugEventType.TOOL_CALL
        assert event.event_id is not None
    
    def test_get_debug_events_by_session(self):
        """Test retrieving debug events for a session"""
        session_id = "test-session-002"
        
        # Create multiple events
        create_debug_event(session_id, DebugEventType.TOOL_CALL, "Event 1", {})
        create_debug_event(session_id, DebugEventType.TOOL_RESULT, "Event 2", {})
        
        events = get_debug_events_by_session(session_id)
        
        assert len(events) >= 2
        assert all(e.session_id == session_id for e in events)
    
    def test_delete_debug_events_cascade(self):
        """Test that deleting session removes debug events"""
        session_id = "test-session-003"
        
        # Create events
        create_debug_event(session_id, DebugEventType.TOOL_CALL, "Event", {})
        
        # Delete events
        delete_debug_events_by_session(session_id)
        
        # Verify deletion
        events = get_debug_events_by_session(session_id)
        assert len(events) == 0
```

**Run tests** (they should FAIL):
```bash
pytest tests/unit/test_debug_db_operations.py -v
```

#### Step 1.2: Implement Debug Schemas

**File**: `src/core/db/schemas/debug_objects.py` (NEW)

```python
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from enum import Enum

from core.db.schemas import Node


class DebugEventType(str, Enum):
    AGENT_TO_MODEL = "agent_to_model"
    MODEL_TO_AGENT = "model_to_agent"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    TOOL_ERROR = "tool_error"
    MCP_CALL = "mcp_call"
    MCP_RESULT = "mcp_result"
    SYSTEM_INFO = "system_info"
    ERROR = "error"


class DebugEvent(Node):
    def __init__(
        self,
        event_id: str,
        session_id: str,
        event_type: DebugEventType,
        message: str,
        data: Dict[str, Any],
        timestamp: Optional[datetime] = None,
    ):
        super().__init__()
        self.event_id = event_id
        self.session_id = session_id
        self.event_type = event_type
        self.message = message
        self.data = data
        self.timestamp = timestamp or datetime.now(timezone.utc)
```

**Update**: `src/core/db/schemas/__init__.py`

```python
# Add at the end
from core.db.schemas.debug_objects import *
```

#### Step 1.3: Implement Debug CRUD Operations

**File**: `src/core/db/debug.py` (NEW)

```python
import json
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime

from core.db import get_connection_pool
from core.db.schemas.debug_objects import DebugEvent, DebugEventType


def create_debug_event(
    session_id: str,
    event_type: DebugEventType,
    message: str,
    data: Dict[str, Any],
    timestamp: Optional[datetime] = None
) -> DebugEvent:
    """Create and persist a debug event"""
    pool = get_connection_pool()
    
    event = DebugEvent(
        event_id=str(uuid.uuid4()),
        session_id=session_id,
        event_type=event_type,
        message=message,
        data=data,
        timestamp=timestamp
    )
    
    with pool.get_connection() as db:
        # Create event node
        create_query, params = event.create()
        db._execute(create_query, params)
        
        # Create relationship to session
        rel_query = """
            MATCH (e:DEBUG_EVENT {event_id: $event_id})
            MATCH (s:SESSION {session_id: $session_id})
            CREATE (e)-[:BELONGS_TO]->(s)
        """
        db._execute(rel_query, {
            "event_id": event.event_id,
            "session_id": session_id
        })
    
    return event


def get_debug_events_by_session(
    session_id: str,
    event_type: Optional[DebugEventType] = None,
    limit: int = 1000
) -> List[DebugEvent]:
    """Retrieve debug events for a session"""
    pool = get_connection_pool()
    
    with pool.get_connection() as db:
        if event_type:
            query = """
                MATCH (e:DEBUG_EVENT {session_id: $session_id, event_type: $event_type})
                RETURN e
                ORDER BY e.timestamp ASC
                LIMIT $limit
            """
            params = {
                "session_id": session_id,
                "event_type": event_type,
                "limit": limit
            }
        else:
            query = """
                MATCH (e:DEBUG_EVENT {session_id: $session_id})
                RETURN e
                ORDER BY e.timestamp ASC
                LIMIT $limit
            """
            params = {"session_id": session_id, "limit": limit}
        
        db._cur.execute(query, params)
        results = [dict(row[0].properties) for row in db._cur.fetchall()]
    
    return [DebugEvent.from_dict(r) for r in results]


def delete_debug_events_by_session(session_id: str) -> int:
    """Delete all debug events for a session"""
    pool = get_connection_pool()
    
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
```

#### Step 1.4: Run Tests (Should Pass Now)

```bash
pytest tests/unit/test_debug_db_operations.py -v
```

---

### Phase 2: Session Persistence Integration

#### Step 2.1: Write Integration Tests

**File**: `tests/integration/test_session_persistence.py`

```python
import pytest
from src.core.db.session import (
    create_session,
    get_session_by_id,
    save_session_state,
    restore_session_state,
    delete_session
)

class TestSessionPersistence:
    def test_session_survives_restart(self):
        """Test that session state is restored after simulated restart"""
        session_id = "test-restart-001"
        
        # Create session with state
        save_session_state(
            session_id=session_id,
            conversation_history=[
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi!"}
            ],
            enabled_tools=["google_search"],
            disabled_tools=["write_file"],
            mcp_initialized=True,
            agent_config={"model": "gpt-4"}
        )
        
        # Simulate restart - retrieve from database
        restored = restore_session_state(session_id)
        
        assert restored is not None
        assert len(restored["conversation_history"]) == 2
        assert "google_search" in restored["enabled_tools"]
        assert restored["mcp_initialized"] is True
    
    def test_session_deletion_cascade(self):
        """Test that deleting session removes debug events"""
        from src.core.db.debug import create_debug_event
        from src.core.db.schemas.debug_objects import DebugEventType
        
        session_id = "test-delete-001"
        
        # Create session
        create_session(session_id=session_id)
        
        # Create debug event
        create_debug_event(
            session_id=session_id,
            event_type=DebugEventType.TOOL_CALL,
            message="Test",
            data={}
        )
        
        # Delete session
        delete_session(session_id)
        
        # Verify session is gone
        session = get_session_by_id(session_id)
        assert session is None
```

**Run tests** (may fail initially):
```bash
pytest tests/integration/test_session_persistence.py -v
```

#### Step 2.2: Modify Agent to Use Database

**File**: `src/agent.py` (MODIFY)

Find the `Agent.__init__()` method and update:

```python
def __init__(self, session_id: str = "cli-session", restore_from_db: bool = False):
    self.session_id = session_id
    self.mcp_initialized = False
    self.history = []

    self.tools = {
        GitHubKnowledgebase(),
        GoogleSearch(),
        # ... other tools
    }
    self.chat = Chat.create(self.tools, session_id)

    if restore_from_db:
        self._restore_from_db()  # Load state from database
    else:
        for tool in self.chat.tools:
            tool.enable()
        self._update_system_prompt()
        
        # NEW: Save initial state to database
        from core.db.session import save_session_state
        save_session_state(
            session_id=self.session_id,
            conversation_history=self.history,
            enabled_tools=[t.name for t in self.chat.tools if t.enabled],
            disabled_tools=[t.name for t in self.chat.tools if not t.enabled],
            mcp_initialized=self.mcp_initialized,
            agent_config={}
        )
```

Add the restoration method:

```python
def _restore_from_db(self) -> None:
    """Restore session state from database"""
    from core.db.session import restore_session_state
    
    state = restore_session_state(self.session_id)
    if not state:
        # Session not found in DB - initialize fresh
        self._restore_from_db = False
        self.__init__(self.session_id, restore_from_db=False)
        return
    
    # Restore conversation history
    self.history = state.get("conversation_history", [])
    self.chat.history = self.history
    
    # Restore tool states
    enabled = set(state.get("enabled_tools", []))
    for tool in self.chat.tools:
        if tool.name in enabled:
            tool.enable()
        else:
            tool.disable()
    
    # Restore MCP state
    self.mcp_initialized = state.get("mcp_initialized", False)
    
    self._update_system_prompt()
```

#### Step 2.3: Update Session Save After Chat

Find where chat responses are generated and add save:

```python
# In the method that processes chat messages
async def chat(self, message: str) -> str:
    # ... existing chat logic ...
    
    # NEW: Save state after each message
    from core.db.session import save_session_state
    save_session_state(
        session_id=self.session_id,
        conversation_history=self.history,
        enabled_tools=[t.name for t in self.chat.tools if t.enabled],
        disabled_tools=[t.name for t in self.chat.tools if not t.enabled],
        mcp_initialized=self.mcp_initialized,
        agent_config={}
    )
    
    return response
```

---

### Phase 3: Debug Event Integration

#### Step 3.1: Modify DebugCapture to Persist Events

**File**: `src/core/debug_capture.py` (MODIFY)

Update the `capture_event` method:

```python
def capture_event(
    self,
    event_type: DebugEventType,
    message: str,
    data: Optional[Dict[str, Any]] = None
):
    if not self._enabled:
        return

    safe_data = safe_serialize(data) if data else {}
    
    event = DebugEvent(event_type, message, self.session_id, safe_data)
    
    with self._lock:
        self._events.append(event)
        if len(self._events) > self._max_events:
            self._events = self._events[-self._max_events:]
    
    # NEW: Persist to database
    try:
        from core.db.debug import create_debug_event
        create_debug_event(
            session_id=self.session_id,
            event_type=event_type,
            message=message,
            data=safe_data
        )
    except Exception as e:
        # Don't crash on DB errors - debug events are non-critical
        print(f"Warning: Failed to persist debug event: {e}")
```

---

### Phase 4: API Integration

#### Step 4.1: Update Session Route for Cache-DB Sync

**File**: `src/api/routes/session.py` (MODIFY)

```python
@router.get("/api/session/{session_id}")
async def get_session(session_id: str, user_id: str = Depends(get_user_id)):
    try:
        if session_id == "new":
            # Create new session
            from core.db.session import create_db_session
            session_id = str(uuid.uuid4())
            create_db_session(session_id=session_id, user_id=user_id)
        
        # Try to get agent instance (will load from DB if not in cache)
        agent = await get_agent_instance(session_id)
        
        # Get session state (from DB for accuracy)
        session_state = restore_session_state(session_id)
        if session_state:
            filtered_history = filter_system_messages(session_state["conversation_history"])
            return NewSessionResponse(
                session_id=session_id,
                message="Session restored" if len(filtered_history) > 0 else "Session is active",
                conversation_history=filtered_history,
                title=session_state.get("title", "New Session")
            )
        
        return NewSessionResponse(
            session_id=session_id,
            message="Session is active",
            conversation_history=[],
            title="New Session"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

Update `get_agent_instance()` to check database:

```python
async def get_agent_instance(session_id: str) -> Agent:
    # Check cache first
    if session_id in _agent_sessions:
        return _agent_sessions[session_id]
    
    # Cache miss - try to restore from database
    from core.db.session import get_session_by_id
    db_session = get_session_by_id(session_id)
    
    if db_session:
        # Session exists in DB - restore it
        agent = Agent(session_id, restore_from_db=True)
    else:
        # New session
        agent = Agent(session_id, restore_from_db=False)
    
    _agent_sessions[session_id] = agent
    return agent
```

---

## Testing

### Run All Tests

```bash
# Run all tests with coverage
pytest tests/ --cov=src/core/db --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Manual Testing

#### Test 1: Session Persistence

```bash
# Terminal 1: Start server
uvicorn src.api.app:app --reload

# Terminal 2: Create session and send message
curl -X GET http://localhost:8000/api/session/new \
  -H "X-API-Key: dev-api-key"

# Note the session_id from response
export SESSION_ID="<session-id-here>"

curl -X POST http://localhost:8000/api/session/$SESSION_ID/chat \
  -H "X-API-Key: dev-api-key" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, remember this message"}'

# Terminal 1: Stop server (Ctrl+C), then restart
uvicorn src.api.app:app --reload

# Terminal 2: Verify session restored
curl -X GET http://localhost:8000/api/session/$SESSION_ID \
  -H "X-API-Key: dev-api-key"

# Should return conversation history with "Hello, remember this message"
```

#### Test 2: Debug Events

```bash
# Enable debug mode
curl -X POST http://localhost:8000/api/session/$SESSION_ID/debug/enable \
  -H "X-API-Key: dev-api-key"

# Send message to generate events
curl -X POST http://localhost:8000/api/session/$SESSION_ID/chat \
  -H "X-API-Key: dev-api-key" \
  -H "Content-Type: application/json" \
  -d '{"message": "Search for Memgraph documentation"}'

# Retrieve debug events
curl -X GET http://localhost:8000/api/session/$SESSION_ID/debug/events \
  -H "X-API-Key: dev-api-key"
```

---

## Verification

### Database Verification (Memgraph Lab)

1. Open Memgraph Lab: http://localhost:3000
2. Connect to database (should auto-connect)
3. Run query to see sessions:

```cypher
MATCH (s:SESSION)
RETURN s
LIMIT 10
```

4. Run query to see debug events with relationships:

```cypher
MATCH (e:DEBUG_EVENT)-[:BELONGS_TO]->(s:SESSION)
RETURN e, s
LIMIT 20
```

5. Verify indexes exist:

```cypher
SHOW INDEX INFO
```

---

## Troubleshooting

### Issue: Database connection fails

**Solution**:
```bash
# Check if Memgraph is running
docker ps | grep memgraph

# Check logs
docker logs ai-agent-memgraph

# Restart database
docker-compose restart memgraph
```

### Issue: Sessions not persisting

**Debug**:
```python
# Add logging to save_session_state
import logging
logger = logging.getLogger(__name__)

def save_session_state(...):
    logger.info(f"Saving session {session_id}")
    try:
        # ... save logic
        logger.info(f"Successfully saved session {session_id}")
    except Exception as e:
        logger.error(f"Failed to save session {session_id}: {e}")
```

### Issue: Tests failing

**Common causes**:
1. Database not running: `docker-compose up -d memgraph`
2. Stale data in database: Clear database with `MATCH (n) DETACH DELETE n`
3. Import errors: Ensure all files are created and imports are correct

---

## Next Steps

After completing this implementation:

1. ✅ All tests passing (unit + integration)
2. ✅ Manual testing verified
3. ✅ Database indexes created
4. ⏭️ Update frontend to use new session verification API
5. ⏭️ Add session cleanup job for inactive sessions (>30 days)
6. ⏭️ Add monitoring/metrics for database operations

---

## Additional Resources

- [Memgraph Documentation](https://memgraph.com/docs)
- [Cypher Query Language](https://memgraph.com/docs/cypher-manual)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [pytest Documentation](https://docs.pytest.org/)

---

**Questions?** Check the data-model.md and contracts/api.md for detailed specifications.
