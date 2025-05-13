import os
from typing import Dict, List, Any, Optional, Union
import asyncio
from datetime import datetime
import json
from neo4j import AsyncGraphDatabase
from dotenv import load_dotenv
import uuid

# Load environment variables from .env file
load_dotenv()

class Neo4jClient:
    def __init__(self, 
                 uri: Optional[str] = None, 
                 username: Optional[str] = None, 
                 password: Optional[str] = None, 
                 max_connection_pool_size: int = 50):
        """Initialize Neo4j client with connection parameters"""
        self.uri = uri or os.environ.get("NEO4J_URI", "bolt://localhost:7687")
        self.username = username or os.environ.get("NEO4J_USER", "neo4j")
        self.password = password or os.environ.get("NEO4J_PASSWORD", "password")
        
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
                           mime_type: Optional[str] = None, source_path: Optional[str] = None) -> Dict:
        """Create a document node with content and embedding"""
        query = """
        CREATE (d:Document {
            id: randomUUID(),
            path: $path,
            content: $content,
            embedding: $embedding,
            content_hash: apoc.util.sha256([content]),
            embedding_version: "text-embedding-ada-002",
            updated_at: datetime(),
            title: $title,
            author: $author,
            mime_type: $mime_type,
            source_path: $source_path
        })
        RETURN d
        """
        params = {
            "path": path,
            "content": content,
            "embedding": embedding,
            "title": title or os.path.basename(path),
            "author": author,
            "mime_type": mime_type,
            "source_path": source_path or standardize_source_path(path)
        }
        result = await self.run_query(query, params)
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
                           mime_type: Optional[str] = None, source_path: Optional[str] = None) -> Dict:
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
            d.mime_type = $mime_type,
            d.source_path = $source_path
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
            "mime_type": mime_type,
            "source_path": source_path or standardize_source_path(path)
        }
        result = await self.run_query(query, params)
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
    
    async def create_url_link(self, url: str, document_path: str) -> Dict:
        """Create a URL node and link it to a document"""
        query = """
        MATCH (d:Document {path: $document_path})
        MERGE (u:URL {href: $url})
        CREATE (d)-[:LINKS_TO]->(u)
        RETURN u
        """
        result = await self.run_query(query, {"url": url, "document_path": document_path})
        return result[0]["u"] if result else {}
    
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
        query = """
        CREATE (c:Conversation {
            id: randomUUID(),
            start_time: datetime(),
            title: $title
        })
        RETURN c.id as id
        """
        result = await self.run_query(query, {"title": title or "New Conversation"})
        return result[0]["id"] if result else str(uuid.uuid4())
    
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
        query = """
        MATCH (c:Conversation {id: $conversation_id})
        CREATE (m:Message {
            id: randomUUID(),
            content: $content,
            role: $role,
            timestamp: $timestamp
        })
        CREATE (m)-[:PART_OF]->(c)
        RETURN m.id as id
        """
        params = {
            "conversation_id": conversation_id,
            "content": content,
            "role": role,
            "timestamp": timestamp.isoformat()
        }
        result = await self.run_query(query, params)
        message_id = result[0]["id"] if result else str(uuid.uuid4())
        
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
        result = await self.run_query(query, {"message_id": message_id, "document_id": document_id})
        return result[0] if result else {}
    
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
        query = """
        MERGE (c:Concept {name: $name})
        RETURN c.id as id
        """
        result = await self.run_query(query, {"name": name})
        return result[0]["id"] if result else str(uuid.uuid4())
    
    async def create_or_get_entity(self, name: str, entity_type: str) -> str:
        """Create or get an entity node and return its ID"""
        query = """
        MERGE (e:Entity {name: $name, type: $entity_type})
        RETURN e.id as id
        """
        result = await self.run_query(query, {"name": name, "entity_type": entity_type})
        return result[0]["id"] if result else str(uuid.uuid4())
    
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
        WHERE datetime() > c.start_time + duration({days: $days})
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
        """Search documents by vector similarity"""
        query = """
        MATCH (d:Document)
        WHERE d.embedding IS NOT NULL
        WITH d, vector.similarity(d.embedding, $query_embedding) AS score
        ORDER BY score DESC
        LIMIT $limit
        RETURN d.path AS path, d.content AS content, score, d.title as title, 
               d.author as author, d.updated_at as updated_at, d.source_path as source_path
        """
        return await self.run_query(query, {"query_embedding": query_embedding, "limit": limit})
    
    async def semantic_search_fallback(self, query_embedding: List[float], limit: int = 5) -> List[Dict]:
        """Fallback search method when vector functions are not available
        This method fetches all documents and computes similarity on the client side"""
        query = """
        MATCH (d:Document)
        WHERE d.embedding IS NOT NULL
        RETURN d.path AS path, d.content AS content, d.embedding AS embedding,
               d.title as title, d.author as author, d.updated_at as updated_at, 
               d.source_path as source_path
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
                "source_path": doc.get("source_path", "")
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
                WITH c, vector.similarity(c.summary_embedding, $query_embedding) AS score
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
                            "source_path": "conversation_history"
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
        """Create vector indices for documents and message embeddings"""
        # Create document embedding index
        document_query = """
        CREATE VECTOR INDEX document_embedding IF NOT EXISTS
        FOR (d:Document)
        ON d.embedding
        OPTIONS {indexConfig: {
          `vector.dimensions`: 1536,
          `vector.similarity_function`: 'cosine'
        }}
        """
        await self.run_query(document_query)
        
        # Create message embedding index
        message_query = """
        CREATE VECTOR INDEX message_embedding IF NOT EXISTS
        FOR (m:Message)
        ON m.embedding
        OPTIONS {indexConfig: {
          `vector.dimensions`: 1536,
          `vector.similarity_function`: 'cosine'
        }}
        """
        await self.run_query(message_query)
        
        # Create text index for conversation summaries
        summary_query = """
        CREATE TEXT INDEX conversation_summary IF NOT EXISTS
        FOR (c:Conversation)
        ON c.summary
        """
        await self.run_query(summary_query)

def standardize_source_path(path: str) -> str:
    """Standardize source paths for consistent reference matching"""
    # Convert to absolute path if possible
    if os.path.exists(path):
        path = os.path.abspath(path)
    
    # Normalize path separators
    path = path.replace('\\', '/')
    
    # Remove URI schemes if present
    uri_schemes = ['file://', 'http://', 'https://']
    for scheme in uri_schemes:
        if path.startswith(scheme):
            path = path[len(scheme):]
    
    return path

# Example query functions
async def example_queries(client: Neo4jClient):
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
    client = Neo4jClient()
    try:
        # Create vector index if it doesn't exist
        await client.create_vector_index()
        
        # Run example queries
        await example_queries(client)
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())