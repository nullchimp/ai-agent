import asyncio
import os
from typing import List
from datetime import datetime
import hashlib
from rag.graph_client import Neo4jClient

async def create_sample_data(client: Neo4jClient):
    """Create sample data to demonstrate the graph structure"""
    
    # Sample documents
    documents = [
        {
            "path": "src/rag/retriever.py",
            "content": "class Retriever:\n    def retrieve(self, query: str):\n        # Get query embedding\n        # Find similar documents\n        return documents"
        },
        {
            "path": "src/rag/prompt_builder.py",
            "content": "def build(messages, docs):\n    # Create prompt with context\n    return {'role': 'system', 'content': 'Context:\\n' + '\\n'.join(docs)}"
        },
        {
            "path": "src/rag/indexer.py",
            "content": "class DocumentIndexer:\n    def index_document(self, path, content):\n        # Calculate hash\n        # Generate embedding\n        # Store in database"
        },
        {
            "path": "tests/rag/test_retriever.py",
            "content": "def test_retriever():\n    retriever = Retriever()\n    docs = retriever.retrieve('test query')\n    assert len(docs) > 0"
        },
        {
            "path": "docs/usage/rag.md",
            "content": "# RAG Usage\nThe Retriever class can be used to fetch relevant documents.\nSee [Neo4j documentation](https://neo4j.com/docs/) for more details."
        }
    ]
    
    # Create sample documents with mock embeddings
    for doc in documents:
        # Generate a simple mock embedding (in real app, this would come from an embedding model)
        mock_embedding = generate_mock_embedding(doc["content"])
        print(f"Generated mock embedding for {doc['path']}")
        
        # Calculate content hash
        content_hash = hashlib.sha256(doc["content"].encode()).hexdigest()
        
        # Store the document
        await client.upsert_document(
            path=doc["path"],
            content=doc["content"],
            embedding=mock_embedding,
            content_hash=content_hash,
            embedding_version="text-embedding-ada-002",
            updated_at=datetime.now().isoformat()
        )
    
    # Create symbols and relationships
    symbols = ["Retriever", "DocumentIndexer", "build", "retrieve", "index_document"]
    for symbol in symbols:
        if symbol == "Retriever":
            await client.create_symbol(symbol, "src/rag/retriever.py")
            await client.create_symbol(symbol, "tests/rag/test_retriever.py")
        elif symbol == "DocumentIndexer":
            await client.create_symbol(symbol, "src/rag/indexer.py")
        elif symbol == "build":
            await client.create_symbol(symbol, "src/rag/prompt_builder.py")
        elif symbol == "retrieve":
            await client.create_symbol(symbol, "src/rag/retriever.py")
        elif symbol == "index_document":
            await client.create_symbol(symbol, "src/rag/indexer.py")
    
    # Create URL links
    await client.create_url_link("https://neo4j.com/docs/", "docs/usage/rag.md")
    
    # Create tool definitions
    tools = ["RetrieveTool", "IndexTool"]
    for tool in tools:
        if tool == "RetrieveTool":
            await client.create_tool(tool, "src/rag/retriever.py")
        elif tool == "IndexTool":
            await client.create_tool(tool, "src/rag/indexer.py")
    
    print("Sample data created successfully!")

def generate_mock_embedding(text: str) -> List[float]:
    """Generate a simple mock embedding based on text hash (for demo purposes only)"""
    # In a real implementation, this would call an embedding model
    hash_value = hashlib.md5(text.encode()).digest()
    
    # Create a deterministic but seemingly random vector of the right dimension (1536)
    base_values = [float(b) / 255.0 for b in hash_value]
    
    # Repeat the values to fill the 1536 dimensions
    embedding = []
    while len(embedding) < 1536:
        embedding.extend(base_values)
    
    return embedding[:1536]  # Trim to exact length

async def perform_example_queries(client: Neo4jClient):
    """Perform some example queries to demonstrate the graph structure"""
    
    print("\n=== Example 1: Find documents by symbol ===")
    query1 = """
    MATCH (d:Document)-[:REFERS_TO]->(s:Symbol {name: $symbol})
    RETURN d.path AS path, d.content AS content
    """
    results1 = await client.run_query(query1, {"symbol": "Retriever"})
    for result in results1:
        print(f"Document path: {result['path']}")
        print(f"Content snippet: {result['content'][:50]}...\n")
    
    print("\n=== Example 2: Find related documents through shared symbols ===")
    query2 = """
    MATCH (d1:Document {path: $path})-[:REFERS_TO]->(s:Symbol)<-[:REFERS_TO]-(d2:Document)
    WHERE d1 <> d2
    RETURN d2.path AS related_doc, s.name AS shared_symbol
    """
    results2 = await client.run_query(query2, {"path": "src/rag/retriever.py"})
    for result in results2:
        print(f"Related document: {result['related_doc']}")
        print(f"Shared symbol: {result['shared_symbol']}\n")
    
    print("\n=== Example 3: Find tools and their implementations ===")
    query3 = """
    MATCH (t:Tool)-[:DEFINED_IN]->(d:Document)
    RETURN t.name AS tool, d.path AS implementation
    """
    results3 = await client.run_query(query3)
    for result in results3:
        print(f"Tool: {result['tool']}")
        print(f"Implementation: {result['implementation']}\n")
    
    print("\n=== Example 4: Find documents with external links ===")
    query4 = """
    MATCH (d:Document)-[:LINKS_TO]->(u:URL)
    RETURN d.path AS document, u.href AS url
    """
    results4 = await client.run_query(query4)
    for result in results4:
        print(f"Document: {result['document']}")
        print(f"Links to: {result['url']}\n")
    
    print("\n=== Example 5: Semantic search (simulated) ===")
    # Generate a mock query embedding
    query_embedding = generate_mock_embedding("retrieve relevant documents for user query")
    try:
        # First try using vector similarity if available
        query5 = """
        MATCH (d:Document)
        WHERE d.embedding IS NOT NULL
        WITH d, vector.similarity(d.embedding, $embedding) AS score
        ORDER BY score DESC
        LIMIT 3
        RETURN d.path AS path, score
        """
        results5 = await client.run_query(query5, {"embedding": query_embedding})
    except Exception:
        # Fall back to client-side similarity calculation
        results5 = await client.semantic_search_fallback(query_embedding, 3)
    
    for result in results5:
        # Handle both key formats (path or document)
        doc_path = result.get("path", result.get("document", "Unknown document"))
        score = result.get("score", 0.0)
        print(f"Document: {doc_path}")
        print(f"Relevance score: {score:.4f}\n")

async def main():
    # Check if environment variables are set
    uri = os.environ.get("NEO4J_URI")
    if not uri:
        print("Warning: NEO4J_URI environment variable not set. Using default.")
    
    # Initialize client
    client = Neo4jClient()
    try:
        # Create vector index
        await client.create_vector_index()
        
        # Create sample data
        await create_sample_data(client)
        
        # Perform example queries
        await perform_example_queries(client)
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())