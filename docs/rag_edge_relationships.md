---
title: RAG Edge Relationships
description: Defines the relationships (edges) between different nodes in the RAG knowledge graph.
---

# RAG Graph Edge Relationships

This document outlines the types of nodes and the relationships (edges) between them within the Retrieval Augmented Generation (RAG) knowledge graph. The schema is primarily defined in `src/core/rag/schema.py`.

## Node Types

The core entities in our graph are:

*   **`DOCUMENT`**: Represents a full document, such as a file or a web page, containing content and metadata.
*   **`DOCUMENTCHUNK`**: Represents a segment of a `DOCUMENT`. These chunks are what get embedded and used for similarity searches. Content is stored in both the graph and the vector store.
*   **`INTERACTION`**: Represents a chat message (user or assistant) or a system-level interaction/event.
*   **`SOURCE`**: Represents the origin of a `DOCUMENT`, like a website URL, a file path, or an API endpoint.
*   **`VECTORSTORE`**: Represents an embedding storage system where vector embeddings are kept.
*   **`VECTOR`**: Represents the actual embedding vector for a `DOCUMENTCHUNK`.

## Edge Types (Relationships)

Relationships define how these nodes are connected:

*   **`CHUNK_OF`**: `DOCUMENTCHUNK` → `DOCUMENT`
    *   Indicates that a `DOCUMENTCHUNK` is a part of a larger `DOCUMENT`.
*   **`FOLLOWS`**: `INTERACTION` → `INTERACTION`
    *   Links `INTERACTION` nodes chronologically to maintain conversation history.
*   **`SOURCED_FROM`**: `DOCUMENT` → `SOURCE`
    *   Connects a `DOCUMENT` to its original `SOURCE`.
*   **`STORED_IN`**: `VECTOR` → `VECTORSTORE`
    *   Shows that a `VECTOR` embedding is managed by a specific `VECTORSTORE`.
*   **`EMBEDDING_OF`**: `VECTOR` → `DOCUMENTCHUNK`
    *   Links a `VECTOR` embedding to the `DOCUMENTCHUNK` it represents.
*   **`REFERENCES`**: `DOCUMENT` → `SOURCE`
    *   Indicates that a `DOCUMENT` makes reference to a `SOURCE` (e.g., a citation or link within the document content).

## Mermaid Diagram

```mermaid
graph TD
    subgraph "Document Processing"
        D[DOCUMENT]
        DC[DOCUMENTCHUNK]
        S[SOURCE]
        V[VECTOR]
        VS[VECTORSTORE]

        DC -- CHUNK_OF --> D
        D -- SOURCED_FROM --> S
        D -- REFERENCES --> S
        V -- EMBEDDING_OF --> DC
        V -- STORED_IN --> VS
    end

    subgraph "Interaction Flow"
        I1[INTERACTION]
        I2[INTERACTION]
        I3[INTERACTION]

        I2 -- FOLLOWS --> I1
        I3 -- FOLLOWS --> I2
    end

    %% Styling
    classDef node fill:#ECECFF,stroke:#9B9BFF,stroke-width:2px,color:#000
    classDef edgeLabel fill:#FFFFFF,color:#333,font-size:10px
    class D,DC,S,V,VS,I1,I2,I3 node

    linkStyle 0 stroke:#FFB6C1,stroke-width:2px;
    linkStyle 1 stroke:#ADD8E6,stroke-width:2px;
    linkStyle 2 stroke:#90EE90,stroke-width:2px;
    linkStyle 3 stroke:#FFD700,stroke-width:2px;
    linkStyle 4 stroke:#FFA07A,stroke-width:2px;
    linkStyle 5 stroke:#BA55D3,stroke-width:2px;
    linkStyle 6 stroke:#BA55D3,stroke-width:2px;
```

This schema allows for flexible querying of document origins, their content (via chunks and embeddings), and the history of interactions related to them.