import uuid
from src.core.rag.schema import DocumentChunk

from . import EmbeddingService

class TextEmbedding3Small(EmbeddingService):
    @property
    def model(self) -> str:
        return "text-embedding-3-small"

    def get_metadata(self) -> dict:
        return {
            "index_name": f"index_{self.model.replace('-', '_')}",
            "label": DocumentChunk.label(),
            "property_name": "embedding",
            "dimension": 1536,
            "model": self.model,
            "capacity": 4096,
            "metric": "cos",
            "resize_coefficient": 2
        }