import os
from typing import Dict, List, Any, Optional
import asyncio
from neo4j import AsyncGraphDatabase
from dotenv import load_dotenv

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
    
    async def create_document(self, path: str, content: str, embedding: List[float]) -> Dict:
        """Create a document node with content and embedding"""
        query = """
        CREATE (d:Document {
            id: randomUUID(),
            path: $path,
            content: $content,
            embedding: $embedding,
            content_hash: apoc.util.sha256([content]),
            embedding_version: "text-embedding-ada-002",
            updated_at: datetime()
        })
        RETURN d
        """
        result = await self.run_query(query, {"path": path, "content": content, "embedding": embedding})
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
                           content_hash: str, embedding_version: str, updated_at: str) -> Dict:
        """Update or insert document"""
        query = """
        MERGE (d:Document {path: $path})
        SET d.content = $content,
            d.embedding = $embedding,
            d.content_hash = $content_hash,
            d.embedding_version = $embedding_version,
            d.updated_at = $updated_at
        RETURN d
        """
        params = {
            "path": path,
            "content": content,
            "embedding": embedding,
            "content_hash": content_hash,
            "embedding_version": embedding_version,
            "updated_at": updated_at
        }
        result = await self.run_query(query, params)
        return result[0]["d"] if result else {}
    
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
    
    async def semantic_search(self, query_embedding: List[float], limit: int = 5) -> List[Dict]:
        """Search documents by vector similarity"""
        query = """
        MATCH (d:Document)
        WHERE d.embedding IS NOT NULL
        WITH d, vector.similarity(d.embedding, $query_embedding) AS score
        ORDER BY score DESC
        LIMIT $limit
        RETURN d.path AS path, d.content AS content, score
        """
        return await self.run_query(query, {"query_embedding": query_embedding, "limit": limit})
    
    async def semantic_search_fallback(self, query_embedding: List[float], limit: int = 5) -> List[Dict]:
        """Fallback search method when vector functions are not available
        This method fetches all documents and computes similarity on the client side"""
        query = """
        MATCH (d:Document)
        WHERE d.embedding IS NOT NULL
        RETURN d.path AS path, d.content AS content, d.embedding AS embedding
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
                "score": score
            })
        
        # Sort by score and return top results
        scored_docs.sort(key=lambda x: x["score"], reverse=True)
        return scored_docs[:limit]
    
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
        """Create a vector index for document embeddings"""
        query = """
        CREATE VECTOR INDEX document_embedding IF NOT EXISTS
        FOR (d:Document)
        ON d.embedding
        OPTIONS {indexConfig: {
          `vector.dimensions`: 1536,
          `vector.similarity_function`: 'cosine'
        }}
        """
        await self.run_query(query)

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