import os
from dotenv import load_dotenv
# Force reload of environment variables to avoid cached data
load_dotenv(override=True)

import asyncio
from core.azureopenai.client import Client
from core.rag.embedding_service import EmbeddingService


async def get_embeddings_example():
    # Get API key from environment variable
    api_key = os.environ.get("AZURE_OPENAI_API_KEY")
    if not api_key:
        raise ValueError("Missing AZURE_OPENAI_API_KEY environment variable")
    
    embedding_service = EmbeddingService(Client(api_key=api_key))
    
    # Get embeddings
    texts_to_embed = [
        "This is a test sentence.",
        "Another test sentence for embedding.",
        "Yet another sentence to test the embedding service.",
        "This is a different sentence to check the embedding.",
        "Final test sentence for the embedding service."
    ]
    embeddings = await embedding_service.get_embeddings(texts_to_embed)
    
    print(f"Number of embeddings: {len(embeddings)}")
    for e in embeddings:
        print(f"First 3/{len(e)} values: {e[:3]}...")
    
    return embeddings


if __name__ == "__main__":
    asyncio.run(get_embeddings_example())