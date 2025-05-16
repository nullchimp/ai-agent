from dotenv import load_dotenv
# Force reload of environment variables to avoid cached data
load_dotenv(override=True)

from core.azureopenai.client import Client
from core.rag.embedder import TextEmbedding3Small
from core.rag.graph_client import MemGraphClient

import asyncio
import os
import random

# Set up clients
api_key = os.environ.get("AZURE_OPENAI_API_KEY")
if not api_key:
    raise ValueError(f"AZURE_OPENAI_API_KEY environment variable is required")

db = MemGraphClient(
    host=os.environ.get("MEMGRAPH_URI", "localhost"),
    port=int(os.environ.get("MEMGRAPH_PORT", 7687)),
    username=os.environ.get("MEMGRAPH_USERNAME", "memgraph"),
    password=os.environ.get("MEMGRAPH_PASSWORD", "memgraph"),
)

client = Client(api_key=api_key)
embedder = TextEmbedding3Small(client)

async def test_vector_search():
    query_text = "Explain NLP to me in simple terms."
    print(f"Using query text (truncated): {query_text[:100]}...")

    # 6. Load a vector store to use for search
    vector_store = db.load_vector_store(model=embedder.model)
    if not vector_store:
        print(f"No vector store found for model {embedder.model}")
        return
    
    query_embedding = await embedder.get_embedding(query_text)
    
    print(f"Using vector store: {vector_store.id} (model: {vector_store.model})")
    
    # 7. Perform vector search
    index_name = vector_store.metadata.get("index_name", None)
    if not index_name:
        print("No index name found in vector store metadata")
        return
    search_results = db.search_chunks(
        query_vector=query_embedding,
        k=5,
        index_name=index_name
    )
    
    # 8. Display results
    print("\n----- Search Results -----")
    print(f"Query text: {query_text[:100]}...")
    print(f"Found {len(search_results)} results\n")
    
    for i, result in enumerate(search_results):
        chunk = result["chunk"]
        similarity = result["similarity"]
        print(f"Result {i+1} (similarity: {similarity:.4f}):")
        print(f"Chunk content (truncated): {chunk['content'][:150]}...")
        print("---")

async def main():
    print("Starting vector search test...")
    await test_vector_search()
    print("Test completed.")

if __name__ == "__main__":
    asyncio.run(main())