import asyncio
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import hashlib
import json
from utils.rag.graph_client import Neo4jClient, standardize_source_path

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
        
        # Store the document with source path and title metadata
        await client.upsert_document(
            path=doc["path"],
            content=doc["content"],
            embedding=mock_embedding,
            content_hash=content_hash,
            embedding_version="text-embedding-ada-002",
            updated_at=datetime.now().isoformat(),
            title=os.path.basename(doc["path"]),
            source_path=standardize_source_path(doc["path"])
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
    
    # Create sample conversation with messages
    print("\nCreating sample conversation...")
    conversation_id = await client.create_conversation("RAG Implementation Discussion")
    
    # Add conversation messages
    messages = [
        {"role": "user", "content": "How can we implement a Retrieval-Augmented Generation system?"},
        {"role": "assistant", "content": "RAG systems combine retrieval of relevant documents with generative AI. You'll need a vector database for document storage and similarity search."},
        {"role": "user", "content": "Which vector database would work best with Neo4j?"},
        {"role": "assistant", "content": "Neo4j itself can serve as your vector database with its vector search capabilities. Starting in Neo4j 5.11, you can create vector indexes to efficiently search embeddings."}
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
    concepts = ["RAG", "Vector Database", "Neo4j", "Embedding", "Similarity Search"]
    for concept in concepts:
        for message_id in message_ids:
            await client.link_message_to_concept(message_id, concept)
            print(f"Linked concept '{concept}' to message {message_id}")
    
    # Add document references to messages
    await client.create_message_document_reference(message_ids[1], "src/rag/retriever.py")
    await client.create_message_document_reference(message_ids[3], "docs/usage/rag.md")
    
    # Create a conversation summary
    summary = "Discussion about implementing a RAG system using Neo4j for vector similarity search and document storage."
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
    
    print("\n=== Example 6: Find conversation messages ===")
    query6 = """
    MATCH (m:Message)-[:PART_OF]->(c:Conversation)
    RETURN m.role AS role, m.content AS content, c.title AS conversation
    LIMIT 5
    """
    results6 = await client.run_query(query6)
    for result in results6:
        print(f"Conversation: {result['conversation']}")
        print(f"Role: {result['role']}")
        print(f"Content: {result['content'][:50]}...\n")
    
    print("\n=== Example 7: Find concepts mentioned in conversations ===")
    query7 = """
    MATCH (m:Message)-[:MENTIONS]->(c:Concept)
    RETURN c.name AS concept, COUNT(m) AS mentions
    GROUP BY c.name
    ORDER BY mentions DESC
    """
    results7 = await client.run_query(query7)
    for result in results7:
        print(f"Concept: {result['concept']}")
        print(f"Mentioned in {result['mentions']} messages\n")
    
    print("\n=== Example 8: Conversation-aware semantic search ===")
    # Simulate conversation context - find documents relevant to ongoing conversation
    query_text = "How can Neo4j be used for vector similarity search?"
    query_embedding = generate_mock_embedding(query_text)
    
    # Get a conversation ID for context
    conversation_query = "MATCH (c:Conversation) RETURN c.id AS id LIMIT 1"
    conversation_result = await client.run_query(conversation_query)
    if conversation_result:
        conversation_id = conversation_result[0]["id"]
        print(f"Using conversation context: {conversation_id}")
        
        # Search using conversation context
        results8 = await client.conversation_aware_search(
            query_embedding=query_embedding,
            conversation_id=conversation_id,
            limit=3
        )
        
        print("Results with conversation context:")
        for result in results8:
            doc_path = result.get("path", "Unknown")
            score = result.get("score", 0.0)
            title = result.get("title", os.path.basename(doc_path))
            print(f"Document: {title}")
            print(f"Path: {doc_path}")
            print(f"Relevance score: {score:.4f}\n")

async def extract_knowledge(client: Neo4jClient, message_id: str) -> Dict[str, Any]:
    """Simulate knowledge extraction from a message (simplified for demo)"""
    # Get message content
    query = """
    MATCH (m:Message {id: $message_id})
    RETURN m.content as content
    """
    result = await client.run_query(query, {"message_id": message_id})
    
    if not result:
        return {"error": "Message not found"}
    
    content = result[0]["content"]
    
    # In a real system, we would use LLM to extract entities and concepts
    # Here we'll use a simple rule-based approach for demonstration
    
    # Simplified extraction logic
    entities = []
    concepts = []
    
    # Simple keyword detection (in a real system, this would use NLP/LLM)
    keywords = ["RAG", "Neo4j", "vector", "embedding", "database", "graph", "retrieval", "generation"]
    
    for keyword in keywords:
        if keyword.lower() in content.lower():
            if keyword in ["Neo4j", "RAG"]:
                entities.append({"name": keyword, "type": "Technology"})
            else:
                concepts.append({"name": keyword.title()})
    
    # Return the extracted knowledge
    return {
        "concepts": concepts,
        "entities": entities,
        "facts": [f"Message mentions {len(concepts)} concepts and {len(entities)} entities"],
    }

async def demonstrate_knowledge_extraction(client: Neo4jClient):
    """Demonstrate the knowledge extraction process"""
    # First, get a sample message
    query = """
    MATCH (m:Message)
    RETURN m.id as id, m.content as content
    LIMIT 1
    """
    result = await client.run_query(query)
    
    if not result:
        print("No messages found to demonstrate knowledge extraction")
        return
    
    message = result[0]
    message_id = message["id"]
    print(f"\n=== Example 9: Knowledge Extraction ===")
    print(f"Message content: {message['content'][:80]}...")
    
    # Extract knowledge from message
    knowledge = await extract_knowledge(client, message_id)
    
    print("\nExtracted knowledge:")
    print(f"Concepts: {[c['name'] for c in knowledge.get('concepts', [])]}")
    print(f"Entities: {[f'{e['name']} ({e['type']})' for e in knowledge.get('entities', [])]}")
    
    # Link extracted concepts to the message
    for concept in knowledge.get("concepts", []):
        await client.link_message_to_concept(message_id, concept["name"])
        print(f"Linked concept '{concept['name']}' to message")

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
        
        # Demonstrate knowledge extraction
        await demonstrate_knowledge_extraction(client)
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())