# Research: Database-Backed Session Storage

**Date**: 2025-10-29  
**Feature**: 001-session-storage  
**Status**: Phase 0 Complete

## Research Questions & Findings

### 1. Session Persistence Strategy

**Question**: How should we handle the transition from in-memory dictionary storage to database-backed storage while maintaining performance?

**Decision**: Hybrid cache-first approach with database as source of truth

**Rationale**:
- **Performance**: In-memory cache provides <1ms access times for active sessions
- **Reliability**: Database ensures persistence across restarts
- **Simplicity**: Leverage existing `_agent_sessions` and `_debug_sessions` dictionaries as cache
- **Atomic operations**: Database provides ACID guarantees for session state

**Alternatives Considered**:
1. **Database-only (no cache)**: Would add 10-50ms latency per session access
2. **Cache-only with periodic sync**: Risk of data loss between sync intervals
3. **Write-through cache**: Chosen approach - write to DB immediately, read from cache

**Implementation Pattern**:
```python
# On session access/create
def get_agent_instance(session_id: str):
    if session_id in _agent_sessions:
        return _agent_sessions[session_id]  # Cache hit
    
    # Cache miss - restore from DB
    session_state = restore_session_state(session_id)
    if session_state:
        agent = Agent(session_id, restore_from_db=True)
        _agent_sessions[session_id] = agent
        return agent
    
    # New session
    agent = Agent(session_id)
    _agent_sessions[session_id] = agent
    create_db_session(session_id)  # Persist immediately
    return agent
```

---

### 2. Debug Event Storage Schema

**Question**: How should debug events be stored in Memgraph to support efficient querying by session?

**Decision**: Use graph relationships to link DebugEvent nodes to Session nodes

**Rationale**:
- **Graph database strength**: Memgraph excels at relationship traversal
- **Query efficiency**: `MATCH (s:SESSION {session_id: $id})<-[:BELONGS_TO]-(e:DEBUG_EVENT)` is O(1) with proper indexing
- **Data locality**: Events naturally belong to sessions
- **Cascade deletion**: When session deleted, events can be easily removed via relationship

**Schema Design**:
```cypher
// Nodes
(s:SESSION {session_id, title, user_id, conversation_history, ...})
(e:DEBUG_EVENT {event_id, event_type, message, data, timestamp})

// Relationship
(e)-[:BELONGS_TO]->(s)

// Index for performance
CREATE INDEX ON :SESSION(session_id);
CREATE INDEX ON :DEBUG_EVENT(event_type);
```

**Alternatives Considered**:
1. **Store as JSON array in Session**: Would require deserializing entire array for queries, limited to 1000 events
2. **Separate table/collection**: Breaks graph model consistency, requires joins
3. **Graph nodes with relationships** (chosen): Natural fit for Memgraph, efficient queries

---

### 3. Memgraph Data Type Handling

**Question**: How should we handle complex Python types (lists, dicts) in Memgraph properties?

**Decision**: Serialize complex types to JSON strings for storage, deserialize on retrieval

**Rationale**:
- **Memgraph limitations**: Native support for primitives (str, int, float, bool) but limited for nested structures
- **Conversation history**: List of message dicts needs to be preserved exactly as-is
- **Tool configurations**: Lists of strings (enabled_tools, disabled_tools) can be stored natively as arrays
- **Agent config**: Dict needs JSON serialization

**Best Practices**:
```python
# Storage
conversation_json = json.dumps(conversation_history)
session.conversation_history = conversation_json

# Retrieval
conversation_history = json.loads(session.conversation_history)

# Arrays of strings - native support
enabled_tools = ["google_search", "read_file"]  # Stored as Memgraph array
```

**Implementation Notes**:
- Add serialization/deserialization helper methods to `Session` class
- Use `json.dumps()` with `default=str` for datetime handling
- Validate JSON integrity on retrieval with try/except

**Alternatives Considered**:
1. **Pickle serialization**: Not human-readable in DB, version compatibility issues
2. **Separate document store**: Adds complexity, breaks single source of truth
3. **JSON serialization** (chosen): Human-readable, standard, portable

---

### 4. Frontend-Backend Session Synchronization

**Question**: How should frontend localStorage sessions synchronize with backend database sessions?

**Decision**: Verify-on-load with lazy backend creation pattern

**Rationale**:
- **User experience**: Don't block frontend load on backend verification
- **Resilience**: Frontend can function even if backend is temporarily unavailable
- **Data integrity**: Backend session IDs are canonical, frontend holds references
- **Lazy creation**: Backend session only created when user sends first message

**Synchronization Flow**:
```
1. Frontend loads sessions from localStorage
   - Each session has: {id, title, messages, sessionId (backend ref)}

2. On app initialization:
   - For each session with sessionId:
     - Call GET /api/session/{sessionId} to verify existence
     - If 404: clear sessionId from frontend session (but keep frontend session)
     - If 200: session is valid

3. On user sends message:
   - If no sessionId: call GET /api/session/new to create backend session
   - Save returned sessionId to localStorage
   - Send message with sessionId

4. On server restart:
   - Backend restores sessions from database
   - Frontend verification finds all sessions intact
```

**Alternatives Considered**:
1. **Sync on every message**: Too much overhead, 2x API calls per message
2. **Periodic background sync**: Complex, battery drain on mobile
3. **Verify-on-load** (chosen): Simple, efficient, resilient

---

### 5. Database Connection Failure Handling

**Question**: How should the system behave when database connection fails during session operations?

**Decision**: Graceful degradation with in-memory fallback and retry logic

**Rationale**:
- **Availability**: System remains functional even if DB is temporarily unavailable
- **User experience**: No error messages for transient failures
- **Data integrity**: Changes persisted to DB as soon as connection restored
- **Observability**: Log all DB failures for monitoring

**Implementation Strategy**:
```python
def save_session_state(session_id, ...):
    try:
        # Attempt database save
        session = get_session_by_id(session_id)
        if session:
            update_session(session)
        else:
            create_session(session_id, ...)
    except ConnectionError as e:
        logger.warning(f"DB unavailable, session {session_id} in memory only: {e}")
        # Session continues in _agent_sessions cache
        # Next save attempt will retry
    except Exception as e:
        logger.error(f"Failed to save session {session_id}: {e}")
        # Don't crash - continue with in-memory state
```

**Recovery Strategy**:
- Implement retry logic with exponential backoff
- On agent instance access, attempt to sync in-memory state to DB
- Health check endpoint to verify DB connectivity

**Alternatives Considered**:
1. **Fail fast**: Reject user requests if DB down - poor UX
2. **Queue writes**: Complex, requires persistent queue storage
3. **Graceful degradation** (chosen): Simple, maintains availability

---

### 6. Session Lifecycle Management

**Question**: When should sessions be created, updated, and deleted in the database?

**Decision**: Eager creation, lazy updates, explicit deletion

**Rationale**:
- **Creation**: On first agent access (GET /api/session/new or first message)
- **Updates**: After each conversation turn, on tool state changes, on MCP initialization
- **Deletion**: Explicit user action or cleanup job for inactive sessions

**Lifecycle Events**:
```python
# Creation
session = create_session(session_id=str(uuid.uuid4()), user_id=user_id)

# Updates (automatic)
- After agent.chat() call: save conversation_history
- On tool enable/disable: save enabled_tools, disabled_tools
- On MCP initialization: save mcp_initialized flag
- On any update: update last_activity timestamp

# Deletion (explicit)
- User clicks "Delete Session" → DELETE /api/session/{session_id}
- Cascade: Delete associated debug events
- Cleanup job: Delete sessions inactive >30 days
```

**Best Practices**:
- Always update `last_activity` timestamp on any session modification
- Increment `conversation_count` on each message
- Use database transactions for multi-step updates

**Alternatives Considered**:
1. **Create on user action**: Risk of orphaned in-memory sessions
2. **Update on every access**: Too much DB load
3. **Eager creation, lazy updates** (chosen): Balances consistency and performance

---

### 7. Multi-User Session Isolation

**Question**: How should we ensure sessions are properly isolated between different users?

**Decision**: User ID filtering at database query level with API-level authentication

**Rationale**:
- **Security**: Prevent unauthorized access to other users' sessions
- **Privacy**: User data completely isolated
- **Scalability**: Database indexes on user_id enable efficient queries
- **Enforcement**: Filter applied at lowest level (database queries)

**Implementation**:
```python
# Database level
def get_all_sessions(user_id: str) -> List[Session]:
    q = "MATCH (n:`SESSION` {is_active: true, user_id: $user_id}) RETURN n"
    # Always include user_id in WHERE clause

# API level
@router.get("/api/sessions")
async def list_sessions(user_id: str = Depends(get_user_id)):
    return get_all_sessions(user_id)  # user_id from JWT token
```

**Security Measures**:
- Never trust user_id from request body - always from JWT/API key
- Add user_id to all session queries (CREATE, MATCH, DELETE)
- Add index on user_id for performance: `CREATE INDEX ON :SESSION(user_id)`

**Alternatives Considered**:
1. **Application-level filtering only**: Risk of bugs exposing data
2. **Separate databases per user**: Massive overhead, poor scalability
3. **Database-level filtering** (chosen): Defense in depth, efficient

---

## Technology Best Practices

### Memgraph in Docker

**Current Setup** (from docker-compose.yml):
```yaml
memgraph:
  image: memgraph/memgraph-mage:latest
  ports: ["7687:7687", "7444:7444"]
  volumes: [memgraph_data:/var/lib/memgraph]
  command: [
    "--storage-snapshot-interval-sec=300",
    "--storage-wal-enabled=true",
    "--storage-snapshot-on-exit=true"
  ]
```

**Best Practices Applied**:
1. **Persistence**: WAL (Write-Ahead Log) enabled for crash recovery
2. **Snapshots**: Automatic snapshots every 5 minutes
3. **Exit safety**: Snapshot on graceful shutdown
4. **Data volume**: Persistent storage mounted at `/var/lib/memgraph`

**Recommendations**:
- Monitor snapshot size growth over time
- Implement backup strategy (export/import snapshots)
- Consider snapshot-on-exit for production deployments

---

### Python Connection Pooling

**Current Setup** (from src/core/db/__init__.py):
```python
ConnectionPool(
    min_connections=2,
    max_connections=10,
    connection_timeout=30.0,
    idle_timeout=300.0
)
```

**Best Practices Applied**:
1. **Pool reuse**: Connections reused across requests
2. **Validation**: Connections validated before use (`RETURN 1` query)
3. **Context managers**: Automatic connection return to pool
4. **Thread-safe**: Uses threading.RLock for concurrent access

**Recommendations**:
- Monitor pool exhaustion (max_connections reached)
- Tune min/max based on concurrent session load
- Add metrics for pool utilization

---

### Async/Await Patterns

**Current Pattern**:
```python
# API routes are async
async def get_session(session_id: str):
    await get_agent_instance(session_id)  # Should be async
```

**Issue**: Database operations in `src/core/db/session.py` are synchronous

**Recommendation**:
```python
# Make DB operations async-safe by running in thread pool
import asyncio
from functools import partial

async def save_session_state_async(...):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, partial(save_session_state, ...))
```

**Rationale**:
- FastAPI endpoints are async
- Memgraph driver (mgclient) is synchronous
- Use thread pool executor to avoid blocking event loop

---

## Integration Patterns

### Pattern 1: Cache-Aside (Lazy Loading)

```python
def get_session_from_cache_or_db(session_id: str) -> Optional[Dict]:
    # 1. Check cache
    if session_id in _session_cache:
        return _session_cache[session_id]
    
    # 2. Cache miss - load from DB
    session_state = restore_session_state(session_id)
    if session_state:
        _session_cache[session_id] = session_state
        return session_state
    
    # 3. Not found
    return None
```

**When to use**: Session retrieval (GET operations)

---

### Pattern 2: Write-Through Cache

```python
def save_session_to_cache_and_db(session_id: str, state: Dict):
    # 1. Update cache
    _session_cache[session_id] = state
    
    # 2. Write to database
    try:
        save_session_state(session_id, **state)
    except Exception as e:
        logger.error(f"DB write failed: {e}")
        # Keep cache updated even if DB fails
```

**When to use**: Session updates (PUT/PATCH operations)

---

### Pattern 3: Cache Invalidation

```python
def delete_session_from_cache_and_db(session_id: str):
    # 1. Remove from cache
    if session_id in _agent_sessions:
        del _agent_sessions[session_id]
    if session_id in _debug_sessions:
        del _debug_sessions[session_id]
    
    # 2. Delete from database
    delete_session(session_id)
    # This will cascade to debug events via DETACH DELETE
```

**When to use**: Session deletion (DELETE operations)

---

## Summary of Decisions

| Area | Decision | Rationale |
|------|----------|-----------|
| **Persistence Strategy** | Hybrid cache-first with DB source of truth | Performance + reliability |
| **Debug Storage** | Graph nodes with relationships | Natural fit for Memgraph |
| **Data Serialization** | JSON for complex types, arrays for lists | Compatibility + readability |
| **Frontend Sync** | Verify-on-load with lazy creation | Simple + resilient |
| **Failure Handling** | Graceful degradation to in-memory | High availability |
| **Lifecycle** | Eager creation, lazy updates | Balance consistency/performance |
| **Multi-User** | User ID filtering at DB level | Security + scalability |
| **Async Pattern** | Thread pool executor for sync DB calls | Event loop safety |

---

## Next Steps (Phase 1)

1. ✅ Complete research.md (this document)
2. ⏭️ Create data-model.md with detailed schema definitions
3. ⏭️ Create contracts/ with API endpoint specifications
4. ⏭️ Create quickstart.md with setup and usage instructions
5. ⏭️ Update agent context (run update-agent-context.sh script)
6. ⏭️ Re-evaluate constitution check after design phase
