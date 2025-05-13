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
            # First index the file
            doc = await indexer.index_file(
                readme_path, 
                title="AI Agent README"
            )
            # Then create and link the resource
            if doc and "id" in doc:
                await graph_client.create_resource(
                    uri="https://github.com/nullchimp/ai-agent/blob/main/README.md",
                    type="documentation",
                    description="AI Agent README documentation"
                )
                await graph_client.link_document_to_resource(
                    doc["id"],
                    "https://github.com/nullchimp/ai-agent/blob/main/README.md",
                    "documentation"
                )
        
        # Index current script
        current_script_path = os.path.abspath(__file__)
        print(f"Indexing {current_script_path}...")
        # First index the file
        doc = await indexer.index_file(
            current_script_path, 
            title="RAG Example Script"
        )
        # Then create and link the resource
        if doc and "id" in doc:
            resource_uri = "file://" + current_script_path
            await graph_client.create_resource(
                uri=resource_uri,
                type="example_code",
                description="RAG Example Script"
            )
            await graph_client.link_document_to_resource(
                doc["id"],
                resource_uri,
                "example_code"
            )
        
        # Index agent.py
        agent_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src", "agent.py"))
        if os.path.exists(agent_path):
            print(f"Indexing {agent_path}...")
            # First index the file
            doc = await indexer.index_file(
                agent_path, 
                title="Agent Implementation"
            )
            # Then create and link the resource
            if doc and "id" in doc:
                resource_uri = "file://" + agent_path
                await graph_client.create_resource(
                    uri=resource_uri,
                    type="implementation",
                    description="Agent Implementation"
                )
                await graph_client.link_document_to_resource(
                    doc["id"],
                    resource_uri,
                    "implementation"
                )
        
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
            # First index the file
            doc = await indexer.index_file(
                adr_path, 
                title="RAG Integration ADR"
            )
            # Then create and link the resource
            if doc and "id" in doc:
                resource_uri = "file://" + adr_path
                await graph_client.create_resource(
                    uri=resource_uri,
                    type="architecture",
                    description="RAG Integration Architecture Decision Record"
                )
                await graph_client.link_document_to_resource(
                    doc["id"],
                    resource_uri,
                    "architecture"
                )
        
        # Create and link additional resources for the project
        print("\nCreating additional project resources...")
        await graph_client.create_resource(
            uri="https://platform.openai.com/docs/guides/embeddings", 
            type="api_documentation",
            description="OpenAI embeddings API documentation"
        )
        
        # Link API documentation to agent implementation
        doc = await graph_client.find_document(agent_path)
        if doc and "id" in doc:
            await graph_client.link_document_to_resource(
                doc["id"], 
                "https://platform.openai.com/docs/guides/embeddings",
                "api_documentation"
            )
            print("Linked agent implementation to OpenAI embeddings documentation")
        
        # Execute semantic searches with resources
        print("\nPerforming semantic searches...")
        
        # Search 1: General project query
        query1 = "What is AI Agent and what does it do?"
        print(f"\nQuery: {query1}")
        results1 = await retriever.search_documents(query1, limit=3)
        print(f"Found {len(results1)} results:")
        for i, result in enumerate(results1):
            print(f"  {i+1}. {result['title']} (Score: {result['score']:.4f})")
            print(f"     Path: {result['path']}")
            print(f"     Resource: {result.get('resource_uri', 'None')}")
            print(f"     Content snippet: {result['content'][:100]}...")
        
        # Search 2: Technical implementation query with resource awareness
        query2 = "How does the RAG system work with graph databases?"
        print(f"\nQuery: {query2}")
        results2 = await retriever.search_documents(query2, limit=3)
        print(f"Found {len(results2)} results:")
        for i, result in enumerate(results2):
            print(f"  {i+1}. {result['title']} (Score: {result['score']:.4f})")
            print(f"     Path: {result['path']}")
            print(f"     Resource type: {result.get('resource_type', 'Unknown')}")
            print(f"     Content snippet: {result['content'][:100]}...")
        
        # Search 3: Resource-specific query
        query3 = "Show me architecture documentation about embeddings"
        print(f"\nQuery: {query3}")
        # Change to use the standard search_documents method
        # We'll filter by resource type after the search
        results3 = await retriever.search_documents(query3, limit=5)
        
        # Filter results by resource type
        filtered_results = []
        resource_types = ["architecture", "documentation"]
        for result in results3:
            doc_id = result.get("document_id")
            if doc_id:
                # Check if document is linked to specified resource types
                query = """
                MATCH (d:Document {id: $doc_id})-[:REFERENCES]->(r:Resource)
                WHERE r.type IN $resource_types
                RETURN r.type as resource_type
                LIMIT 1
                """
                resource_result = await graph_client.run_query(
                    query, 
                    {"doc_id": doc_id, "resource_types": resource_types}
                )
                if resource_result:
                    result["resource_type"] = resource_result[0].get("resource_type")
                    filtered_results.append(result)
        
        print(f"Found {len(filtered_results)} results in architecture/documentation resources:")
        for i, result in enumerate(filtered_results):
            print(f"  {i+1}. {result['title']} (Score: {result['score']:.4f})")
            print(f"     Path: {result['path']}")
            print(f"     Resource type: {result.get('resource_type', 'Unknown')}")
            print(f"     Content snippet: {result['content'][:100]}...")
        
        # Demo conversation context retrieval with resources
        print("\nSimulating conversation context retrieval...")
        conversation_id = await graph_client.create_conversation("Example Conversation About Resources")
        
        # Use current datetime for message timestamp
        current_time = datetime.now()
        message_id = await graph_client.add_message(
            conversation_id=conversation_id,
            content="How can I organize resources by type in the graph database?",
            role="user",
            timestamp=current_time
        )
        
        context = await retriever.get_conversation_context(
            query="What are the different types of resources in the knowledge graph?",
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
        
        # Analyze resources in the graph
        print("\nAnalyzing resources in the knowledge graph...")
        
        # Get resource statistics by type
        query = """
        MATCH (r:Resource)
        RETURN r.type AS resource_type, COUNT(r) AS count
        ORDER BY count DESC
        """
        resource_stats = await graph_client.run_query(query)
        
        print("Resource statistics by type:")
        for stat in resource_stats:
            resource_type = stat["resource_type"] or "unspecified"
            print(f"  {resource_type}: {stat['count']} resources")
        
        # Find the most referenced resources
        query = """
        MATCH (d:Document)-[:REFERENCES]->(r:Resource)
        RETURN r.uri AS uri, r.type AS type, COUNT(d) AS references
        ORDER BY references DESC
        LIMIT 5
        """
        top_resources = await graph_client.run_query(query)
        
        print("\nTop referenced resources:")
        for res in top_resources:
            uri = res["uri"]
            res_type = res["type"] or "unspecified"
            print(f"  {uri} (Type: {res_type})")
            print(f"  Referenced by {res['references']} documents")
        
        # Group documents by resource type - fixing the query for MemGraph compatibility
        query = """
        MATCH (d:Document)-[:REFERENCES]->(r:Resource)
        WITH r.type AS type, COLLECT(d.title) AS documents
        RETURN type, documents
        ORDER BY SIZE(documents) DESC
        """
        grouped_docs = await graph_client.run_query(query)
        
        print("\nDocuments grouped by resource type:")
        for group in grouped_docs:
            res_type = group["type"] or "unspecified"
            docs = group["documents"]
            print(f"  {res_type} ({len(docs)} documents):")
            for i, doc in enumerate(docs[:3]):  # Show only first 3 for brevity
                print(f"    - {doc}")
            if len(docs) > 3:
                print(f"    - ... and {len(docs) - 3} more")
        
        # Demonstrate finding resources by URI pattern
        print("\nFinding resources by URI pattern...")
        query = """
        MATCH (r:Resource)
        WHERE r.uri CONTAINS $pattern
        RETURN r.uri AS uri, r.type AS type, r.description AS description
        """
        github_resources = await graph_client.run_query(query, {"pattern": "github"})
        
        print("GitHub-related resources:")
        for res in github_resources:
            print(f"  URI: {res['uri']}")
            print(f"  Type: {res['type']}")
            print(f"  Description: {res.get('description', 'No description')}\n")
        
        return context
        
    finally:
        # Close the connection
        await graph_client.close()
        print("\nCleanup complete.")


if __name__ == "__main__":
    asyncio.run(rag_example())