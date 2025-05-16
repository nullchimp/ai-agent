from dotenv import load_dotenv
# Force reload of environment variables to avoid cached data
load_dotenv(override=True)

from core.azureopenai.client import Client
from core.rag.embedder import TextEmbedding3Small
from core.rag.graph_client import MemGraphClient

from core.rag.loader.web_loader import WebLoader

from core import chatutil, graceful_exit, mainloop, pretty_print

import asyncio
import os

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
loader = WebLoader("http://localhost:4000/en/copilot/managing-copilot/monitoring-usage-and-entitlements/about-premium-requests")
embedder = TextEmbedding3Small(client)

vector_store = db.create_vector_store(
    **embedder.get_metadata()
)

def store(source, doc, chunks, vectors):
    db.create_source(source)
    db.create_document(doc)
    for chunk in chunks:
        db.create_chunk(chunk)

    for vector in vectors:
        vector.vector_store_id = vector_store.id
        db.create_vector(vector)

async def main():
    max_test = 100
    docs = []
    for source, doc, chunks in loader.load_data():
        vectors = []
        await embedder.process_chunks(chunks, callback=lambda v: vectors.append(v))
        store(source, doc, chunks, vectors)

        max_test -= 1
        if max_test <= 0:
            break
    

if __name__ == "__main__":
    asyncio.run(main())