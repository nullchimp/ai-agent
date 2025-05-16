from typing import List
import asyncio

from core.rag.schema import DocumentChunk, Vector
from core.azureopenai.client import Client

class EmbeddingService:
    def __init__(
        self,
        client: Client,
    ):
        self._client = client
        
    def get_index_config(self) -> dict:
        raise NotImplementedError("Subclasses should implement this method")

    async def get_embedding(self, text: str) -> List[float]:
        return await self._make_embedding_request(text)

    async def process_chunk(
        self,
        chunk: DocumentChunk,
        callback: callable = None
    ) -> None:
        """Process a single chunk: generate embedding and store in vector DB"""
        try:
            embedding = await self._make_embedding_request(chunk.content)
        except Exception as e:
            raise ValueError(f"Failed to process chunk {chunk.id}: {e}")

        vector = Vector(
            chunk_id=chunk.id,
            vector_store_id=None,
            embedding=embedding
        )

        if callback:
            callback(vector)
    
    async def process_chunks(
        self,
        chunks: List[DocumentChunk],
        callback: callable = None
    ) -> None:
        """Process multiple chunks in batches"""

        batch_size = 5  # Can be adjusted based on needs
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i+batch_size]
            tasks = [self.process_chunk(chunk, callback) for chunk in batch]
            await asyncio.gather(*tasks)
    
    async def search_similar(
        self,
        text: str,
        limit: int = 5
    ) -> List[dict]:
        """Search for similar chunks using text"""

        query_vector = await self._make_embedding_request(text)
        return await self._vector_store.search(query_vector, limit)
    
    async def _make_embedding_request(self, text: str) -> List[float]:
        response = await self._client.make_embeddings_request(input=text)

        # Extract embedding from response
        if response and "data" in response and len(response["data"]) > 0:
            return response["data"][0]["embedding"]
        
        raise ValueError("Failed to get embedding from Azure OpenAI")
    
from .text_embedding_3_small import TextEmbedding3Small