from typing import List
import asyncio

from core.azureopenai.client import Client

class EmbeddingService:
    def __init__(
        self,
        client: Client,
        use_local_fallback: bool = True
    ):
        self._client = client
        self.local_model = None
        
        if use_local_fallback:
            try:
                from sentence_transformers import SentenceTransformer
                self.local_model = SentenceTransformer("all-MiniLM-L6-v2")
            except ImportError:
                self.local_model = None
    
    async def get_embedding(
        self,
        text: str,
        use_openai: bool = True
    ) -> List[float]:
        if use_openai:
            try:
                response = await self._make_openai_embedding_request(text)
                return response
            except Exception as e:
                if not self.local_model:
                    raise e
                # Fall back to local model

        # Use local model if OpenAI failed or if use_openai=False
        if self.local_model:
            result = self.local_model.encode(text)
            # Handle both numpy arrays and lists
            return result.tolist() if hasattr(result, 'tolist') else result
        
        raise ValueError("No embedding model available")
    
    async def get_embeddings(
        self,
        texts: List[str],
        use_openai: bool = True
    ) -> List[List[float]]:
        if use_openai:
            try:
                embeddings = []
                # Process in batches to avoid API limits
                batch_size = 5  # Can be adjusted based on needs
                for i in range(0, len(texts), batch_size):
                    batch = texts[i:i+batch_size]
                    tasks = [self._make_openai_embedding_request(text) for text in batch]
                    batch_embeddings = await asyncio.gather(*tasks)
                    embeddings.extend(batch_embeddings)
                return embeddings
            except Exception as e:
                if not self.local_model:
                    raise e
                # Fall back to local model

        # Use local model
        if self.local_model:
            result = self.local_model.encode(texts)
            # Handle both numpy arrays and lists
            return result.tolist() if hasattr(result, 'tolist') else result
        
        raise ValueError("No embedding model available")
    
    async def _make_openai_embedding_request(self, text: str) -> List[float]:
        response = await self._client.make_embeddings_request(input=text)
        
        # Extract embedding from response
        if response and "data" in response and len(response["data"]) > 0:
            return response["data"][0]["embedding"]
        
        raise ValueError("Failed to get embedding from Azure OpenAI")