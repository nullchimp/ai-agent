# Data Model: Database-Backed Session Storage

**Date**: 2025-10-29  
**Feature**: 001-session-storage  
**Status**: Phase 1 - Design

## Overview

This document defines the data model for persistent session storage in Memgraph. The model extends the existing `Session` node schema and introduces new `DebugEvent` nodes with relationships to support debug capture persistence.

---

## Entity Definitions

### 1. SESSION Node

**Purpose**: Represents an agent conversation session with complete state

**Schema Definition**:
```python
class Session(Node):
    # Identity
    id: str                          # UUID (inherited from Node base class)
    session_id: str                  # UUID - primary identifier for session
    user_id: Optional[str]           # User identifier for multi-user scenarios
    
    # Metadata
    title: str                       # Display title (default: "New Session")
    is_active: bool                  # Soft delete flag (default: True)
    created_at: datetime             # Creation timestamp (inherited from Node)
    updated_at: datetime             # Last update timestamp (inherited from Node)
    last_activity: datetime          # Last user interaction timestamp
    conversation_count: int          # Number of conversation turns
    
    # Session State
    conversation_history: str        # JSON serialized List[Dict[str, Any]]
    enabled_tools: List[str]         # Array of enabled tool names
    disabled_tools: List[str]        # Array of disabled tool names
    mcp_initialized: bool            # MCP initialization status
    agent_config: str                # JSON serialized Dict[str, Any]
```

**Cypher Representation**:
```cypher
CREATE (s:SESSION {
    id: $id,
    session_id: $session_id,
    user_id: $user_id,
    title: $title,
    is_active: true,
    created_at: datetime(),
    updated_at: datetime(),
    last_activity: datetime(),
    conversation_count: 0,
    conversation_history: $conversation_history_json,
    enabled_tools: $enabled_tools,
    disabled_tools: $disabled_tools,
    mcp_initialized: false,
    agent_config: $agent_config_json
})
```

**Indexes**:
```cypher
CREATE INDEX ON :SESSION(session_id);
CREATE INDEX ON :SESSION(user_id);
CREATE INDEX ON :SESSION(is_active);
CREATE INDEX ON :SESSION(last_activity);
```

**Field Descriptions**:

- **id**: Internal UUID from Node base class, used for graph operations
- **session_id**: External session identifier, used in API and frontend
- **user_id**: Associates session with user for multi-user isolation (NULL for anonymous sessions)
- **title**: Human-readable session title, can be updated by user
- **is_active**: Soft delete flag - inactive sessions not returned in queries but preserved for history
- **created_at**: Immutable creation timestamp
- **updated_at**: Updated on every modification
- **last_activity**: Updated on user interactions (messages, tool changes), used for cleanup jobs
- **conversation_count**: Incremented per message turn, used for analytics
- **conversation_history**: JSON array of message objects `[{role, content, ...}, ...]`
- **enabled_tools**: Array of tool names currently enabled for this session
- **disabled_tools**: Array of tool names explicitly disabled
- **mcp_initialized**: Boolean flag indicating if MCP servers are initialized for this session
- **agent_config**: JSON object with agent-specific configuration

**Validation Rules**:
- `session_id` must be unique across all sessions (enforced by index)
- `conversation_history` must be valid JSON or empty string
- `agent_config` must be valid JSON or empty string
- `conversation_count` must be non-negative
- `last_activity` must be <= `updated_at`

**State Transitions**:
```
NEW → ACTIVE (conversation_count = 0 → 1)
ACTIVE → ACTIVE (conversation_count incremented)
ACTIVE → INACTIVE (is_active = true → false)
INACTIVE → [no transitions] (soft deleted)
```

---

### 2. DEBUG_EVENT Node

**Purpose**: Represents a single debug capture event associated with a session

**Schema Definition**:
```python
class DebugEvent(Node):
    # Identity
    id: str                          # UUID (inherited from Node base class)
    event_id: str                    # UUID - unique event identifier
    session_id: str                  # Reference to parent session
    
    # Event Data
    event_type: str                  # Enum: AGENT_TO_MODEL, MODEL_TO_AGENT, TOOL_CALL, etc.
    message: str                     # Human-readable event description
    data: str                        # JSON serialized Dict[str, Any] - event payload
    timestamp: datetime              # Event occurrence timestamp
    
    # Metadata
    created_at: datetime             # Creation timestamp (inherited from Node)
```

**Cypher Representation**:
```cypher
CREATE (e:DEBUG_EVENT {
    id: $id,
    event_id: $event_id,
    session_id: $session_id,
    event_type: $event_type,
    message: $message,
    data: $data_json,
    timestamp: $timestamp,
    created_at: datetime()
})
```

**Indexes**:
```cypher
CREATE INDEX ON :DEBUG_EVENT(event_id);
CREATE INDEX ON :DEBUG_EVENT(session_id);
CREATE INDEX ON :DEBUG_EVENT(event_type);
CREATE INDEX ON :DEBUG_EVENT(timestamp);
```

**Field Descriptions**:

- **id**: Internal UUID from Node base class
- **event_id**: External event identifier for tracking
- **session_id**: Foreign key reference to SESSION node
- **event_type**: Event classification (see DebugEventType enum below)
- **message**: Short description of the event (e.g., "Tool Call: google_search")
- **data**: JSON payload with event-specific data (LLM request/response, tool args/results, etc.)
- **timestamp**: When the event occurred (not when it was persisted)
- **created_at**: When the event was persisted to database

**Event Types**:
```python
class DebugEventType(str, Enum):
    AGENT_TO_MODEL = "agent_to_model"      # LLM request from agent
    MODEL_TO_AGENT = "model_to_agent"      # LLM response to agent
    TOOL_CALL = "tool_call"                # Local tool invocation
    TOOL_RESULT = "tool_result"            # Local tool result
    TOOL_ERROR = "tool_error"              # Local tool error
    MCP_CALL = "mcp_call"                  # MCP tool invocation
    MCP_RESULT = "mcp_result"              # MCP tool result
    SYSTEM_INFO = "system_info"            # System-level information
    ERROR = "error"                        # General error event
```

**Validation Rules**:
- `event_type` must be one of the DebugEventType enum values
- `data` must be valid JSON or empty string
- `timestamp` must be <= `created_at`
- `session_id` must reference an existing SESSION node

---

### 3. DEBUG_CAPTURE (In-Memory State)

**Purpose**: In-memory session-specific debug capture controller (not persisted as node)

**Schema Definition**:
```python
class DebugCapture:
    # Identity
    session_id: str                  # Associated session ID
    
    # Configuration
    _enabled: bool                   # Debug capture on/off
    _max_events: int                 # Event buffer limit (default: 1000)
    
    # State
    _events: List[DebugEvent]        # In-memory event buffer
    _lock: threading.Lock            # Thread safety for event list
```

**Lifecycle**:
- Created on-demand when `get_debug_capture_instance(session_id)` is called
- Stored in `_debug_sessions` dict (keyed by session_id)
- Persists events to database when captured (if enabled)
- Deleted from memory when session is deleted

**Relationship to Database**:
- Events are persisted to DEBUG_EVENT nodes as they're captured
- In-memory `_events` list acts as a cache for recent events
- On restart, events are loaded from database into cache

---

## Relationships

### BELONGS_TO

**Purpose**: Links debug events to their parent session

**Schema**:
```cypher
(e:DEBUG_EVENT)-[:BELONGS_TO]->(s:SESSION)
```

**Properties**: None (simple directional relationship)

**Cardinality**: Many-to-One (many events belong to one session)

**Cascade Behavior**:
```cypher
// When session is deleted, all debug events are also deleted
MATCH (s:SESSION {session_id: $session_id})<-[:BELONGS_TO]-(e:DEBUG_EVENT)
DETACH DELETE s, e
```

**Query Patterns**:
```cypher
// Get all events for a session (ordered by timestamp)
MATCH (s:SESSION {session_id: $session_id})<-[:BELONGS_TO]-(e:DEBUG_EVENT)
RETURN e
ORDER BY e.timestamp ASC

// Count events per session
MATCH (s:SESSION)<-[:BELONGS_TO]-(e:DEBUG_EVENT)
RETURN s.session_id, count(e) as event_count

// Get events by type for a session
MATCH (s:SESSION {session_id: $session_id})<-[:BELONGS_TO]-(e:DEBUG_EVENT {event_type: $type})
RETURN e
ORDER BY e.timestamp DESC
```

---

## Data Flow Diagrams

### Session Creation Flow

```
User Request → FastAPI Endpoint
    ↓
GET /api/session/new
    ↓
Check if session_id in _agent_sessions cache?
    ├─ YES → Return cached agent instance
    └─ NO  → Create new Agent instance
                ↓
            create_db_session(session_id, user_id)
                ↓
            INSERT SESSION node to Memgraph
                ↓
            Store Agent in _agent_sessions cache
                ↓
            Return session details to frontend
```

### Session Update Flow

```
Agent.chat(message) called
    ↓
Process message, call tools, get LLM response
    ↓
Update agent.history with new messages
    ↓
save_session_state(session_id, conversation_history, ...)
    ↓
MATCH SESSION node by session_id
    ↓
UPDATE conversation_history, last_activity, conversation_count
    ↓
COMMIT to Memgraph
    ↓
Cache remains in _agent_sessions (already updated)
```

### Debug Event Capture Flow

```
debug_capture.capture_event(event_type, message, data)
    ↓
Is debug capture enabled?
    ├─ NO  → Discard event
    └─ YES → Create DebugEvent object
                ↓
            Add to in-memory _events list (with max limit)
                ↓
            Persist to database (async)
                ↓
            CREATE DEBUG_EVENT node in Memgraph
                ↓
            CREATE (event)-[:BELONGS_TO]->(session) relationship
                ↓
            Event available for retrieval via API
```

### Session Restore Flow

```
Server restart
    ↓
_agent_sessions and _debug_sessions are empty (in-memory cleared)
    ↓
User makes request to existing session_id
    ↓
get_agent_instance(session_id)
    ↓
session_id not in _agent_sessions cache → Cache miss
    ↓
restore_session_state(session_id)
    ↓
MATCH SESSION node by session_id in Memgraph
    ↓
Load conversation_history, enabled_tools, mcp_initialized, etc.
    ↓
Create Agent instance with restore_from_db=True
    ↓
Agent._restore_from_db() applies loaded state
    ↓
Store Agent in _agent_sessions cache
    ↓
Session continues seamlessly
```

---

## JSON Serialization Formats

### Conversation History Format

```json
[
    {
        "role": "user",
        "content": "What is the weather today?"
    },
    {
        "role": "assistant",
        "content": "I'll check the weather for you.",
        "tool_calls": [
            {
                "id": "call_123",
                "type": "function",
                "function": {
                    "name": "google_search",
                    "arguments": "{\"query\": \"weather today\"}"
                }
            }
        ]
    },
    {
        "role": "tool",
        "tool_call_id": "call_123",
        "name": "google_search",
        "content": "Weather results..."
    },
    {
        "role": "assistant",
        "content": "Today's weather is sunny with 72°F."
    }
]
```

**Storage**:
```python
session.conversation_history = json.dumps(conversation_list)
```

**Retrieval**:
```python
conversation_list = json.loads(session.conversation_history)
```

---

### Agent Config Format

```json
{
    "model": "gpt-4-turbo-preview",
    "temperature": 0.7,
    "max_tokens": 4096,
    "system_prompt_version": "v2.1",
    "custom_settings": {
        "enable_rag": true,
        "enable_mcp": true
    }
}
```

**Storage**:
```python
session.agent_config = json.dumps(config_dict)
```

**Retrieval**:
```python
config_dict = json.loads(session.agent_config or "{}")
```

---

### Debug Event Data Format

**Example: AGENT_TO_MODEL event**
```json
{
    "payload": {
        "model": "gpt-4-turbo-preview",
        "messages": [
            {"role": "user", "content": "Hello"}
        ],
        "tools": [
            {"type": "function", "function": {"name": "google_search", ...}}
        ],
        "temperature": 0.7
    }
}
```

**Example: TOOL_CALL event**
```json
{
    "tool_name": "google_search",
    "arguments": {
        "query": "Memgraph database best practices"
    }
}
```

**Example: TOOL_RESULT event**
```json
{
    "tool_name": "google_search",
    "result": {
        "results": [
            {"title": "...", "url": "...", "snippet": "..."}
        ]
    }
}
```

---

## Database Constraints & Indexes

### Unique Constraints

```cypher
-- Ensure session_id is unique
CREATE CONSTRAINT ON (s:SESSION) ASSERT s.session_id IS UNIQUE;

-- Ensure event_id is unique
CREATE CONSTRAINT ON (e:DEBUG_EVENT) ASSERT e.event_id IS UNIQUE;
```

### Performance Indexes

```cypher
-- Session lookups by ID (most common query)
CREATE INDEX ON :SESSION(session_id);

-- Session filtering by user (multi-user isolation)
CREATE INDEX ON :SESSION(user_id);

-- Session filtering by active status (list all sessions)
CREATE INDEX ON :SESSION(is_active);

-- Session cleanup by last activity (find stale sessions)
CREATE INDEX ON :SESSION(last_activity);

-- Debug event lookups by session (common join)
CREATE INDEX ON :DEBUG_EVENT(session_id);

-- Debug event filtering by type (debugging specific events)
CREATE INDEX ON :DEBUG_EVENT(event_type);

-- Debug event ordering by time (chronological retrieval)
CREATE INDEX ON :DEBUG_EVENT(timestamp);
```

---

## Data Size Estimates

### Per Session

| Field | Size | Notes |
|-------|------|-------|
| session_id | 36 bytes | UUID string |
| user_id | 50 bytes | Typical user ID |
| title | 100 bytes | Short string |
| conversation_history | 10-50 KB | 50-100 messages |
| enabled_tools | 200 bytes | ~10 tool names |
| disabled_tools | 200 bytes | ~10 tool names |
| agent_config | 500 bytes | JSON config |
| Metadata | 200 bytes | Timestamps, counts, booleans |
| **Total** | **~12-52 KB** | Per active session |

### Per Debug Event

| Field | Size | Notes |
|-------|------|-------|
| event_id | 36 bytes | UUID string |
| session_id | 36 bytes | UUID reference |
| event_type | 20 bytes | Enum string |
| message | 100 bytes | Short description |
| data | 1-10 KB | Varies by event type |
| Timestamps | 50 bytes | datetime fields |
| **Total** | **~1.2-10.3 KB** | Per event |

### Scale Projections

| Metric | Volume | Storage |
|--------|--------|---------|
| 1,000 active sessions | 1,000 sessions | ~12-52 MB |
| 10,000 active sessions | 10,000 sessions | ~120-520 MB |
| 1,000 events/session | 1M events | ~1.2-10.3 GB |

**Note**: Memgraph stores data efficiently in memory with snapshots to disk. Monitor memory usage and implement cleanup policies for old sessions.

---

## Migration from Current State

### Current State

**In-Memory Only**:
```python
# agent.py
_agent_sessions = {}  # {session_id: Agent}

# debug_capture.py
_debug_sessions = {}  # {session_id: DebugCapture}
```

**Partial Database Support**:
- Session schema exists in `src/core/db/schemas/session_objects.py`
- CRUD operations exist in `src/core/db/session.py`
- But `_agent_sessions` dict is not synced with database

### Migration Steps

1. **Add Debug Event Schema** (NEW)
   - Create `src/core/db/schemas/debug_objects.py` with DebugEvent class
   - Update `src/core/db/schemas/__init__.py` to import debug objects

2. **Add Debug Persistence** (NEW)
   - Create `src/core/db/debug.py` with CRUD operations for debug events
   - Implement `save_debug_event()`, `get_debug_events_by_session()`, `delete_debug_events()`

3. **Modify Agent Session Management** (MODIFY)
   - Update `get_agent_instance()` to check DB on cache miss
   - Update `Agent.__init__()` to support `restore_from_db=True`
   - Call `save_session_state()` after each conversation turn

4. **Modify Debug Capture** (MODIFY)
   - Update `DebugCapture.capture_event()` to persist to database
   - Add `load_events_from_db()` to restore event history on session access

5. **Add Frontend Synchronization** (NEW)
   - Update frontend to verify backend session existence on load
   - Update frontend to save backend session IDs to localStorage

6. **Add Database Indexes** (NEW)
   - Run index creation queries in Memgraph initialization script

---

## Next Steps

1. ✅ Complete data-model.md (this document)
2. ⏭️ Create contracts/ with API endpoint specifications
3. ⏭️ Create quickstart.md with setup and development guide
4. ⏭️ Update agent context files
5. ⏭️ Proceed to Phase 2: Task breakdown (tasks.md)
