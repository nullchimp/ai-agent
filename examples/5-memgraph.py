import asyncio
import os
from dotenv import load_dotenv
# Force reload of environment variables to avoid cached data
load_dotenv(override=True)

from typing import List, Dict, Any, Optional
from datetime import datetime
import hashlib
import json
from core.rag.graph_client import MemGraphClient, standardize_resource_uri

async def create_sample_data(client: MemGraphClient):
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
            "content": "# RAG Usage\nThe Retriever class can be used to fetch relevant documents.\nSee [MemGraph documentation](https://memgraph.com/docs/) for more details."
        }
    ]
    
    # Create sample documents with mock embeddings
    for doc in documents:
        # Generate a simple mock embedding (in real app, this would come from an embedding model)
        mock_embedding = generate_mock_embedding(doc["content"])
        print(f"Generated mock embedding for {doc['path']}")
        
        # Calculate content hash
        content_hash = hashlib.sha256(doc["content"].encode()).hexdigest()
        
        # Store the document with source path and title metadata
        await client.upsert_document(
            path=doc["path"],
            content=doc["content"],
            embedding=mock_embedding,
            content_hash=content_hash,
            embedding_version="text-embedding-3-small",
            updated_at=datetime.now().isoformat(),
            title=os.path.basename(doc["path"])
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
    await client.create_url_link("https://memgraph.com/docs/", "docs/usage/rag.md")
    
    # Create additional Resource nodes
    await client.create_resource("https://github.com/nullchimp/ai-agent", "github", "Project repository")
    await client.create_resource("https://platform.openai.com/docs/guides/embeddings", "web", "OpenAI Embeddings documentation")
    await client.create_resource("file:///data/training/embeddings_dataset.jsonl", "dataset", "Training dataset for embeddings")
    
    # Link documents to additional resources
    doc = await client.find_document("src/rag/retriever.py")
    if doc and "id" in doc:
        await client.link_document_to_resource(doc["id"], "https://platform.openai.com/docs/guides/embeddings", "web")
        await client.link_document_to_resource(doc["id"], "file:///data/training/embeddings_dataset.jsonl", "dataset")
    
    # Create tool definitions
    tools = ["RetrieveTool", "IndexTool"]
    for tool in tools:
        if tool == "RetrieveTool":
            await client.create_tool(tool, "src/rag/retriever.py")
        elif tool == "IndexTool":
            await client.create_tool(tool, "src/rag/indexer.py")
    
    # Create sample conversation with messages
    print("\nCreating sample conversation...")
    conversation_id = await client.create_conversation("RAG Implementation Discussion")
    
    # Add conversation messages
    messages = [
        {"role": "user", "content": "How can we implement a Retrieval-Augmented Generation system?"},
        {"role": "assistant", "content": "RAG systems combine retrieval of relevant documents with generative AI. You'll need a vector database for document storage and similarity search."},
        {"role": "user", "content": "Which vector database would work best with MemGraph?"},
        {"role": "assistant", "content": "MemGraph itself can serve as your vector database with its vector search capabilities. MemGraph has built-in vector similarity functions like mg.vectors.cosine() for efficient embedding similarity searches."}
    ]
    
    # Add each message with a timestamp
    message_ids = []
    for i, msg in enumerate(messages):
        timestamp = datetime.now()
        message_id = await client.add_message(
            conversation_id=conversation_id,
            content=msg["content"],
            role=msg["role"],
            timestamp=timestamp
        )
        message_ids.append(message_id)
        print(f"Added message: {msg['role']} - {msg['content'][:40]}...")
    
    # Extract concepts from the conversation (simplified version)
    concepts = ["RAG", "Vector Database", "MemGraph", "Embedding", "Similarity Search"]
    for concept in concepts:
        for message_id in message_ids:
            await client.link_message_to_concept(message_id, concept)
            print(f"Linked concept '{concept}' to message {message_id}")
    
    # Add document references to messages
    await client.create_message_document_reference(message_ids[1], "src/rag/retriever.py")
    await client.create_message_document_reference(message_ids[3], "docs/usage/rag.md")
    
    # Create a conversation summary
    summary = "Discussion about implementing a RAG system using MemGraph for vector similarity search and document storage."
    summary_embedding = generate_mock_embedding(summary)
    await client.update_conversation(
        conversation_id=conversation_id,
        properties={
            "summary": summary,
            "summary_embedding": summary_embedding,
            "sentiment": "positive",
            "topic_clusters": ["RAG", "Vector Database", "Knowledge Graph"]
        }
    )
    
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

def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Calculate cosine similarity between two vectors"""
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    magnitude1 = sum(a * a for a in vec1) ** 0.5
    magnitude2 = sum(b * b for b in vec2) ** 0.5
    if magnitude1 * magnitude2 == 0:
        return 0
    return dot_product / (magnitude1 * magnitude2)

async def perform_client_side_semantic_search(client: MemGraphClient, query_embedding: List[float], limit: int = 3) -> List[Dict[str, Any]]:
    """Perform semantic search on the client side when vector functions aren't available in MemGraph"""
    # Get all documents with embeddings
    query = """
    MATCH (d:Document)
    WHERE d.embedding IS NOT NULL
    OPTIONAL MATCH (d)-[:REFERENCES]->(r:Resource)
    RETURN d.path AS path, d.title AS title, d.embedding,
           r.uri as resource_uri, r.type as resource_type
    """
    results = await client.run_query(query)
    
    # Calculate similarity scores
    scored_results = []
    for result in results:
        doc_embedding = result.get("embedding", [])
        if doc_embedding:
            score = cosine_similarity(query_embedding, doc_embedding)
            scored_results.append({
                "path": result.get("path", "Unknown path"),
                "title": result.get("title", os.path.basename(result.get("path", "Unknown"))),
                "score": score,
                "resource_uri": result.get("resource_uri"),
                "resource_type": result.get("resource_type")
            })
    
    # Sort by score and limit results
    scored_results.sort(key=lambda x: x["score"], reverse=True)
    return scored_results[:limit]

async def perform_example_queries(client: MemGraphClient):
    """Perform key example queries to demonstrate the graph structure"""
    
    print("\n=== Example 1: Find documents by symbol ===")
    query1 = """
    MATCH (d:Document)-[:REFERS_TO]->(s:Symbol {name: $symbol})
    RETURN d.path AS path, d.content AS content
    """
    results1 = await client.run_query(query1, {"symbol": "Retriever"})
    if not results1:
        print("No results found for documents with symbol 'Retriever'")
    else:
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
    if not results2:
        print("No related documents found through shared symbols")
    else:
        for result in results2:
            print(f"Related document: {result['related_doc']}")
            print(f"Shared symbol: {result['shared_symbol']}\n")
    
    print("\n=== Example 3: Find Resource nodes and their types ===")
    query3 = """
    MATCH (r:Resource)
    RETURN r.uri AS uri, r.type AS type, r.description AS description
    """
    results3 = await client.run_query(query3)
    if not results3:
        print("No resources found")
    else:
        for result in results3:
            print(f"Resource URI: {result['uri']}")
            print(f"Type: {result['type']}")
            print(f"Description: {result.get('description', 'No description')}\n")
    
    print("\n=== Example 4: Find documents linked to specific resource types ===")
    query4 = """
    MATCH (d:Document)-[:REFERENCES]->(r:Resource)
    WHERE r.type = $resource_type
    RETURN d.path AS document, r.uri AS resource_uri
    """
    results4 = await client.run_query(query4, {"resource_type": "web"})
    if not results4:
        print("No documents with web resources found")
    else:
        for result in results4:
            print(f"Document: {result['document']}")
            print(f"Links to web resource: {result['resource_uri']}\n")
    
    print("\n=== Example 5: Semantic search with resources ===")
    # Generate a mock query embedding
    query_text = "retrieve relevant documents for user query"
    query_embedding = generate_mock_embedding(query_text)
    print(f"Searching for: '{query_text}'")
    
    try:
        # First try using vector similarity if available in MemGraph
        query5 = """
        MATCH (d:Document)
        WHERE d.embedding IS NOT NULL
        WITH d, mg.vectors.cosine(d.embedding, $embedding) AS score
        OPTIONAL MATCH (d)-[:REFERENCES]->(r:Resource)
        ORDER BY score DESC
        LIMIT 3
        RETURN d.path AS path, score, r.uri AS resource_uri, r.type AS resource_type
        """
        results5 = await client.run_query(query5, {"embedding": query_embedding})
        print("Using native MemGraph vector similarity search")
    except Exception as e:
        print(f"Vector search error: {e}")
        print("Falling back to client-side similarity calculation")
        # Perform client-side similarity calculation as fallback
        results5 = await perform_client_side_semantic_search(client, query_embedding)
    
    if not results5:
        print("No semantic search results found")
    else:
        for result in results5:
            # Handle both key formats (path or document)
            doc_path = result.get("path", result.get("document", "Unknown document"))
            score = result.get("score", 0.0)
            resource_uri = result.get("resource_uri", "No linked resource")
            resource_type = result.get("resource_type", "unknown")
            print(f"Document: {doc_path}")
            print(f"Relevance score: {score:.4f}")
            if resource_uri != "No linked resource":
                print(f"Associated resource: {resource_uri} (Type: {resource_type})")
            print()
    
    print("\n=== Example 6: Find messages that reference documents with specific resource types ===")
    query6 = """
    MATCH (m:Message)-[:REFERENCES]->(d:Document)-[:REFERENCES]->(r:Resource)
    WHERE r.type = 'web'
    RETURN m.role AS role, m.content AS content, d.path AS document_path, r.uri AS resource_uri
    LIMIT 5
    """
    results6 = await client.run_query(query6)
    if not results6:
        print("No messages found referencing documents with web resources")
    else:
        for result in results6:
            print(f"Role: {result['role']}")
            print(f"Content: {result['content'][:50]}...")
            print(f"Referenced document: {result['document_path']}")
            print(f"Document links to: {result['resource_uri']}\n")
    
    print("\n=== Example 7: Find concepts mentioned in conversations ===")
    query7 = """
    MATCH (m:Message)-[:MENTIONS]->(c:Concept)
    RETURN c.name AS concept, COUNT(m) AS mentions ORDER BY mentions DESC
    """
    results7 = await client.run_query(query7)
    if not results7:
        print("No concepts found in conversations")
    else:
        for result in results7:
            print(f"Concept: {result['concept']}")
            print(f"Mentioned in {result['mentions']} messages\n")
    
    print("\n=== Example 8: Conversation-aware semantic search ===")
    # Simulate conversation context - find documents relevant to ongoing conversation
    query_text = "How can MemGraph be used for vector similarity search?"
    query_embedding = generate_mock_embedding(query_text)
    print(f"Searching for documents relevant to: '{query_text}'")
    
    # Get a conversation ID for context
    conversation_query = "MATCH (c:Conversation) RETURN c.id AS id LIMIT 1"
    conversation_result = await client.run_query(conversation_query)
    
    if not conversation_result:
        print("No conversations found for context-aware search")
    else:
        conversation_id = conversation_result[0]["id"]
        print(f"Using conversation context: {conversation_id}")
        
        try:
            # Try to use client's conversation-aware search
            results8 = await client.conversation_aware_search(
                query_embedding=query_embedding,
                conversation_id=conversation_id,
                limit=3
            )
        except Exception as e:
            print(f"Conversation-aware search error: {e}")
            print("Falling back to standard semantic search")
            # Fallback to perform semantic search without conversation context
            results8 = await perform_client_side_semantic_search(client, query_embedding)
        
        if not results8:
            print("No documents found relevant to the conversation")
        else:
            print("Results with conversation context:")
            for result in results8:
                doc_path = result.get("path", "Unknown")
                score = result.get("score", 0.0)
                title = result.get("title", os.path.basename(doc_path))
                resource_uri = result.get("resource_uri", "No linked resource")
                print(f"Document: {title}")
                print(f"Path: {doc_path}")
                print(f"Relevance score: {score:.4f}")
                if resource_uri != "No linked resource":
                    print(f"Associated resource: {resource_uri}")
                print()
    
    print("\n=== Example 9: Resource usage statistics ===")
    query9 = """
    MATCH (r:Resource)<-[:REFERENCES]-(d:Document)
    RETURN r.uri AS resource_uri, r.type AS resource_type, COUNT(d) AS document_count
    ORDER BY document_count DESC
    """
    results9 = await client.run_query(query9)
    print("Resources by document reference count:")
    if not results9:
        print("No resources with document references found")
    else:
        for result in results9:
            print(f"Resource: {result['resource_uri']}")
            print(f"Type: {result['resource_type']}")
            print(f"Referenced by {result['document_count']} documents\n")
    
    print("\n=== Example 10: Group documents by resource type ===")
    query10 = """
    MATCH (d:Document)-[:REFERENCES]->(r:Resource)
    RETURN r.type AS resource_type, COLLECT(d.path) AS documents
    """
    results10 = await client.run_query(query10)
    if not results10:
        print("No document groups by resource type found")
    else:
        for result in results10:
            print(f"Resource type: {result['resource_type']}")
            docs = result['documents']
            print(f"Documents ({len(docs)}):")
            for doc in docs[:3]:  # Show only first 3 documents for brevity
                print(f"  - {doc}")
            if len(docs) > 3:
                print(f"  ... and {len(docs) - 3} more")
            print()
    
    print("Demonstration complete!")

async def main():
    # Check if environment variables are set
    uri = os.environ.get("MEMGRAPH_URI") or "bolt://localhost:7687"
    if not uri:
        print("Warning: MEMGRAPH_URI environment variable not set. Using default.")
    
    # Initialize client
    client = MemGraphClient()
    try:
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