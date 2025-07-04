from typing import List
import asyncio

from core.rag.schema import DocumentChunk, Vector
from core.llm.client import *

class EmbeddingService:
    def __init__(
        self
    ):
        self._client = EmbeddingsClient()
        
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
            raise ValueError(f"Failed to get embedding: {str(e)}")

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
    
    async def _make_embedding_request(self, text: str, retry = 3) -> List[float]:
        try:
            response = await self._client.make_request([text])
            
            # Extract embedding from response
            if response and "data" in response and len(response["data"]):
                return response["data"][0]["embedding"]
            
            raise ValueError("Failed to get embedding from Azure OpenAI")
        except Exception as e:
            if retry <= 0:
                raise ValueError(f"Failed to get embedding after retries: {str(e)}")

            await asyncio.sleep(5) # Wait for 5 seconds before retrying
            if "429" in str(e):
                await asyncio.sleep(55) # Wait for a total of 1 minute before retrying
            
            return await self._make_embedding_request(text, retry=retry-1)
    
from core.rag.embedder.text_embedding_3_small import TextEmbedding3Small