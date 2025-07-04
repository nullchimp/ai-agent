import json
from datetime import datetime
from typing import List, Optional, Dict, Any

from core.models import AgentSession, ConversationMessage, SessionStatus, MemoryEntry, MemoryType
from core.rag.dbhandler.memgraph import MemGraphClient
from core.storage.interfaces import SessionRepository, MemoryRepository, StorageManager


class MemgraphSessionRepository(SessionRepository):
    def __init__(self, client: MemGraphClient):
        self.client = client
    
    async def create_session(self, session: AgentSession) -> AgentSession:
        query = """
        CREATE (s:AgentSession {
            session_id: $session_id,
            user_id: $user_id,
            title: $title,
            status: $status,
            created_at: $created_at,
            last_activity: $last_activity,
            metadata: $metadata,
            conversation_history: $conversation_history
        })
        RETURN s
        """
        
        params = {
            "session_id": session.session_id,
            "user_id": session.user_id,
            "title": session.title,
            "status": session.status.value,
            "created_at": session.created_at.isoformat(),
            "last_activity": session.last_activity.isoformat(),
            "metadata": json.dumps(session.metadata),
            "conversation_history": json.dumps([msg.model_dump() for msg in session.conversation_history])
        }
        
        self.client._execute(query, params)
        return session
    
    async def get_session(self, session_id: str) -> Optional[AgentSession]:
        query = "MATCH (s:AgentSession {session_id: $session_id}) RETURN s"
        self.client._execute(query, {"session_id": session_id})
        result = self.client._cur.fetchone()
        
        if not result:
            return None
            
        return self._node_to_session(result[0])
    
    async def update_session(self, session: AgentSession) -> AgentSession:
        query = """
        MATCH (s:AgentSession {session_id: $session_id})
        SET s.title = $title,
            s.status = $status,
            s.last_activity = $last_activity,
            s.metadata = $metadata,
            s.conversation_history = $conversation_history
        RETURN s
        """
        
        params = {
            "session_id": session.session_id,
            "title": session.title,
            "status": session.status.value,
            "last_activity": session.last_activity.isoformat(),
            "metadata": json.dumps(session.metadata),
            "conversation_history": json.dumps([msg.model_dump() for msg in session.conversation_history])
        }
        
        self.client._execute(query, params)
        return session
    
    async def delete_session(self, session_id: str) -> bool:
        query = "MATCH (s:AgentSession {session_id: $session_id}) DELETE s"
        self.client._execute(query, {"session_id": session_id})
        return True
    
    async def list_sessions(self, user_id: Optional[str] = None, limit: int = 100) -> List[AgentSession]:
        if user_id:
            query = """
            MATCH (s:AgentSession {user_id: $user_id})
            RETURN s
            ORDER BY s.last_activity DESC
            LIMIT $limit
            """
            params = {"user_id": user_id, "limit": limit}
        else:
            query = """
            MATCH (s:AgentSession)
            RETURN s
            ORDER BY s.last_activity DESC
            LIMIT $limit
            """
            params = {"limit": limit}
        
        self.client._execute(query, params)
        results = self.client._cur.fetchall()
        
        return [self._node_to_session(row[0]) for row in results]
    
    async def get_active_sessions(self) -> List[AgentSession]:
        query = """
        MATCH (s:AgentSession {status: 'active'})
        RETURN s
        ORDER BY s.last_activity DESC
        """
        
        self.client._execute(query)
        results = self.client._cur.fetchall()
        
        return [self._node_to_session(row[0]) for row in results]
    
    def _node_to_session(self, node) -> AgentSession:
        props = node.properties
        
        conversation_history = []
        if props.get("conversation_history"):
            history_data = json.loads(props["conversation_history"])
            conversation_history = [ConversationMessage(**msg) for msg in history_data]
        
        return AgentSession(
            session_id=props["session_id"],
            user_id=props.get("user_id"),
            title=props["title"],
            status=SessionStatus(props["status"]),
            created_at=datetime.fromisoformat(props["created_at"]),
            last_activity=datetime.fromisoformat(props["last_activity"]),
            metadata=json.loads(props.get("metadata", "{}")),
            conversation_history=conversation_history
        )


class MemgraphMemoryRepository(MemoryRepository):
    def __init__(self, client: MemGraphClient):
        self.client = client
    
    async def store_memory(self, memory: MemoryEntry) -> MemoryEntry:
        query = """
        CREATE (m:MemoryEntry {
            id: $id,
            session_id: $session_id,
            memory_type: $memory_type,
            content: $content,
            importance: $importance,
            created_at: $created_at,
            last_accessed: $last_accessed,
            access_count: $access_count,
            tags: $tags,
            metadata: $metadata,
            related_messages: $related_messages
        })
        RETURN m
        """
        
        params = {
            "id": memory.id,
            "session_id": memory.session_id,
            "memory_type": memory.memory_type.value,
            "content": memory.content,
            "importance": memory.importance.value,
            "created_at": memory.created_at.isoformat(),
            "last_accessed": memory.last_accessed.isoformat(),
            "access_count": memory.access_count,
            "tags": json.dumps(memory.tags),
            "metadata": json.dumps(memory.metadata),
            "related_messages": json.dumps(memory.related_messages)
        }
        
        self.client._execute(query, params)
        return memory
    
    async def get_memory(self, memory_id: str) -> Optional[MemoryEntry]:
        query = "MATCH (m:MemoryEntry {id: $memory_id}) RETURN m"
        self.client._execute(query, {"memory_id": memory_id})
        result = self.client._cur.fetchone()
        
        if not result:
            return None
            
        return self._node_to_memory(result[0])
    
    async def update_memory(self, memory: MemoryEntry) -> MemoryEntry:
        query = """
        MATCH (m:MemoryEntry {id: $id})
        SET m.content = $content,
            m.importance = $importance,
            m.last_accessed = $last_accessed,
            m.access_count = $access_count,
            m.tags = $tags,
            m.metadata = $metadata,
            m.related_messages = $related_messages
        RETURN m
        """
        
        params = {
            "id": memory.id,
            "content": memory.content,
            "importance": memory.importance.value,
            "last_accessed": memory.last_accessed.isoformat(),
            "access_count": memory.access_count,
            "tags": json.dumps(memory.tags),
            "metadata": json.dumps(memory.metadata),
            "related_messages": json.dumps(memory.related_messages)
        }
        
        self.client._execute(query, params)
        return memory
    
    async def delete_memory(self, memory_id: str) -> bool:
        query = "MATCH (m:MemoryEntry {id: $memory_id}) DELETE m"
        self.client._execute(query, {"memory_id": memory_id})
        return True
    
    async def get_session_memories(
        self, 
        session_id: str, 
        memory_type: Optional[MemoryType] = None,
        limit: int = 100
    ) -> List[MemoryEntry]:
        if memory_type:
            query = """
            MATCH (m:MemoryEntry {session_id: $session_id, memory_type: $memory_type})
            RETURN m
            ORDER BY m.last_accessed DESC
            LIMIT $limit
            """
            params = {"session_id": session_id, "memory_type": memory_type.value, "limit": limit}
        else:
            query = """
            MATCH (m:MemoryEntry {session_id: $session_id})
            RETURN m
            ORDER BY m.last_accessed DESC
            LIMIT $limit
            """
            params = {"session_id": session_id, "limit": limit}
        
        self.client._execute(query, params)
        results = self.client._cur.fetchall()
        
        return [self._node_to_memory(row[0]) for row in results]
    
    async def search_memories(
        self,
        query: str,
        session_id: Optional[str] = None,
        memory_type: Optional[MemoryType] = None,
        limit: int = 10
    ) -> List[MemoryEntry]:
        where_conditions = ["m.content CONTAINS $query"]
        params = {"query": query, "limit": limit}
        
        if session_id:
            where_conditions.append("m.session_id = $session_id")
            params["session_id"] = session_id
            
        if memory_type:
            where_conditions.append("m.memory_type = $memory_type")
            params["memory_type"] = memory_type.value
        
        where_clause = " AND ".join(where_conditions)
        
        cypher_query = f"""
        MATCH (m:MemoryEntry)
        WHERE {where_clause}
        RETURN m
        ORDER BY m.importance DESC, m.last_accessed DESC
        LIMIT $limit
        """
        
        self.client._execute(cypher_query, params)
        results = self.client._cur.fetchall()
        
        return [self._node_to_memory(row[0]) for row in results]
    
    def _node_to_memory(self, node) -> MemoryEntry:
        props = node.properties
        
        return MemoryEntry(
            id=props["id"],
            session_id=props["session_id"],
            memory_type=MemoryType(props["memory_type"]),
            content=props["content"],
            importance=props["importance"],
            created_at=datetime.fromisoformat(props["created_at"]),
            last_accessed=datetime.fromisoformat(props["last_accessed"]),
            access_count=props["access_count"],
            tags=json.loads(props.get("tags", "[]")),
            metadata=json.loads(props.get("metadata", "{}")),
            related_messages=json.loads(props.get("related_messages", "[]"))
        )


class MemgraphStorageManager(StorageManager):
    def __init__(self, host: str = "127.0.0.1", port: int = 7687, username: str = None, password: str = None):
        self.client = MemGraphClient(host=host, port=port, username=username, password=password)
        self.session_repo = MemgraphSessionRepository(self.client)
        self.memory_repo = MemgraphMemoryRepository(self.client)
    
    async def initialize(self) -> None:
        self.client.connect()
        await self._create_indexes()
    
    async def close(self) -> None:
        self.client.close()
    
    async def health_check(self) -> bool:
        try:
            self.client._execute("RETURN 1")
            return True
        except Exception:
            return False
    
    async def _create_indexes(self) -> None:
        indexes = [
            "CREATE INDEX ON :AgentSession(session_id);",
            "CREATE INDEX ON :AgentSession(user_id);",
            "CREATE INDEX ON :AgentSession(status);",
            "CREATE INDEX ON :MemoryEntry(id);",
            "CREATE INDEX ON :MemoryEntry(session_id);",
            "CREATE INDEX ON :MemoryEntry(memory_type);",
            "CREATE INDEX ON :MemoryEntry(importance);",
        ]
        
        for index_query in indexes:
            try:
                self.client._execute(index_query)
            except Exception:
                pass  # Index might already exist