# RAG System: Edge and Relationship Structure

## Overview

This document details the relationships in our graph-based RAG (Retrieval-Augmented Generation) system. The relationship structure provides contextual information retrieval beyond simple vector similarity by modeling connections between documents, chunks, sources, and vectors.

## Core Relationship Types

The graph database uses these fundamental relationship types:

| Relationship | Direction | Description |
|--------------|-----------|-------------|
| `[:CHUNK_OF]` | DocumentChunk → Document | Connects a text chunk to its parent document |
| `[:SOURCED_FROM]` | Document → Source | Links a document to its origin source |
| `[:STORED_IN]` | Vector → VectorStore | Associates vectors with their storage system |
| `[:EMBEDDING_OF]` | Vector → DocumentChunk | Links vector embeddings to their document chunks |
| `[:FOLLOWS]` | Interaction → Interaction | Creates conversational thread chronology |
| `[:REFERENCES]` | Document → Source | Document refers to an external source |

## Internal Implementation

The relationship structure is defined in the schema and enforced through the graph client:

```python
class EdgeType(Enum):
    CHUNK_OF = "CHUNK_OF"          # DocumentChunk ➜ Document
    FOLLOWS = "FOLLOWS"            # Interaction ➜ Interaction
    SOURCED_FROM = "SOURCED_FROM"  # Document ➜ Source
    STORED_IN = "STORED_IN"        # Vector ➜ VectorStore
    EMBEDDING_OF = "EMBEDDING_OF"  # Vector ➜ DocumentChunk
    REFERENCES = "REFERENCES"      # Document ➜ Source
```

## Relationship Creation Mechanisms

### Document Processing Pipeline

When documents are processed through the RAG system:

```
+---------------+     +---------------+     +---------------+     +---------------+
|               |     |               |     |               |     |               |
| Content Load  |---->| Text Splitting|---->| Embedding     |---->| Relationship  |
|               |     |               |     | Generation    |     | Establishment |
+---------------+     +---------------+     +---------------+     +---------------+
```

1. **Source Creation**: Register content origin
   ```python
   # Create source node based on content type
   source = Source(name=domain, type="website", uri=url)
   db.create_source(source)
   ```

2. **Document Registration**: Store full document content
   ```python
   # Create document with reference to source
   document = Document(path=path, content=content, source_id=source.id)
   db.create_document(document)
   ```

3. **Chunk Generation**: Split document into semantic units
   ```python
   # Process document into chunks
   nodes = splitter.get_nodes_from_documents([doc])
   for idx, node in enumerate(nodes):
       chunk = DocumentChunk(
           path=path,
           content=node.text,
           parent_id=document.id,
           chunk_index=idx
       )
       db.create_chunk(chunk)
   ```

4. **Vector Embedding**: Generate and store embeddings
   ```python
   # Create embeddings for chunks
   vectors = []
   await embedder.process_chunks(chunks, callback=lambda v: vectors.append(v))
   for vector in vectors:
       vector.vector_store_id = vector_store.id
       db.create_vector(vector)
   ```

### Relationship Creation

Relationships are established during entity creation:

```python
def create_chunk(self, chunk: DocumentChunk) -> str:
    self._execute(*chunk.create())
    
    if not chunk.parent_id:
        raise ValueError("DocumentChunk must have a parent_id")
    
    # Create CHUNK_OF relationship from chunk to document
    self._execute(*chunk.link(
        EdgeType.CHUNK_OF,
        Document.label(),
        chunk.parent_id,
    ))
```

## Implementation in the Node Class

The base `Node` class provides methods for link creation:

```python
def link(
    self,
    edge: EdgeType,
    nodeType: str,
    to_id: str,
) -> None:
    label = self.__class__.__name__.upper()
    q = (
        f"MATCH (a:`{label}` {{id: $lid}}), "
        f"(b:`{nodeType}` {{id: $rid}}) "
        f"MERGE (a)-[r:`{edge.value}`]->(b)"
    )
    return [q, {"lid": str(self.id), "rid": str(to_id)}]
```

## Vector Search Operations

The relationship structure enables efficient vector search:

```python
def search_chunks(
    self,
    query_vector: Sequence[float],
    k: int = 5,
    index_name: str = "vector_embedding_index"
) -> List[Dict[str, Any]]:
    # First, search for matching vectors
    vector_results = self.vector_search(index_name, query_vector, k)
    
    # For each vector result, fetch the associated chunk
    results = []
    for result in vector_results:
        vector_node = result["node"]
        chunk_id = vector_node.get("chunk_id")
        
        if chunk_id:
            chunk = self.get_chunk_by_id(chunk_id)
            if chunk:
                results.append({
                    "chunk": chunk,
                    "vector": vector_node,
                    "distance": result["distance"],
                    "similarity": result["similarity"]
                })
                
    return results
```

## Web Content Relationships

For web content, specialized relationship handling occurs:

```python
# Create document with references to linked pages
document = Document(
    path=display_url,
    content=content,
    title=title,
    source_id=source.id,
    reference_ids=[hashlib.sha256(url.encode()).hexdigest()[:16] for url in new_urls]
)
```

## Technical Implementation Notes

### Graph Database Connection

The `MemGraphClient` class provides the interface to Memgraph:

```python
def __init__(
    self,
    host: str = "127.0.0.1",
    port: int = 7687,
    username: str | None = None,
    password: str | None = None,
    **kwargs,
) -> None:
    # Remove bolt:// prefix if present in host
    if host.startswith("bolt://"):
        host = host.replace("bolt://", "")
        
    # Handle localhost -> 127.0.0.1 conversion (more reliable)
    if host == "localhost":
        host = "127.0.0.1"
        
    try:
        print(f"Connecting to Memgraph at {host}:{port}")
        self._conn = mgclient.connect(
            host=host,
            port=port,
            username=username,
            password=password,
            **kwargs,
        )
        self._conn.autocommit = True
        self._cur = self._conn.cursor()
```

### Vector Indexing

Vector searches utilize Memgraph's vector index capability:

```python
def create_vector_store(
    self,
    **kwargs: Any
) -> VectorStore:
    # Create the actual vector index
    q = (
        f"CREATE VECTOR INDEX {str(kwargs['index_name'])} "
        f"ON :`{Vector.label()}`({kwargs['property_name']}) "
        f"WITH CONFIG {{"
        f' "dimension": {kwargs["dimension"]}, '
        f' "capacity": {kwargs["capacity"]}, '
        f' "metric": "{kwargs["metric"]}", '
        f' "resize_coefficient": {kwargs["resize_coefficient"]}'
        f" }};"
    )
```

## Further Enhancements

Potential extensions to the relationship model:

1. **Temporal Relationships**: Track document changes over time
2. **User Interaction Tracking**: Record user views and relevance feedback
3. **Concept Extraction**: Identify and link key concepts across documents
4. **Multi-hop Navigation**: Enable knowledge discovery across multiple relationships
5. **Conversation Threading**: Link interactions in a conversational context

As conversations progress, the system builds a graph of messages and referenced documents:

1. Each message is linked to its conversation with a `[:PART_OF]` relationship
2. When documents are referenced in responses, a `[:REFERENCES]` relationship is created
3. Concepts mentioned in messages create `[:MENTIONS]` relationships

```python
async def add_message_with_references(
    conversation_id: str, 
    content: str, 
    role: str,
    document_ids: list[str] = None
) -> str:
    # Create message node
    message_id = await client.add_message(
        conversation_id=conversation_id,
        content=content,
        role=role
    )
    
    # If the message references documents, add those relationships
    if document_ids:
        for doc_id in document_ids:
            await client.create_relationship(
                from_id=message_id, 
                to_id=doc_id, 
                relationship_type="REFERENCES"
            )
    
    # Extract concepts from message and create MENTIONS relationships
    concepts = concept_extractor.extract_concepts(content)
    for concept in concepts:
        concept_id = await client.create_or_get_concept(name=concept.name)
        await client.create_relationship(
            from_id=message_id, 
            to_id=concept_id, 
            relationship_type="MENTIONS"
        )
    
    return message_id
```

### 4. User Interaction Tracking

The system tracks how users interact with documents to build personalized knowledge profiles:

1. When a user views a document, a `[:VIEWED]` relationship is created with metadata
2. The relationship can include properties like view_count, last_viewed_at, and relevance_score
3. User interactions inform future recommendations and search result ranking

```python
async def track_user_viewed_document(
    user_id: str, 
    document_id: str,
    timestamp: datetime = None
) -> None:
    # Check if relationship already exists
    existing = await client.get_relationship(
        from_id=user_id, 
        to_id=document_id, 
        relationship_type="VIEWED"
    )
    
    if existing:
        # Update existing relationship
        view_count = existing.get("view_count", 0) + 1
        await client.update_relationship(
            from_id=user_id,
            to_id=document_id,
            relationship_type="VIEWED",
            properties={
                "view_count": view_count,
                "last_viewed_at": timestamp or datetime.now()
            }
        )
    else:
        # Create new relationship
        await client.create_relationship(
            from_id=user_id,
            to_id=document_id,
            relationship_type="VIEWED",
            properties={
                "view_count": 1,
                "first_viewed_at": timestamp or datetime.now(),
                "last_viewed_at": timestamp or datetime.now()
            }
        )
```

## Leveraging Relationships for Enhanced Retrieval

### Context-Aware Search

The system uses the graph structure to enhance retrieval quality through:

1. **Traversal-Based Retrieval**: Following relationships to find related documents
2. **Conversation-Aware Search**: Using conversation history to customize search results
3. **Personalized Ranking**: Incorporating user interaction patterns

Example Cypher query for conversation-aware search:

```cypher
// Find documents related to the current query that are connected to the conversation
MATCH (q:Query {id: $query_id})
MATCH (c:Conversation {id: $conversation_id})
MATCH (c)-[:CONTAINS]->(m:Message)-[:MENTIONS]->(concept:Concept)
MATCH (d:Document)-[:EXPLAINS]->(concept)
WITH d, count(distinct concept) AS conceptRelevance

// Combine with vector similarity
MATCH (q)-[s:SIMILARITY]->(d)
WITH d, s.score AS vectorSimilarity, conceptRelevance

// Calculate combined relevance score
RETURN d.id, d.path, 
       (vectorSimilarity * 0.7) + (conceptRelevance * 0.3) AS relevance
ORDER BY relevance DESC
LIMIT 5
```

### Multi-Hop Knowledge Discovery

The system can traverse multiple relationship hops to discover knowledge that might not be immediately apparent:

```cypher
// Find documents that explain concepts related to concepts mentioned in user questions
MATCH (u:User {id: $user_id})-[:CREATED]->(m:Message {role: "user"})
MATCH (m)-[:MENTIONS]->(c1:Concept)
MATCH (c1)-[:RELATED_TO*1..2]->(c2:Concept)
MATCH (d:Document)-[:EXPLAINS]->(c2)
WHERE NOT (u)-[:VIEWED]->(d)
RETURN d.id, d.path, count(distinct c2) AS relevance
ORDER BY relevance DESC
LIMIT 3
```

## Implementation Details

### Node Schema

The system uses typed nodes with specific properties:

```python
class DocumentNode:
    id: str  # UUID
    path: str  # Path to the document
    title: str  # Document title
    created_at: datetime  # Timestamp
    updated_at: datetime  # Timestamp
    content_type: str  # MIME type

class ChunkNode:
    id: str  # UUID
    content: str  # Text content
    embedding: list[float]  # Vector embedding
    created_at: datetime  # Timestamp

class ConceptNode:
    id: str  # UUID
    name: str  # Concept name
    description: str  # Optional description
```

### Relationship Properties

Relationships can carry properties that provide additional context:

```python
class ExplainsRelationship:
    relevance_score: float  # How well the document explains the concept
    explanation_type: str  # "definition", "example", "application", etc.

class ViewedRelationship:
    view_count: int  # Number of times viewed
    first_viewed_at: datetime  # First view timestamp
    last_viewed_at: datetime  # Most recent view timestamp
    duration: int  # Optional: time spent viewing (seconds)
```

## Technical Considerations

### Performance Optimization

1. **Indexing Strategy**: The system creates graph indexes for frequently traversed relationships
2. **Caching**: High-frequency patterns are cached to reduce database load
3. **Batch Operations**: Relationships are created in batches when processing multiple documents

### Data Quality Management

1. **Confidence Scores**: Relationship creation includes confidence metrics
2. **Periodic Evaluation**: Relationships are periodically evaluated for relevance
3. **Pruning**: Low-value relationships may be pruned to maintain graph quality

## Extension Points

The relationship architecture is designed to be extensible:

1. **Custom Relationship Types**: Domain-specific relationships can be added
2. **Pluggable Extractors**: New concept extraction methods can be integrated
3. **Relationship Inference**: ML models can be added to infer relationships from content

## Conclusion

The edge and relationship building architecture is the foundation of the RAG system's contextual understanding. By modeling connections between concepts, documents, conversations, and users, the system can provide highly relevant information retrieval beyond what vector similarity alone can achieve.