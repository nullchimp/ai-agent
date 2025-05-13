import os
import sys
import asyncio
from dotenv import load_dotenv
from datetime import datetime
# Force reload of environment variables to avoid cached data
load_dotenv(override=True)

# Add parent directory to path to make imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.azureopenai.client import Client
from core.rag.embedding_service import EmbeddingService
from core.rag.graph_client import MemGraphClient
from core.rag.indexer import Indexer
from core.rag.retriever import Retriever

async def rag_example():
    # Get API key from environment variables
    azure_api_key = os.environ.get("AZURE_OPENAI_API_KEY")
    if not azure_api_key:
        raise ValueError("Missing AZURE_OPENAI_API_KEY environment variable")
    
    # Set up Memgraph connection using the correct environment variables
    memgraph_uri = os.environ.get("MEMGRAPH_URI", "bolt://localhost:7687")
    memgraph_username = os.environ.get("MEMGRAPH_USERNAME", "neo4j")
    memgraph_password = os.environ.get("MEMGRAPH_PASSWORD", "aiagentpassword")
    
    # Initialize clients
    print("Initializing clients...")
    openai_client = Client(api_key=azure_api_key)
    embedding_service = EmbeddingService(openai_client)
    graph_client = MemGraphClient(memgraph_uri, memgraph_username, memgraph_password)
    
    # Initialize indexer and retriever
    indexer = Indexer(graph_client, embedding_service)
    retriever = Retriever(graph_client, embedding_service)
    
    try:
        # Create vector indices if they don't exist
        print("Setting up vector indices...")
        await graph_client.create_vector_index()
        
        # Index the README.md and some Python files
        print("\nIndexing project files...")
        
        # Index README.md
        readme_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "README.md"))
        if os.path.exists(readme_path):
            print(f"Indexing {readme_path}...")
            await indexer.index_file(readme_path, title="AI Agent README")
        
        # Index current script
        current_script_path = os.path.abspath(__file__)
        print(f"Indexing {current_script_path}...")
        await indexer.index_file(current_script_path, title="RAG Example Script")
        
        # Index agent.py
        agent_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src", "agent.py"))
        if os.path.exists(agent_path):
            print(f"Indexing {agent_path}...")
            await indexer.index_file(agent_path, title="Agent Implementation")
        
        # Index RAG-Integration.md ADR document
        adr_path = os.path.abspath(os.path.join(
            os.path.dirname(__file__), 
            "..", 
            "docs", 
            "ADRs", 
            "RAG-Integration.md"
        ))
        if os.path.exists(adr_path):
            print(f"Indexing {adr_path}...")
            await indexer.index_file(adr_path, title="RAG Integration ADR")
        
        # Execute some searches
        print("\nPerforming semantic searches...")
        
        # Search 1: General project query
        query1 = "What is AI Agent and what does it do?"
        print(f"\nQuery: {query1}")
        results1 = await retriever.search_documents(query1, limit=3)
        print(f"Found {len(results1)} results:")
        for i, result in enumerate(results1):
            print(f"  {i+1}. {result['title']} (Score: {result['score']:.4f})")
            print(f"     Path: {result['path']}")
            print(f"     Content snippet: {result['content'][:100]}...")
        
        # Search 2: Technical implementation query
        query2 = "How does the RAG system work with Neo4j?"
        print(f"\nQuery: {query2}")
        results2 = await retriever.search_documents(query2, limit=3)
        print(f"Found {len(results2)} results:")
        for i, result in enumerate(results2):
            print(f"  {i+1}. {result['title']} (Score: {result['score']:.4f})")
            print(f"     Path: {result['path']}")
            print(f"     Content snippet: {result['content'][:100]}...")
        
        # Search 3: Code-specific query
        query3 = "How are embeddings generated in this project?"
        print(f"\nQuery: {query3}")
        results3 = await retriever.search_documents(query3, limit=3)
        print(f"Found {len(results3)} results:")
        for i, result in enumerate(results3):
            print(f"  {i+1}. {result['title']} (Score: {result['score']:.4f})")
            print(f"     Path: {result['path']}")
            print(f"     Content snippet: {result['content'][:100]}...")
        
        # Demo conversation context retrieval
        print("\nSimulating conversation context retrieval...")
        conversation_id = await graph_client.create_conversation("Example Conversation")
        
        # Use current datetime instead of float timestamp
        current_time = datetime.now()
        message_id = await graph_client.add_message(
            conversation_id=conversation_id,
            content="Tell me about the retrieval system in this project.",
            role="user",
            timestamp=current_time
        )
        
        context = await retriever.get_conversation_context(
            query="How does the retriever work with embeddings?",
            conversation_id=conversation_id,
            message_id=message_id
        )
        
        print(f"Retrieved {len(context['relevant_documents'])} relevant documents")
        print(f"Retrieved {len(context['relevant_messages'])} related conversation messages")
        
        # Format the context for use in a prompt
        formatted_context = retriever.format_retrieved_context(
            context['relevant_documents'], 
            max_tokens=500
        )
        
        print("\nFormatted context preview:")
        print(formatted_context[:300] + "...")
        
        # Demonstrate source node relationships
        print("\nDemonstrating Source node relationships...")
        query = """
        MATCH (d:Document)-[:SOURCED_FROM]->(s:Source)
        RETURN d.path AS document_path, s.path AS source_path
        LIMIT 5
        """
        source_results = await graph_client.run_query(query)
        
        print("Documents and their source nodes:")
        for result in source_results:
            print(f"Document: {result['document_path']}")
            print(f"Source: {result['source_path']}\n")
        
        # Find a specific document and its source
        if len(results1) > 0:
            example_doc_path = results1[0]['path']
            query = """
            MATCH (d:Document {path: $path})-[:SOURCED_FROM]->(s:Source)
            RETURN d.path AS document_path, d.title AS document_title, s.path AS source_path
            """
            doc_source_result = await graph_client.run_query(query, {"path": example_doc_path})
            
            if doc_source_result:
                print(f"\nExample document '{example_doc_path}' Source relationship:")
                print(f"Document: {doc_source_result[0]['document_title']} ({doc_source_result[0]['document_path']})")
                print(f"Source: {doc_source_result[0]['source_path']}")
                
                # Show that we can also get documents from a source
                source_path = doc_source_result[0]['source_path']
                query = """
                MATCH (s:Source {path: $path})<-[:SOURCED_FROM]-(d:Document)
                RETURN d.path AS document_path, d.title AS document_title
                """
                source_docs_result = await graph_client.run_query(query, {"path": source_path})
                
                if source_docs_result:
                    print(f"\nDocuments with source '{source_path}':")
                    for doc in source_docs_result:
                        print(f"- {doc['document_title']} ({doc['document_path']})")
        
        return context
        
    finally:
        # Close the Neo4j connection
        await graph_client.close()
        print("\nCleanup complete.")


if __name__ == "__main__":
    asyncio.run(rag_example())