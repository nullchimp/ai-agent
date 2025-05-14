# RAG System: Edge and Relationship Building Architecture

## Overview

This document explains how the RAG (Retrieval Augmented Generation) system builds and maintains the edge relationships in the underlying graph database. The relationship structure is central to the system's ability to provide contextual, relevant information retrieval beyond simple vector similarity.

## Relationship Types

The RAG system uses the following core relationship types:

| Relationship | Direction | Description |
|--------------|-----------|-------------|
| `[:CHUNK_OF]` | Chunk → Document | Connects a text chunk to its parent document |
| `[:EXPLAINS]` | Document → Concept | Document explains or defines a concept |
| `[:BELONGS_TO]` | Document → Topic | Document belongs to a broader topic |
| `[:RELATED_TO]` | Concept ↔ Concept | Bidirectional relationship between related concepts |
| `[:REFERENCES]` | Message → Document | Message in a conversation references a document |
| `[:PART_OF]` | Message → Conversation | Message belongs to a conversation |
| `[:VIEWED]` | User → Document | User has viewed a document |
| `[:CREATED]` | User → Message | User created a message |
| `[:MENTIONS]` | Message → Concept | Message mentions a concept |

## Relationship Creation Mechanisms

### 1. Document Processing Pipeline

Relationships are established during the document indexing process through the following pipeline:

```
+---------------+     +---------------+     +---------------+     +---------------+
|               |     |               |     |               |     |               |
| Document Load |---->| Text Splitting|---->| Embedding     |---->| Relationship  |
|               |     |               |     | Generation    |     | Establishment |
+---------------+     +---------------+     +---------------+     +---------------+
```

#### Document Loading and Chunking

When a document is loaded into the system:

1. The document is registered as a node with metadata (path, title, creation date)
2. The document is split into semantic chunks via the `TextSplitter`
3. Each chunk is stored as a separate node
4. A `[:CHUNK_OF]` relationship is created from each chunk to its parent document

```python
async def index_document(doc_path: str) -> str:
    # Create document node
    doc_id = await client.create_document(path=doc_path)
    
    # Load and split document
    content = loader.load_document(doc_path)
    chunks = splitter.split_text(content)
    
    # Create chunks and relationships
    for chunk in chunks:
        chunk_id = await client.create_chunk(content=chunk, doc_id=doc_id)
        await client.create_relationship(
            from_id=chunk_id, 
            to_id=doc_id, 
            relationship_type="CHUNK_OF"
        )
    
    return doc_id
```

### 2. Concept and Topic Extraction

The system extracts concepts and topics from documents using:

1. **Named Entity Recognition**: Identifies entities like people, organizations, and technologies
2. **Keyword Extraction**: Identifies significant terms using TF-IDF or similar algorithms
3. **Topic Modeling**: Uses techniques like LDA to identify broad themes

For each identified concept or topic:

```python
async def link_document_to_concepts(doc_id: str, text: str) -> None:
    # Extract concepts from text
    concepts = concept_extractor.extract_concepts(text)
    
    for concept in concepts:
        # Create or retrieve concept node
        concept_id = await client.create_or_get_concept(name=concept.name)
        
        # Link document to concept
        await client.link_document_explains_concept(
            document_id=doc_id,
            concept_id=concept_id
        )
        
        # Create relationships between concepts that co-occur
        for other_concept in concepts:
            if other_concept != concept:
                other_id = await client.create_or_get_concept(name=other_concept.name)
                await client.link_related_concepts(concept_id, other_id)
```

### 3. Conversation Context Tracking

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