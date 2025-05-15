from dotenv import load_dotenv
# Force reload of environment variables to avoid cached data
load_dotenv(override=True)

from core.azureopenai.client import Client
from core.rag.loader import DocumentLoader
from core.rag.embedder import EmbeddingService
from core import complex_handler

import asyncio
import os
import json

async def main ():
    api_key = os.environ.get("AZURE_OPENAI_API_KEY")
    if not api_key:
        raise ValueError(f"AZURE_OPENAI_API_KEY environment variable is required")
    
    client = Client(api_key=api_key)
    loader = DocumentLoader()
    embedder = EmbeddingService(client)

    embedded_chunks = []
    for doc, chunks in loader.load_document_chunks("data"):
        await embedder.get_embeddings(chunks, callback=lambda chunk: embedded_chunks.append(chunk))
    
    print(json.dumps(embedded_chunks, indent=2, default=complex_handler))
    print("")

asyncio.run(main())