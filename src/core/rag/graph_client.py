import os
from typing import Dict, List, Any, Optional, Union
import asyncio
from datetime import datetime
import json
from neo4j import AsyncGraphDatabase
from dotenv import load_dotenv
import uuid

# Load environment variables from .env file
load_dotenv(override=True)

class MemGraphClient:
    def __init__(self, 
                 uri: Optional[str] = None, 
                 username: Optional[str] = None, 
                 password: Optional[str] = None, 
                 max_connection_pool_size: int = 50):
        """Initialize MemGraph client with connection parameters"""
        self.uri = uri or os.environ.get("MEMGRAPH_URI") or "bolt://localhost:7687"
        self.username = username or os.environ.get("MEMGRAPH_USERNAME") or "neo4j"
        self.password = password or os.environ.get("MEMGRAPH_PASSWORD") or "aiagentpassword"
        
        self.driver = AsyncGraphDatabase.driver(
            self.uri,
            auth=(self.username, self.password),
            max_connection_pool_size=max_connection_pool_size
        )
    
    async def close(self):
        """Close all connections in the driver connection pool"""
        await self.driver.close()
    
    async def run_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict]:
        """Execute a Cypher query and return results"""
        async with self.driver.session() as session:
            result = await session.run(query, params or {})
            # Using values() to get all records
            records = await result.values()
            # If we have column names, convert to dictionaries
            if result.keys():
                return [dict(zip(result.keys(), record)) for record in records]
            return []
    
    # Document management methods
    
    async def create_document(self, path: str, content: str, embedding: List[float],
                           title: Optional[str] = None, author: Optional[str] = None,
                           mime_type: Optional[str] = None) -> Dict:
        """Create a document node with content and embedding"""
        # Generate a random UUID
        doc_id = str(uuid.uuid4())
        query = """
        CREATE (d:Document {
            id: $id,
            path: $path,
            content: $content,
            embedding: $embedding,
            content_hash: $content_hash,
            embedding_version: "text-embedding-3-small",
            updated_at: $updated_at,
            title: $title,
            author: $author,
            mime_type: $mime_type
        })
        RETURN d
        """
        import hashlib
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        
        params = {
            "id": doc_id,
            "path": path,
            "content": content,
            "embedding": embedding,
            "content_hash": content_hash,
            "updated_at": datetime.now().isoformat(),
            "title": title or os.path.basename(path),
            "author": author,
            "mime_type": mime_type
        }
        result = await self.run_query(query, params)
        
        # Link document to a Resource
        if result and result[0]["d"]:
            document = result[0]["d"]
            standardized_path = standardize_resource_uri(path)
            await self.link_document_to_resource(document["id"], standardized_path)
            
        return result[0]["d"] if result else {}
    
    async def find_document(self, path: str) -> Optional[Dict]:
        """Find document by path"""
        query = """
        MATCH (d:Document {path: $path})
        RETURN d
        """
        result = await self.run_query(query, {"path": path})
        return result[0]["d"] if result else None
    
    async def upsert_document(self, path: str, content: str, embedding: List[float], 
                           content_hash: str, embedding_version: str, updated_at: str,
                           title: Optional[str] = None, author: Optional[str] = None,
                           mime_type: Optional[str] = None) -> Dict:
        """Update or insert document"""
        query = """
        MERGE (d:Document {path: $path})
        SET d.content = $content,
            d.embedding = $embedding,
            d.content_hash = $content_hash,
            d.embedding_version = $embedding_version,
            d.updated_at = $updated_at,
            d.title = $title,
            d.author = $author,
            d.mime_type = $mime_type
        RETURN d
        """
        params = {
            "path": path,
            "content": content,
            "embedding": embedding,
            "content_hash": content_hash,
            "embedding_version": embedding_version,
            "updated_at": updated_at,
            "title": title or os.path.basename(path),
            "author": author,
            "mime_type": mime_type
        }
        result = await self.run_query(query, params)
        
        # Link document to a Resource
        if result and result[0]["d"]:
            document = result[0]["d"]
            standardized_path = standardize_resource_uri(path)
            await self.link_document_to_resource(document["id"], standardized_path)
            
        return result[0]["d"] if result else {}
    
    # Symbol and relationship methods
    
    async def create_symbol(self, name: str, document_path: str) -> Dict:
        """Create a symbol and connect it to a document"""
        query = """
        MATCH (d:Document {path: $document_path})
        MERGE (s:Symbol {name: $name})
        CREATE (d)-[:REFERS_TO]->(s)
        RETURN s
        """
        result = await self.run_query(query, {"name": name, "document_path": document_path})
        return result[0]["s"] if result else {}
    
    # Resource management methods
    
    async def create_resource(self, uri: str, type: str = "unknown", description: Optional[str] = None) -> Dict:
        """Create a Resource node with URI, type and optional description"""
        resource_id = str(uuid.uuid4())
        query = """
        MERGE (r:Resource {uri: $uri})
        ON CREATE SET r.id = $id, r.type = $type, r.description = $description
        RETURN r
        """
        result = await self.run_query(query, {
            "uri": uri, 
            "id": resource_id,
            "type": type,
            "description": description
        })
        return result[0]["r"] if result else {}
    
    async def create_url_link(self, url: str, document_path: str) -> Dict:
        """Create a Resource node for URL and link it to a document"""
        resource = await self.create_resource(url, "web", "External web resource")
        
        doc = await self.find_document(document_path)
        if not doc or "id" not in doc:
            return {}
            
        query = """
        MATCH (d:Document {id: $doc_id}), (r:Resource {uri: $uri})
        CREATE (d)-[:LINKS_TO]->(r)
        RETURN r
        """
        result = await self.run_query(query, {"doc_id": doc["id"], "uri": url})
        return result[0]["r"] if result else resource
    
    async def link_document_to_resource(self, document_id: str, resource_uri: str, 
                                    resource_type: str = "file") -> Dict:
        """Create a REFERENCES relationship from document to resource"""
        resource = await self.create_resource(resource_uri, resource_type)
        
        query = """
        MATCH (d:Document {id: $doc_id}), (r:Resource {uri: $uri})
        MERGE (d)-[:REFERENCES]->(r)
        RETURN r
        """
        result = await self.run_query(query, {"doc_id": document_id, "uri": resource_uri})
        return result[0]["r"] if result else {}
    
    async def create_tool(self, name: str, document_path: str) -> Dict:
        """Create a Tool node and link it to a document"""
        query = """
        MATCH (d:Document {path: $document_path})
        MERGE (t:Tool {name: $name})
        CREATE (t)-[:DEFINED_IN]->(d)
        RETURN t
        """
        result = await self.run_query(query, {"name": name, "document_path": document_path})
        return result[0]["t"] if result else {}
    
    # Conversation and message management
    
    async def create_conversation(self, title: Optional[str] = None) -> str:
        """Create a new conversation node and return its ID"""
        convo_id = str(uuid.uuid4())
        query = """
        CREATE (c:Conversation {
            id: $id,
            start_time: $start_time,
            title: $title
        })
        RETURN c.id as id
        """
        result = await self.run_query(query, {
            "id": convo_id,
            "start_time": datetime.now().isoformat(),
            "title": title or "New Conversation"
        })
        return result[0]["id"] if result else convo_id
    
    async def update_conversation(self, conversation_id: str, properties: Dict[str, Any]) -> Dict:
        """Update conversation properties"""
        property_sets = ", ".join([f"c.{k} = ${k}" for k in properties])
        query = f"""
        MATCH (c:Conversation {{id: $id}})
        SET {property_sets}
        RETURN c
        """
        params = {"id": conversation_id, **properties}
        result = await self.run_query(query, params)
        return result[0]["c"] if result else {}
    
    async def add_message(self, conversation_id: str, content: str, role: str,
                       timestamp: datetime, references: Optional[List[str]] = None) -> str:
        """Add a message to a conversation and return the message ID"""
        message_id = str(uuid.uuid4())
        query = """
        MATCH (c:Conversation {id: $conversation_id})
        CREATE (m:Message {
            id: $id,
            content: $content,
            role: $role,
            timestamp: $timestamp
        })
        CREATE (m)-[:PART_OF]->(c)
        RETURN m.id as id
        """
        params = {
            "id": message_id,
            "conversation_id": conversation_id,
            "content": content,
            "role": role,
            "timestamp": timestamp.isoformat()
        }
        result = await self.run_query(query, params)
        message_id = result[0]["id"] if result else message_id
        
        # Add references to documents if provided
        if references and message_id:
            for ref_id in references:
                await self.create_message_document_reference(message_id, ref_id)
                
        return message_id
    
    async def get_conversation_messages(self, conversation_id: str) -> List[Dict]:
        """Get all messages in a conversation ordered by timestamp"""
        query = """
        MATCH (m:Message)-[:PART_OF]->(c:Conversation {id: $conversation_id})
        RETURN m.id as id, m.content as content, m.role as role, m.timestamp as timestamp
        ORDER BY m.timestamp
        """
        return await self.run_query(query, {"conversation_id": conversation_id})
    
    async def create_message_document_reference(self, message_id: str, document_id: str) -> Dict:
        """Create a reference from a message to a document"""
        query = """
        MATCH (m:Message {id: $message_id})
        MATCH (d:Document {id: $document_id})
        CREATE (m)-[:REFERENCES]->(d)
        RETURN m, d
        """
        try:
            result = await self.run_query(query, {"message_id": message_id, "document_id": document_id})
            return result[0] if result else {}
        except Exception as e:
            # If document_id is actually a path
            if "id" not in document_id and "/" in document_id:
                query_by_path = """
                MATCH (m:Message {id: $message_id})
                MATCH (d:Document {path: $document_path})
                CREATE (m)-[:REFERENCES]->(d)
                RETURN m, d
                """
                result = await self.run_query(query_by_path, {"message_id": message_id, "document_path": document_id})
                return result[0] if result else {}
            raise e
    
    async def get_conversation_summary(self, conversation_id: str) -> Dict:
        """Get summary of a conversation"""
        query = """
        MATCH (c:Conversation {id: $conversation_id})
        RETURN c.summary as summary, c.title as title, c.start_time as start_time
        """
        result = await self.run_query(query, {"conversation_id": conversation_id})
        return result[0] if result else {}
    
    # Concept and entity management
    
    async def create_or_get_concept(self, name: str) -> str:
        """Create or get a concept node and return its ID"""
        concept_id = str(uuid.uuid4())
        query = """
        MERGE (c:Concept {name: $name})
        ON CREATE SET c.id = $id
        RETURN c.id as id
        """
        result = await self.run_query(query, {"name": name, "id": concept_id})
        return result[0]["id"] if result else concept_id
    
    async def create_or_get_entity(self, name: str, entity_type: str) -> str:
        """Create or get an entity node and return its ID"""
        entity_id = str(uuid.uuid4())
        query = """
        MERGE (e:Entity {name: $name, type: $entity_type})
        ON CREATE SET e.id = $id
        RETURN e.id as id
        """
        result = await self.run_query(query, {"name": name, "entity_type": entity_type, "id": entity_id})
        return result[0]["id"] if result else entity_id
    
    async def create_relationship(self, from_id: str, to_id: str, relationship_type: str) -> Dict:
        """Create a relationship between two nodes"""
        query = f"""
        MATCH (a), (b)
        WHERE a.id = $from_id AND b.id = $to_id
        CREATE (a)-[r:{relationship_type}]->(b)
        RETURN r
        """
        result = await self.run_query(query, {"from_id": from_id, "to_id": to_id})
        return result[0]["r"] if result else {}
    
    async def link_message_to_concept(self, message_id: str, concept_name: str) -> Dict:
        """Link a message to a concept"""
        concept_id = await self.create_or_get_concept(concept_name)
        return await self.create_relationship(message_id, concept_id, "MENTIONS")
    
    # Privacy and retention management
    
    async def get_expired_conversations(self, days: int = 90) -> List[Dict]:
        """Get conversations that have expired based on retention period"""
        query = """
        MATCH (c:Conversation)
        WHERE timestamp() > timestamp(c.start_time) + duration({days: $days})
        RETURN c
        """
        return await self.run_query(query, {"days": days})
    
    async def delete_conversation(self, conversation_id: str) -> None:
        """Delete a conversation and all its messages"""
        query = """
        MATCH (c:Conversation {id: $conversation_id})
        DETACH DELETE c
        """
        await self.run_query(query, {"conversation_id": conversation_id})
        
        # Delete orphaned messages
        query_messages = """
        MATCH (m:Message)
        WHERE NOT (m)-[:PART_OF]->()
        DETACH DELETE m
        """
        await self.run_query(query_messages)
    
    async def update_message(self, message_id: str, properties: Dict[str, Any]) -> Dict:
        """Update message properties"""
        property_sets = ", ".join([f"m.{k} = ${k}" for k in properties])
        query = f"""
        MATCH (m:Message {{id: $id}})
        SET {property_sets}
        RETURN m
        """
        params = {"id": message_id, **properties}
        result = await self.run_query(query, params)
        return result[0]["m"] if result else {}
    
    # Semantic search and vector operations
    
    async def semantic_search(self, query_embedding: List[float], limit: int = 5) -> List[Dict]:
        """Search documents by vector similarity using MemGraph's vector search"""
        query = """
        MATCH (d:Document)
        WHERE d.embedding IS NOT NULL
        WITH d, mg.vectors.cosine(d.embedding, $query_embedding) AS score
        MATCH (d)-[:REFERENCES]->(r:Resource)
        ORDER BY score DESC
        LIMIT $limit
        RETURN d.path AS path, d.content AS content, score, d.title as title, 
               d.author as author, d.updated_at as updated_at, r.uri as resource_uri,
               r.type as resource_type
        """
        return await self.run_query(query, {"query_embedding": query_embedding, "limit": limit})
    
    async def semantic_search_fallback(self, query_embedding: List[float], limit: int = 5) -> List[Dict]:
        """Fallback search method when vector functions are not available
        This method fetches all documents and computes similarity on the client side"""
        query = """
        MATCH (d:Document)
        WHERE d.embedding IS NOT NULL
        MATCH (d)-[:REFERENCES]->(r:Resource)
        RETURN d.path AS path, d.content AS content, d.embedding AS embedding,
               d.title as title, d.author as author, d.updated_at as updated_at,
               r.uri as resource_uri, r.type as resource_type
        """
        all_docs = await self.run_query(query)
        
        # Calculate similarity scores on the client side
        scored_docs = []
        for doc in all_docs:
            if "embedding" not in doc or not doc["embedding"]:
                continue
                
            # Calculate cosine similarity
            score = self._cosine_similarity(doc["embedding"], query_embedding)
            scored_docs.append({
                "path": doc["path"],
                "content": doc["content"],
                "score": score,
                "title": doc.get("title", os.path.basename(doc["path"])),
                "author": doc.get("author", "Unknown"),
                "updated_at": doc.get("updated_at", ""),
                "resource_uri": doc.get("resource_uri", ""),
                "resource_type": doc.get("resource_type", "")
            })
        
        # Sort by score and return top results
        scored_docs.sort(key=lambda x: x["score"], reverse=True)
        return scored_docs[:limit]
    
    async def conversation_aware_search(self, 
                                     query_embedding: List[float], 
                                     conversation_id: Optional[str] = None, 
                                     limit: int = 5) -> List[Dict]:
        """Search documents and past conversations based on query relevance"""
        try:
            # First try to find relevant documents
            docs = await self.semantic_search(query_embedding, limit)
            
            # If a conversation ID is provided, also find related conversations
            if conversation_id:
                conv_query = """
                MATCH (c:Conversation)
                WHERE c.id <> $current_conversation_id AND c.summary_embedding IS NOT NULL
                WITH c, mg.vectors.cosine(c.summary_embedding, $query_embedding) AS score
                WHERE score > 0.7
                ORDER BY score DESC
                LIMIT 3
                
                // Get messages from those conversations
                MATCH (m:Message)-[:PART_OF]->(c)
                RETURN m.content as content, c.summary as conversation_summary, 
                       score as relevance, c.id as conversation_id
                ORDER BY c.start_time, m.timestamp
                LIMIT 10
                """
                conv_results = await self.run_query(conv_query, {
                    "current_conversation_id": conversation_id,
                    "query_embedding": query_embedding
                })
                
                # Combine document results with conversation results
                if conv_results:
                    # Format conversation results to match document format
                    for i, conv in enumerate(conv_results):
                        docs.append({
                            "path": f"conversation/{conv['conversation_id']}",
                            "content": conv["content"],
                            "score": conv["relevance"],
                            "title": f"Past Conversation: {conv.get('conversation_summary', 'Unnamed')}",
                            "resource_uri": f"conversation://{conv['conversation_id']}",
                            "resource_type": "conversation"
                        })
                    
                    # Re-sort by score
                    docs.sort(key=lambda x: x.get("score", 0), reverse=True)
                    docs = docs[:limit]
            
            return docs
        except Exception:
            # Fallback to standard semantic search
            return await self.semantic_search_fallback(query_embedding, limit)
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        if len(vec1) != len(vec2):
            return 0.0
            
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        mag1 = sum(a * a for a in vec1) ** 0.5
        mag2 = sum(b * b for b in vec2) ** 0.5
        
        if mag1 * mag2 == 0:
            return 0.0
            
        return dot_product / (mag1 * mag2)
    
    async def create_vector_index(self) -> None:
        """Create vector indices for documents and message embeddings in MemGraph
        Note: MemGraph handles vector search without requiring explicit index creation"""
        pass

    # Topic management
    
    async def create_or_get_topic(self, name: str) -> str:
        """Create or get a topic node and return its ID"""
        topic_id = str(uuid.uuid4())
        query = """
        MERGE (t:Topic {name: $name})
        ON CREATE SET t.id = $id
        RETURN t.id as id
        """
        result = await self.run_query(query, {"name": name, "id": topic_id})
        return result[0]["id"] if result else topic_id
    
    async def link_document_to_topic(self, document_path: str, topic_name: str) -> Dict:
        """Link a document to a topic"""
        topic_id = await self.create_or_get_topic(topic_name)
        doc = await self.find_document(document_path)
        if not doc or "id" not in doc:
            return {}
            
        return await self.create_relationship(doc["id"], topic_id, "BELONGS_TO")
    
    # Concept relationship management
    
    async def link_document_explains_concept(self, document_path: str, concept_name: str) -> Dict:
        """Create an EXPLAINS relationship from document to concept"""
        concept_id = await self.create_or_get_concept(concept_name)
        doc = await self.find_document(document_path)
        if not doc or "id" not in doc:
            return {}
            
        return await self.create_relationship(doc["id"], concept_id, "EXPLAINS")
    
    async def link_related_concepts(self, concept_name1: str, concept_name2: str) -> Dict:
        """Create a RELATED_TO relationship between two concepts"""
        concept_id1 = await self.create_or_get_concept(concept_name1)
        concept_id2 = await self.create_or_get_concept(concept_name2)
        return await self.create_relationship(concept_id1, concept_id2, "RELATED_TO")
    
    # User interaction tracking
    
    async def create_or_get_user(self, user_id: str, name: Optional[str] = None) -> str:
        """Create or get a user node and return its ID"""
        query = """
        MERGE (u:User {id: $user_id})
        ON CREATE SET u.name = $name
        RETURN u.id as id
        """
        result = await self.run_query(query, {"user_id": user_id, "name": name or user_id})
        return result[0]["id"] if result else user_id
    
    async def track_user_viewed_document(self, user_id: str, document_path: str) -> Dict:
        """Record that a user has viewed a document"""
        user_id = await self.create_or_get_user(user_id)
        doc = await self.find_document(document_path)
        if not doc or "id" not in doc:
            return {}
            
        query = """
        MATCH (u:User {id: $user_id}), (d:Document {id: $doc_id})
        MERGE (u)-[r:VIEWED]->(d)
        ON CREATE SET r.first_viewed = datetime()
        SET r.last_viewed = datetime(), r.view_count = COALESCE(r.view_count, 0) + 1
        RETURN r
        """
        result = await self.run_query(query, {"user_id": user_id, "doc_id": doc["id"]})
        return result[0]["r"] if result else {}
    
    # Question-answer relationships
    
    async def create_question(self, content: str) -> str:
        """Create a question node and return its ID"""
        question_id = str(uuid.uuid4())
        query = """
        CREATE (q:Question {
            id: $id,
            content: $content,
            created_at: datetime()
        })
        RETURN q.id as id
        """
        result = await self.run_query(query, {"id": question_id, "content": content})
        return result[0]["id"] if result else question_id
    
    async def link_question_to_document(self, question_id: str, document_path: str) -> Dict:
        """Link a question to a document that answers it"""
        doc = await self.find_document(document_path)
        if not doc or "id" not in doc:
            return {}
            
        return await self.create_relationship(question_id, doc["id"], "ANSWERED_BY")
    
    # Enhanced document reference management
    
    async def create_document_reference(self, from_document_path: str, to_document_path: str, 
                                      ref_type: str = "REFERENCES", context: Optional[str] = None) -> Dict:
        """Create a reference relationship between two documents"""
        from_doc = await self.find_document(from_document_path)
        to_doc = await self.find_document(to_document_path)
        
        if not from_doc or not to_doc or "id" not in from_doc or "id" not in to_doc:
            return {}
            
        query = f"""
        MATCH (d1:Document {{id: $from_id}}), (d2:Document {{id: $to_id}})
        CREATE (d1)-[r:REFERENCES {{type: $ref_type, context: $context, created_at: datetime()}}]->(d2)
        RETURN r
        """
        result = await self.run_query(query, {
            "from_id": from_doc["id"], 
            "to_id": to_doc["id"],
            "ref_type": ref_type,
            "context": context
        })
        return result[0]["r"] if result else {}

    # Legacy methods for backward compatibility
    
    async def create_or_get_source(self, path: str) -> str:
        """Legacy method - creates a Resource instead"""
        return await self.create_resource(path, "file")
    
    async def link_document_to_source(self, document_id: str, source_path: str) -> Dict:
        """Legacy method - links document to a Resource using REFERENCES relationship"""
        return await self.link_document_to_resource(document_id, source_path, "file")
    
    # Document chunk methods
    
    async def create_document_chunk(self, parent_doc_id: str, chunk_index: int, content: str, embedding: List[float],
                                 path: str, content_hash: str, metadata: Optional[Dict] = None) -> Dict:
        """Create a document chunk node with content and embedding"""
        # Generate a random UUID
        chunk_id = f"{parent_doc_id}_chunk_{chunk_index}"
        query = """
        CREATE (c:DocumentChunk {
            id: $id,
            path: $path,
            content: $content,
            embedding: $embedding,
            content_hash: $content_hash,
            embedding_version: "text-embedding-3-small",
            chunk_index: $chunk_index,
            parent_document_id: $parent_doc_id,
            updated_at: $updated_at
        })
        RETURN c
        """
        
        params = {
            "id": chunk_id,
            "path": path,
            "content": content,
            "embedding": embedding,
            "content_hash": content_hash,
            "chunk_index": chunk_index,
            "parent_document_id": parent_doc_id,
            "updated_at": datetime.now().isoformat()
        }
        
        # Add any additional metadata
        if metadata:
            for key, value in metadata.items():
                if key not in params:
                    params[f"c.{key}"] = value
                    
        result = await self.run_query(query, params)
        
        # Create CHUNK_OF relationship
        if result and result[0]["c"]:
            chunk = result[0]["c"]
            await self.create_relationship(chunk["id"], parent_doc_id, "CHUNK_OF")
            
        return result[0]["c"] if result else {}
    
    async def get_document_chunks(self, parent_doc_id: str) -> List[Dict]:
        """Get all chunks of a document"""
        query = """
        MATCH (c:DocumentChunk)-[:CHUNK_OF]->(d:Document {id: $parent_doc_id})
        RETURN c
        ORDER BY c.chunk_index
        """
        result = await self.run_query(query, {"parent_doc_id": parent_doc_id})
        return [r["c"] for r in result] if result else []
    
    async def semantic_search_chunks(self, query_embedding: List[float], limit: int = 10) -> List[Dict]:
        """Search document chunks by vector similarity"""
        query = """
        MATCH (c:DocumentChunk)
        WHERE c.embedding IS NOT NULL
        WITH c, mg.vectors.cosine(c.embedding, $query_embedding) AS score
        MATCH (c)-[:CHUNK_OF]->(d:Document)
        ORDER BY score DESC
        LIMIT $limit
        RETURN c.path AS path, c.content AS content, score, 
               c.chunk_index as chunk_index, d.path as parent_path, 
               d.title as parent_title
        """
        return await self.run_query(query, {"query_embedding": query_embedding, "limit": limit})
    
    async def semantic_search_chunks_fallback(self, query_embedding: List[float], limit: int = 10) -> List[Dict]:
        """Fallback chunk search method when vector functions are not available"""
        query = """
        MATCH (c:DocumentChunk)
        WHERE c.embedding IS NOT NULL
        MATCH (c)-[:CHUNK_OF]->(d:Document)
        RETURN c.path AS path, c.content AS content, c.embedding AS embedding,
               c.chunk_index as chunk_index, d.path as parent_path,
               d.title as parent_title
        """
        all_chunks = await self.run_query(query)
        
        # Calculate similarity scores on the client side
        scored_chunks = []
        for chunk in all_chunks:
            if "embedding" not in chunk or not chunk["embedding"]:
                continue
                
            # Calculate cosine similarity
            score = self._cosine_similarity(chunk["embedding"], query_embedding)
            chunk_result = {
                "path": chunk["path"],
                "content": chunk["content"],
                "score": score,
                "chunk_index": chunk.get("chunk_index", 0),
                "parent_path": chunk.get("parent_path", ""),
                "parent_title": chunk.get("parent_title", "")
            }
            scored_chunks.append(chunk_result)
        
        # Sort by score and return top results
        scored_chunks.sort(key=lambda x: x["score"], reverse=True)
        return scored_chunks[:limit]
    
    async def find_document_chunk(self, path: str) -> Optional[Dict]:
        """Find document chunk by path"""
        query = """
        MATCH (c:DocumentChunk {path: $path})
        RETURN c
        """
        result = await self.run_query(query, {"path": path})
        return result[0]["c"] if result else None
    
    async def conversation_aware_search_chunks(self, 
                                           query_embedding: List[float], 
                                           conversation_id: Optional[str] = None, 
                                           limit: int = 10) -> List[Dict]:
        """Search document chunks and past conversations based on query relevance"""
        try:
            # First try to find relevant document chunks
            chunks = await self.semantic_search_chunks(query_embedding, limit)
            
            # If a conversation ID is provided, also find related conversations
            if conversation_id:
                conv_query = """
                MATCH (c:Conversation)
                WHERE c.id <> $current_conversation_id AND c.summary_embedding IS NOT NULL
                WITH c, mg.vectors.cosine(c.summary_embedding, $query_embedding) AS score
                WHERE score > 0.7
                ORDER BY score DESC
                LIMIT 3
                
                // Get messages from those conversations
                MATCH (m:Message)-[:PART_OF]->(c)
                RETURN m.content as content, c.summary as conversation_summary, 
                       score as relevance, c.id as conversation_id
                ORDER BY c.start_time, m.timestamp
                LIMIT 5
                """
                conv_results = await self.run_query(conv_query, {
                    "current_conversation_id": conversation_id,
                    "query_embedding": query_embedding
                })
                
                # Combine document results with conversation results
                if conv_results:
                    # Format conversation results to match chunk format
                    for i, conv in enumerate(conv_results):
                        chunks.append({
                            "path": f"conversation/{conv['conversation_id']}",
                            "content": conv["content"],
                            "score": conv["relevance"],
                            "parent_title": f"Past Conversation: {conv.get('conversation_summary', 'Unnamed')}",
                            "parent_path": f"conversation://{conv['conversation_id']}"
                        })
                    
                    # Re-sort by score
                    chunks.sort(key=lambda x: x.get("score", 0), reverse=True)
                    chunks = chunks[:limit]
            
            return chunks
        except Exception:
            # Fallback to standard semantic search
            return await self.semantic_search_chunks_fallback(query_embedding, limit)
    
def standardize_resource_uri(path: str) -> str:
    """Standardize resource URIs for consistent reference matching"""
    # Convert to absolute path if possible
    if os.path.exists(path):
        path = os.path.abspath(path)
    
    # Normalize path separators
    path = path.replace('\\', '/')
    
    # Determine resource type and format URI appropriately
    if path.startswith(('http://', 'https://')):
        return path  # Already a well-formed web URI
    
    # For file paths, ensure they have a proper file:// scheme if they're absolute
    if os.path.isabs(path):
        if not path.startswith('file://'):
            # Handle Windows drive letter properly
            if len(path) > 1 and path[1] == ':':  # Windows path with drive letter
                return f"file:///{path}"
            return f"file://{path}"
    
    return path

# Alias for backward compatibility
standardize_source_path = standardize_resource_uri

# Example query functions
async def example_queries(client: MemGraphClient):
    """Run example queries demonstrating the graph structure"""
    
    # Example 1: Find documents that refer to a specific symbol
    symbol_query = """
    MATCH (d:Document)-[:REFERS_TO]->(s:Symbol {name: $symbol_name})
    RETURN d.path AS document_path, d.updated_at AS last_updated
    """
    symbol_results = await client.run_query(symbol_query, {"symbol_name": "Retriever"})
    print("Documents referring to 'Retriever' symbol:")
    for result in symbol_results:
        print(f"  - {result['document_path']} (Updated: {result['last_updated']})")
    
    # Example 2: Find tools and their implementation files
    tools_query = """
    MATCH (t:Tool)-[:DEFINED_IN]->(d:Document)
    RETURN t.name AS tool_name, d.path AS implementation_path
    """
    tools_results = await client.run_query(tools_query)
    print("\nTools and their implementations:")
    for result in tools_results:
        print(f"  - {result['tool_name']}: {result['implementation_path']}")
    
    # Example 3: Find documents that link to external URLs
    urls_query = """
    MATCH (d:Document)-[:LINKS_TO]->(u:URL)
    RETURN d.path AS document_path, u.href AS external_link
    LIMIT 5
    """
    urls_results = await client.run_query(urls_query)
    print("\nDocuments with external links:")
    for result in urls_results:
        print(f"  - {result['document_path']} links to {result['external_link']}")
    
    # Example 4: Find related documents based on shared symbols
    related_query = """
    MATCH (d1:Document)-[:REFERS_TO]->(s:Symbol)<-[:REFERS_TO]-(d2:Document)
    WHERE d1.path = $document_path AND d1 <> d2
    RETURN d2.path AS related_document, COUNT(s) AS shared_symbols
    ORDER BY shared_symbols DESC
    LIMIT 5
    """
    related_results = await client.run_query(related_query, {"document_path": "src/rag/retriever.py"})
    print("\nDocuments related to 'src/rag/retriever.py' by shared symbols:")
    for result in related_results:
        print(f"  - {result['related_document']} ({result['shared_symbols']} shared symbols)")
    
    # Example 5: Semantic search with a sample vector (normally from embedding)
    # Using a placeholder vector of the right dimension
    sample_vector = [0.01] * 1536  # Normally this would be from an embedding model
    semantic_results = await client.semantic_search(sample_vector, 3)
    print("\nSemantic search results:")
    for result in semantic_results:
        print(f"  - {result['path']} (Similarity score: {result['score']:.4f})")
    
    # Example 6: Query conversations by topic
    if await client.run_query("MATCH (c:Conversation) RETURN count(c) > 0 as has_convs"):
        conv_query = """
        MATCH (c:Conversation)
        RETURN c.id as id, c.title as title, c.summary as summary
        LIMIT 3
        """
        conv_results = await client.run_query(conv_query)
        print("\nRecent conversations:")
        for result in conv_results:
            print(f"  - {result['title']}: {result.get('summary', 'No summary')[:50]}...")

async def main():
    client = MemGraphClient()
    try:
        # Create vector index if it doesn't exist
        await client.create_vector_index()
        
        # Run example queries
        await example_queries(client)
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())