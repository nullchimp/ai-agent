from dotenv import load_dotenv
# Force reload of environment variables to avoid cached data
load_dotenv(override=True)

from core.rag.embedder import TextEmbedding3Small
from libs.dataloader.web import WebLoader
from core.db.knowledge_base import (
    create_vector_store,
    create_source,
    create_document,
    create_chunk,
    create_vector,
)

from loader_config import WEB_LOADER_CONFIGS

import asyncio

embedder = TextEmbedding3Small()

vector_store = create_vector_store(
    **embedder.get_metadata()
)

def store(source, doc, chunks, vectors):
    print("### Storing data in Memgraph")
    print("Source:", source)
    print("Document:", doc)
    print("Chunks:", len(chunks))
    print("Vectors:", len(vectors))

    create_source(source)
    create_document(doc)
    for chunk in chunks:
        create_chunk(chunk)

    for vector in vectors:
        vector.vector_store_id = vector_store.id
        create_vector(vector)

    print("### Data stored successfully")

async def main():
    for config in WEB_LOADER_CONFIGS:
        loader = WebLoader(config.url)
        for source, doc, chunks in loader.load_data():
            vectors = []
            await embedder.process_chunks(chunks, callback=lambda v: vectors.append(v))
            if config.uri_replacement:
                old_pattern, new_pattern = config.uri_replacement
                source.uri = f"{source.uri.replace(old_pattern, new_pattern)}"
            store(source, doc, chunks, vectors)
    

if __name__ == "__main__":
    asyncio.run(main())