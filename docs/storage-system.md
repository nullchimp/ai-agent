# Storage System Documentation

## Overview

The AI Agent storage system provides comprehensive persistence for sessions, conversations, and intelligent memory management using a three-tier memory architecture built on top of the existing Memgraph infrastructure.

## Architecture

### Core Components

1. **Session Management**: Persistent agent sessions with conversation history
2. **Memory System**: Three-tier memory architecture (Working, Episodic, Semantic)
3. **Storage Layer**: Memgraph-based repositories with abstraction interfaces
4. **API Integration**: Enhanced endpoints with memory-aware responses

### Memory Architecture

#### Working Memory
- **Purpose**: Immediate conversation context (circular buffer)
- **Capacity**: 20 items max, automatically manages overflow
- **Sorting**: By importance and recency
- **Use Case**: Provides context for current conversation turn

#### Episodic Memory  
- **Purpose**: Conversation history with semantic indexing
- **Storage**: Complete user-agent interactions with metadata
- **Search**: Content-based search across conversation history
- **Use Case**: Reference past conversations and learned context

#### Semantic Memory
- **Purpose**: Extracted knowledge and facts
- **Extraction**: Automatic knowledge detection from conversations
- **Indicators**: "is defined as", "means", "fact:", "important:", etc.
- **Use Case**: Persistent knowledge base for the agent

## Configuration

### Environment Variables

```bash
# Memgraph Connection (optional - defaults shown)
MEMGRAPH_HOST=127.0.0.1
MEMGRAPH_PORT=7687
MEMGRAPH_USERNAME=   # Optional
MEMGRAPH_PASSWORD=   # Optional
```

### Initialization

The storage system initializes automatically when first accessed:

```python
from core.storage.session_manager import get_session_manager

# Get the global session manager instance
session_manager = get_session_manager()

# Health check
is_healthy = await session_manager.health_check()
```

## Usage Examples

### Session Management

```python
from core.storage.session_manager import get_session_manager

session_manager = get_session_manager()

# Create a new session
session = await session_manager.create_session(
    user_id="user-123",
    title="Python Learning Session"
)

# Add messages to the session
await session_manager.add_message(
    session_id=session.session_id,
    role="user", 
    content="What is Python?"
)

await session_manager.add_message(
    session_id=session.session_id,
    role="assistant",
    content="Python is a programming language known for its simplicity.",
    used_tools=["web_search"]
)

# Get memory context for generating responses
context = await session_manager.get_context_for_response(
    session_id=session.session_id,
    query="Tell me more about Python frameworks"
)
```

### Direct Memory Access

```python
from core.storage import MemgraphStorageManager
from core.memory import MemoryCoordinator

# Initialize storage
storage = MemgraphStorageManager()
await storage.initialize()

# Create memory coordinator
memory = MemoryCoordinator(storage.memory_repo)

# Process an interaction
await memory.process_interaction(
    session_id="session-123",
    user_input="What is machine learning?",
    agent_response="Machine learning is defined as a method of data analysis.",
    tools_used=["wikipedia_search"]
)

# Get context for response generation
context = await memory.get_context_for_response(
    session_id="session-123",
    query="How does ML relate to AI?"
)
```

### API Integration

The storage system integrates seamlessly with the API:

```bash
# Create a new session
curl -X GET "http://localhost:8000/api/session/new"

# Send a message (automatically stored)
curl -X POST "http://localhost:8000/api/{session_id}/ask" \
  -H "Content-Type: application/json" \
  -d '{"query": "Hello, how are you?"}'

# Get session information  
curl -X GET "http://localhost:8000/api/session/{session_id}/info"

# Get memory context
curl -X GET "http://localhost:8000/api/{session_id}/memory/context?query=python"

# List all sessions
curl -X GET "http://localhost:8000/api/sessions"
```

## Database Schema

### Nodes Created in Memgraph

1. **AgentSession**
   - Properties: session_id, user_id, title, status, created_at, last_activity, metadata, conversation_history

2. **MemoryEntry** 
   - Properties: id, session_id, memory_type, content, importance, created_at, last_accessed, access_count, tags, metadata, related_messages

### Indexes

The system automatically creates the following indexes for performance:

```cypher
CREATE INDEX ON :AgentSession(session_id);
CREATE INDEX ON :AgentSession(user_id);
CREATE INDEX ON :AgentSession(status);
CREATE INDEX ON :MemoryEntry(id);
CREATE INDEX ON :MemoryEntry(session_id);
CREATE INDEX ON :MemoryEntry(memory_type);
CREATE INDEX ON :MemoryEntry(importance);
```

## Performance Considerations

### Memory Management
- Working memory limited to 20 items to prevent context overflow
- Automatic cleanup of old working memories (24 hours by default)
- Importance-based retention for critical information

### Database Queries
- All queries use indexed fields for optimal performance
- Memory searches use content-based filtering
- Session queries sorted by last activity

### Caching
- Session manager implements singleton pattern
- In-memory session instances cached during active use
- Memory coordinator maintains working memory buffer

## Monitoring and Maintenance

### Health Checks
```python
# Check storage system health
session_manager = get_session_manager()
is_healthy = await session_manager.health_check()
```

### Session Cleanup
```python
# Archive old inactive sessions
archived_count = await session_manager.cleanup_old_sessions(days_inactive=30)
```

### Memory Cleanup
```python
# Clear old working memories
await memory.working_memory.clear_old_memories(
    session_id="session-123",
    older_than_hours=24
)
```

## Error Handling

The storage system includes comprehensive error handling:

- Connection failures gracefully handled with retries
- Invalid session IDs return appropriate 404 responses  
- Database errors logged and converted to HTTP exceptions
- Automatic connection management and cleanup

## Migration from Legacy Sessions

The system gracefully handles the transition:

1. Legacy in-memory sessions continue working
2. New sessions automatically use persistent storage
3. Existing session IDs can be migrated on first access
4. No data loss during the transition

## Testing

Run the comprehensive test suite:

```bash
# Test all storage components
pytest tests/test_storage_memgraph.py tests/test_memory_system.py tests/test_session_manager.py -v --asyncio-mode=auto

# Test coverage
pytest --cov=src/core/storage --cov=src/core/memory --cov=src/core/models
```

## Troubleshooting

### Common Issues

1. **Connection Errors**: Check Memgraph is running and accessible
2. **Index Errors**: May occur on first run, indexes are created automatically
3. **Memory Overflow**: Working memory self-manages, but check importance scoring
4. **Session Not Found**: Verify session was created with persistent storage

### Logging

Enable debug logging to monitor storage operations:

```python
import logging
logging.getLogger('core.storage').setLevel(logging.DEBUG)
```