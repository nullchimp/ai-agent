from typing import List
import asyncio

from core.azureopenai.client import Client

class EmbeddingService:
    def __init__(
        self,
        client: Client
    ):
        self._client = client
    
    async def get_embedding(
        self,
        text: str
    ) -> List[float]:
        try:
            return await self._make_openai_embedding_request(text)
        except Exception as e:
            raise e
    
    async def get_embeddings(
        self,
        texts: List[str]
    ) -> List[List[float]]:
        embeddings = []

        # Process in batches to avoid API limits
        batch_size = 5  # Can be adjusted based on needs
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            tasks = [self.get_embedding(text) for text in batch]
            batch_embeddings = await asyncio.gather(*tasks)
            embeddings.extend(batch_embeddings)

        return embeddings
    
    async def _make_openai_embedding_request(self, text: str) -> List[float]:
        response = await self._client.make_embeddings_request(input=text)

        # Extract embedding from response
        if response and "data" in response and len(response["data"]) > 0:
            return response["data"][0]["embedding"]
        
        raise ValueError("Failed to get embedding from Azure OpenAI")