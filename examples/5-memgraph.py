from core.rag.schema import NodeLabel          # your real dataclass
from core.rag.embedder import EmbeddingService
from core.rag.graph_client import MemGraphClient

async def main():
    embedder = EmbeddingService()
    query = "How do I reset my password?"
    q_vec = embedder.get_embedding(query)

    with MemGraphClient() as mg:
        # one-off: ensure an index exists (once per DB)
        mg.create_vector_index(
            index_name="chunk_embedding_index",
            label=NodeLabel.CHUNK,
            property_name="embedding",
            dimension=len(q_vec),
        )

        results = mg.search_chunks(q_vec, k=8)
        for hit in results:
            print(hit["similarity"], hit["node"]["content"][:120])
