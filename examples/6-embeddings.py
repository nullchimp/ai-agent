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
    text_to_embed = "Your text to embed"
    embedding = await embedding_service.get_embedding(text_to_embed)
    
    print(f"Generated embedding with {len(embedding)} dimensions")
    print(f"First few values: {embedding[:5]}...")
    
    return embedding


if __name__ == "__main__":
    asyncio.run(get_embeddings_example())