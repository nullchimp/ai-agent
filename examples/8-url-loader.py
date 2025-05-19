from dotenv import load_dotenv
# Force reload of environment variables to avoid cached data
load_dotenv(override=True)

from core.rag.embedder import TextEmbedding3Small
from core.rag.dbhandler.memgraph import MemGraphClient

from libs.dataloader.web import WebLoader

import asyncio
import os

db = MemGraphClient(
    host="localhost" or os.environ.get("MEMGRAPH_URI", "localhost"),
    port=int(os.environ.get("MEMGRAPH_PORT", 7687)),
    username=os.environ.get("MEMGRAPH_USERNAME", "memgraph"),
    password=os.environ.get("MEMGRAPH_PASSWORD", "memgraph"),
)
db.connect()

print("Connected to Memgraph", db.host, db.port)

loader = WebLoader("http://localhost:4000/en/enterprise-cloud@latest/copilot")
embedder = TextEmbedding3Small()

vector_store = db.create_vector_store(
    **embedder.get_metadata()
)

def store(source, doc, chunks, vectors):
    print("### Storing data in Memgraph")
    print("Source:", source)
    print("Document:", doc)
    print("Chunks:", len(chunks))
    print("Vectors:", len(vectors))

    db.create_source(source)
    db.create_document(doc)
    for chunk in chunks:
        db.create_chunk(chunk)

    for vector in vectors:
        vector.vector_store_id = vector_store.id
        db.create_vector(vector)

    print("### Data stored successfully")

async def main():
    for source, doc, chunks in loader.load_data():
        vectors = []
        await embedder.process_chunks(chunks, callback=lambda v: vectors.append(v))
        store(source, doc, chunks, vectors)

    db.close()
    

if __name__ == "__main__":
    asyncio.run(main())