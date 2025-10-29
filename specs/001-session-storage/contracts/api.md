# API Contracts: Session Management

**Version**: 1.0  
**Base URL**: `/api`  
**Authentication**: API Key (Header: `X-API-Key`)

---

## Endpoints

### 1. GET /api/session/{session_id}

**Description**: Retrieve or create a session. If `session_id` is "new", creates a new session. Otherwise, retrieves existing session state.

**Authentication**: Required

**Path Parameters**:
- `session_id` (string, required): Session identifier or "new" for creating new session

**Query Parameters**: None

**Headers**:
```
X-API-Key: <api_key>
Authorization: Bearer <jwt_token>  (optional, for user identification)
```

**Request Example**:
```http
GET /api/session/abc123-def456-ghi789 HTTP/1.1
Host: localhost:8000
X-API-Key: my-secret-api-key
```

**Response 200 OK** (Existing Session):
```json
{
    "session_id": "abc123-def456-ghi789",
    "message": "Session restored",
    "conversation_history": [
        {
            "role": "user",
            "content": "Hello"
        },
        {
            "role": "assistant",
            "content": "Hi! How can I help you today?"
        }
    ],
    "title": "My Conversation"
}
```

**Response 200 OK** (New Session):
```json
{
    "session_id": "new-uuid-generated-here",
    "message": "Session is active",
    "conversation_history": [],
    "title": "New Session"
}
```

**Response 404 Not Found**:
```json
{
    "detail": "Session not found"
}
```

**Response 401 Unauthorized**:
```json
{
    "detail": "Invalid API key"
}
```

---

### 2. GET /api/sessions

**Description**: List all active sessions for the authenticated user

**Authentication**: Required

**Query Parameters**:
- `user_id` (string, optional): Filter sessions by user ID (automatically extracted from JWT if not provided)
- `limit` (integer, optional, default=50): Maximum number of sessions to return
- `offset` (integer, optional, default=0): Number of sessions to skip (pagination)

**Headers**:
```
X-API-Key: <api_key>
Authorization: Bearer <jwt_token>
```

**Request Example**:
```http
GET /api/sessions?limit=10&offset=0 HTTP/1.1
Host: localhost:8000
X-API-Key: my-secret-api-key
Authorization: Bearer eyJhbGc...
```

**Response 200 OK**:
```json
{
    "sessions": [
        {
            "session_id": "abc123",
            "title": "My Conversation",
            "last_activity": "2025-10-29T10:30:00Z",
            "conversation_count": 15,
            "user_id": "user_123"
        },
        {
            "session_id": "def456",
            "title": "Another Chat",
            "last_activity": "2025-10-29T09:15:00Z",
            "conversation_count": 8,
            "user_id": "user_123"
        }
    ],
    "total": 2,
    "limit": 10,
    "offset": 0
}
```

**Response 401 Unauthorized**: (same as above)

---

### 3. DELETE /api/session/{session_id}

**Description**: Delete a session and all associated debug events

**Authentication**: Required

**Path Parameters**:
- `session_id` (string, required): Session identifier to delete

**Headers**:
```
X-API-Key: <api_key>
Authorization: Bearer <jwt_token>
```

**Request Example**:
```http
DELETE /api/session/abc123-def456-ghi789 HTTP/1.1
Host: localhost:8000
X-API-Key: my-secret-api-key
```

**Response 200 OK**:
```json
{
    "message": "Session deleted successfully",
    "session_id": "abc123-def456-ghi789"
}
```

**Response 404 Not Found**:
```json
{
    "detail": "Session not found"
}
```

**Response 401 Unauthorized**: (same as above)

---

### 4. POST /api/session/{session_id}/chat

**Description**: Send a message to the agent and receive a response. Updates session state in database.

**Authentication**: Required

**Path Parameters**:
- `session_id` (string, required): Session identifier

**Headers**:
```
X-API-Key: <api_key>
Content-Type: application/json
```

**Request Body**:
```json
{
    "message": "What is the weather in San Francisco?",
    "stream": false
}
```

**Request Schema**:
```typescript
{
    message: string;          // User message content (required)
    stream: boolean;          // Enable streaming response (optional, default: false)
}
```

**Response 200 OK** (Non-streaming):
```json
{
    "response": "The current weather in San Francisco is 68°F and sunny.",
    "session_id": "abc123-def456-ghi789",
    "conversation_count": 5
}
```

**Response 200 OK** (Streaming):
```
Content-Type: text/event-stream

data: {"type": "content", "delta": "The"}
data: {"type": "content", "delta": " current"}
data: {"type": "content", "delta": " weather"}
...
data: {"type": "done", "session_id": "abc123", "conversation_count": 5}
```

**Response 404 Not Found**: (session not found)

---

### 5. GET /api/session/{session_id}/debug/events

**Description**: Retrieve debug events for a specific session

**Authentication**: Required

**Path Parameters**:
- `session_id` (string, required): Session identifier

**Query Parameters**:
- `event_type` (string, optional): Filter by event type (e.g., "tool_call", "agent_to_model")
- `limit` (integer, optional, default=100): Maximum number of events to return
- `offset` (integer, optional, default=0): Number of events to skip

**Headers**:
```
X-API-Key: <api_key>
```

**Request Example**:
```http
GET /api/session/abc123/debug/events?event_type=tool_call&limit=50 HTTP/1.1
Host: localhost:8000
X-API-Key: my-secret-api-key
```

**Response 200 OK**:
```json
{
    "events": [
        {
            "event_id": "event_001",
            "event_type": "tool_call",
            "message": "Tool Call: google_search",
            "data": {
                "tool_name": "google_search",
                "arguments": {
                    "query": "Memgraph database"
                }
            },
            "timestamp": "2025-10-29T10:30:15Z"
        },
        {
            "event_id": "event_002",
            "event_type": "tool_result",
            "message": "Tool Result: google_search",
            "data": {
                "tool_name": "google_search",
                "result": {
                    "results": [...]
                }
            },
            "timestamp": "2025-10-29T10:30:18Z"
        }
    ],
    "total": 2,
    "session_id": "abc123",
    "limit": 50,
    "offset": 0
}
```

---

### 6. POST /api/session/{session_id}/debug/enable

**Description**: Enable debug capture for a session

**Authentication**: Required

**Path Parameters**:
- `session_id` (string, required): Session identifier

**Request Body**: None

**Response 200 OK**:
```json
{
    "message": "Debug capture enabled",
    "session_id": "abc123",
    "enabled": true
}
```

---

### 7. POST /api/session/{session_id}/debug/disable

**Description**: Disable debug capture for a session

**Authentication**: Required

**Path Parameters**:
- `session_id` (string, required): Session identifier

**Request Body**: None

**Response 200 OK**:
```json
{
    "message": "Debug capture disabled",
    "session_id": "abc123",
    "enabled": false
}
```

---

### 8. DELETE /api/session/{session_id}/debug/events

**Description**: Clear all debug events for a session (does not disable capture)

**Authentication**: Required

**Path Parameters**:
- `session_id` (string, required): Session identifier

**Response 200 OK**:
```json
{
    "message": "Debug events cleared",
    "session_id": "abc123",
    "events_deleted": 127
}
```

---

## Data Models

### Session Response Model

```typescript
interface SessionResponse {
    session_id: string;
    message: string;
    conversation_history: Message[];
    title: string;
}

interface Message {
    role: "user" | "assistant" | "system" | "tool";
    content: string;
    tool_calls?: ToolCall[];
    tool_call_id?: string;
    name?: string;
}

interface ToolCall {
    id: string;
    type: "function";
    function: {
        name: string;
        arguments: string;  // JSON string
    };
}
```

### Session List Item

```typescript
interface SessionListItem {
    session_id: string;
    title: string;
    last_activity: string;  // ISO 8601 datetime
    conversation_count: number;
    user_id: string;
}
```

### Debug Event Model

```typescript
interface DebugEvent {
    event_id: string;
    event_type: 
        | "agent_to_model"
        | "model_to_agent"
        | "tool_call"
        | "tool_result"
        | "tool_error"
        | "mcp_call"
        | "mcp_result"
        | "system_info"
        | "error";
    message: string;
    data: Record<string, any>;
    timestamp: string;  // ISO 8601 datetime
}
```

---

## Error Responses

### Standard Error Format

All error responses follow this format:

```json
{
    "detail": "Error message describing what went wrong"
}
```

### Common Status Codes

| Code | Meaning | When Used |
|------|---------|-----------|
| 200 | OK | Successful operation |
| 400 | Bad Request | Invalid request body or parameters |
| 401 | Unauthorized | Missing or invalid API key |
| 403 | Forbidden | User doesn't have access to this session |
| 404 | Not Found | Session doesn't exist |
| 500 | Internal Server Error | Server-side error (database failure, etc.) |

---

## Authentication

### API Key Authentication

All endpoints require an API key in the request header:

```
X-API-Key: your-secret-api-key
```

API keys are validated using the `get_api_key()` dependency in FastAPI.

### User Authentication (Optional)

For multi-user scenarios, include a JWT token:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

The `user_id` is extracted from the JWT payload using the `get_user_id()` dependency.

---

## Rate Limiting

**Current**: No rate limiting implemented

**Future**: Consider implementing rate limiting per API key:
- 100 requests per minute for standard users
- 1000 requests per minute for premium users

---

## Versioning

**Current Version**: v1 (no version prefix in URL)

**Future**: When breaking changes are needed, introduce versioning:
- `/api/v1/session/{session_id}`
- `/api/v2/session/{session_id}`

---

## WebSocket Support (Future)

For real-time session updates and streaming chat:

```
ws://localhost:8000/api/session/{session_id}/ws
```

**Not implemented in Phase 1** - will be added in future iteration.

---

## Frontend Integration

### Session Verification on Load

```typescript
// On app load, verify each localStorage session exists in backend
async function verifySessions() {
    const localSessions = JSON.parse(localStorage.getItem('sessions') || '[]');
    
    for (const session of localSessions) {
        if (session.sessionId) {  // Has backend reference
            try {
                const response = await fetch(`/api/session/${session.sessionId}`, {
                    headers: { 'X-API-Key': apiKey }
                });
                
                if (response.status === 404) {
                    // Backend session no longer exists
                    session.sessionId = null;  // Clear reference
                }
            } catch (error) {
                console.error('Failed to verify session', error);
            }
        }
    }
    
    localStorage.setItem('sessions', JSON.stringify(localSessions));
}
```

### Lazy Backend Session Creation

```typescript
// On first message send, create backend session if needed
async function sendMessage(frontendSessionId: string, message: string) {
    let session = getSessionById(frontendSessionId);
    
    if (!session.sessionId) {
        // No backend session yet - create one
        const response = await fetch('/api/session/new', {
            headers: { 'X-API-Key': apiKey }
        });
        const data = await response.json();
        
        session.sessionId = data.session_id;
        saveSessions();  // Persist to localStorage
    }
    
    // Send message to backend session
    const response = await fetch(`/api/session/${session.sessionId}/chat`, {
        method: 'POST',
        headers: {
            'X-API-Key': apiKey,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ message })
    });
    
    return response.json();
}
```

---

## Next Steps

1. ✅ Complete API contracts (this document)
2. ⏭️ Create quickstart.md with setup instructions
3. ⏭️ Update agent context files
4. ⏭️ Proceed to Phase 2: Task breakdown
