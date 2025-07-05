from dotenv import load_dotenv
# Force reload of environment variables to avoid cached data
load_dotenv(override=True)

from libs.dataloader.document import DocumentLoader
from core.rag.embedder import TextEmbedding3Small
from core.db.knowledge_base import (
    create_vector_store,
    create_source,
    create_document,
    create_chunk,
    create_vector,
)

from loader_config import DOC_LOADER_CONFIGS

import asyncio
import os

api_key = os.environ.get("AZURE_OPENAI_API_KEY")
if not api_key:
    raise ValueError(f"AZURE_OPENAI_API_KEY environment variable is required")

embedder = TextEmbedding3Small()

vector_store = create_vector_store(
    **embedder.get_metadata()
)

def store(source, doc, chunks, vectors):
    create_source(source)
    create_document(doc)
    for chunk in chunks:
        create_chunk(chunk)

    for vector in vectors:
        vector.vector_store_id = vector_store.id
        create_vector(vector)

async def main():
    for config in DOC_LOADER_CONFIGS:
        loader = DocumentLoader(config.path, config.file_extensions or ['.md'])
        for source, doc, chunks in loader.load_data():
            vectors = []
            await embedder.process_chunks(chunks, callback=lambda v: vectors.append(v))
            if config.uri_replacement:
                old_pattern, new_pattern = config.uri_replacement
                source.uri = f"{source.uri.replace(old_pattern, new_pattern)}"
            store(source, doc, chunks, vectors)

asyncio.run(main())