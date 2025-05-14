# Vector Embeddings Reference Guide

## Overview

Vector embeddings are numerical representations of data (text, images, audio) in high-dimensional space, where semantic relationships are preserved through vector operations. This reference describes key embedding types, creation methods, and applications in AI systems.

## Types of Embeddings

### Text Embeddings

| Model | Dimensions | Context Length | Strengths |
|-------|-----------|---------------|-----------|
| OpenAI Ada-002 | 1536 | 8191 tokens | Strong general-purpose semantic similarity |
| BERT Base | 768 | 512 tokens | Contextual word representations |
| Sentence-BERT | 384-768 | ~256 tokens | Optimized for sentence similarity tasks |
| MPNet | 768 | 512 tokens | Enhanced positional encoding |
| GTE-Large | 1024 | 512 tokens | Optimized for retrieval tasks |

### Image Embeddings

| Model | Dimensions | Input Size | Applications |
|-------|-----------|------------|--------------|
| ResNet-50 | 2048 | 224x224px | General image classification |
| CLIP | 512 | 224x224px | Cross-modal text-image similarity |
| DINOv2 | 768 | Variable | Self-supervised vision features |

## Mathematical Operations

### Cosine Similarity

The standard metric for comparing embedding similarity:

```
cosine_similarity(A, B) = (A · B) / (||A|| × ||B||)
```

Where:
- A · B is the dot product
- ||A|| and ||B|| are the L2 norms (magnitudes)

Values range from -1 (opposite) to 1 (identical), with 0 indicating orthogonality.

### Euclidean Distance

Alternative distance metric:

```
euclidean_distance(A, B) = √(Σ(Ai - Bi)²)
```

Smaller values indicate greater similarity.

## Dimensionality Reduction

For visualization and efficiency:

- **PCA (Principal Component Analysis)**: Linear technique that preserves global structure
- **t-SNE**: Non-linear technique that preserves local relationships
- **UMAP**: Balance between global and local structure preservation

## Storage and Indexing

### Vector Databases

| Database | Indexing Algorithm | Query Performance | Scaling |
|----------|-------------------|------------------|---------|
| Pinecone | HNSW / IVF | ~10-50ms at 10M scale | Managed horizontal |
| Weaviate | HNSW | ~20-100ms at 10M scale | Horizontal sharding |
| Milvus | IVF, HNSW, ANNOY | Configurable speed/recall tradeoff | Distributed architecture |
| Qdrant | HNSW | ~10-30ms at 1M scale | Node-based scaling |
| Memgraph | HNSW / Brute force | Graph-enhanced retrieval | Graph relationship traversal |

### Approximate Nearest Neighbor (ANN) Algorithms

- **HNSW (Hierarchical Navigable Small World)**: Multi-layered graph structure
- **IVF (Inverted File Index)**: Clustering-based approach
- **ANNOY**: Tree-based indexing with random projections
- **FAISS**: Facebook AI's library with GPU acceleration

## Best Practices

### Text Embedding Creation

1. **Preprocessing**: 
   - Normalize text (case, punctuation, whitespace)
   - Consider domain-specific tokenization

2. **Chunking Strategy**:
   - Semantic units (paragraphs, sections)
   - Fixed-size with overlap (e.g., 512 tokens with 50-100 token overlap)
   - Hierarchical chunks (document → section → paragraph)

3. **Metadata Integration**:
   - Store metadata alongside embeddings
   - Include source information, timestamps, and relevance signals

### Retrieval Enhancement

- **Hybrid search**: Combine vector search with keyword filtering
- **Reranking**: Two-stage retrieval with initial broad search followed by precise reranking
- **Query expansion**: Augment queries with related terms or concepts
- **Cross-encoder verification**: Use more expensive models to verify top candidates

## Implementation Code Example

```python
# Using SentenceTransformers
from sentence_transformers import SentenceTransformer
import numpy as np

# Load model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Create embeddings
documents = ["Document about machine learning", 
             "Article about natural language processing",
             "Paper discussing vector embeddings"]
embeddings = model.encode(documents)

# Calculate similarity
def cosine_similarity(v1, v2):
    dot_product = np.dot(v1, v2)
    norm_v1 = np.linalg.norm(v1)
    norm_v2 = np.linalg.norm(v2)
    return dot_product / (norm_v1 * norm_v2)

# Query example
query = "How do vector embeddings work?"
query_embedding = model.encode([query])[0]

# Find most similar document
similarities = [cosine_similarity(query_embedding, doc_emb) for doc_emb in embeddings]
most_similar_idx = np.argmax(similarities)
print(f"Most similar document: {documents[most_similar_idx]}")
```

## Recent Research Directions

- **Multi-modal embeddings**: Unified representations across text, image, audio
- **Sparse-dense hybrid embeddings**: Combining benefits of sparse and dense representations
- **Task-specific fine-tuning**: Adapting pre-trained embeddings for domain-specific applications
- **Efficient training methods**: Reducing computational resources needed for embedding creation

## References

1. Reimers, N., & Gurevych, I. (2019). Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks.
2. Karpukhin, V., et al. (2020). Dense Passage Retrieval for Open-Domain Question Answering.
3. Ni, J., et al. (2022). Large Dual Encoders Are Generalizable Retrievers.
4. Radford, A., et al. (2021). Learning Transferable Visual Models From Natural Language Supervision.