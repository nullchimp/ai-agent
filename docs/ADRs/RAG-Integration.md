---
title: RAG Integration ADR
description: Decision to integrate a Retrieval Augmented Generation (RAG) system using Memgraph and a vector embedder.
status: accepted
date: 2024-07-15
---

# ADR: RAG Integration for Enhanced Contextual Understanding

**Status:** Accepted

**Date:** 2024-07-15

## Context

The AI agent requires the ability to access and utilize a dynamic knowledge base to provide more accurate, relevant, and context-aware responses. This involves retrieving information from various sources (documents, web pages) and integrating it into the language model's generation process.

## Decision

We will implement a Retrieval Augmented Generation (RAG) system. This system will comprise the following key components:

1.  **Knowledge Graph Database:** [Memgraph](https://memgraph.com/) will be used to store metadata, relationships between documents, chunks, sources, and interactions. Its graph capabilities are ideal for modeling complex relationships.
    *   Implementation: `src/core/rag/dbhandler/memgraph.py` (specifically `MemGraphClient`)
    *   Generic Interface: `src/core/rag/dbhandler/__init__.py` (defines `GraphClient`)

2.  **Vector Embedder:** A service to generate vector embeddings for text chunks. Initially, we will use OpenAI's `text-embedding-3-small` model.
    *   Implementation: `src/core/rag/embedder/text_embedding_3_small.py`
    *   Generic Interface: `src/core/rag/embedder/__init__.py` (defines `EmbeddingService`)

3.  **Data Loaders:** Utilities to fetch and process data from different sources (e.g., local files, web URLs).
    *   Implementations: `src/libs/dataloader/document.py`, `src/libs/dataloader/web.py`
    *   Common Interface: `src/libs/dataloader/__init__.py`

4.  **RAG Schema:** Defines the structure (nodes and edges) of the knowledge graph.
    *   Implementation: `src/core/rag/schema.py`

5.  **Retriever (Conceptual - No dedicated file yet):** Logic to query the vector store and knowledge graph to find relevant information based on user queries. This logic is currently integrated within other components but may be centralized later.

## Consequences

### Positive

*   **Improved Response Quality:** The agent can access and cite specific information, leading to more factual and detailed answers.
*   **Dynamic Knowledge:** The knowledge base can be updated without retraining the LLM.
*   **Scalability:** Memgraph and vector stores are designed to handle large datasets.
*   **Traceability:** Graph relationships allow for tracing information sources and understanding context flow.

### Negative

*   **Increased Complexity:** Adds more components and infrastructure to manage.
*   **Latency:** Retrieval step can add latency to response times.
*   **Cost:** Vector embedding and database services may incur additional costs.

## Alternatives Considered

*   **Fine-tuning LLMs:** While powerful, fine-tuning requires significant data and computational resources for each knowledge update and doesn't easily allow for citing specific sources in the same way RAG does.
*   **Simpler Vector Search:** Using only a vector database without a graph component would limit the ability to model and query complex relationships between data entities.

## Future Considerations

*   **Vector Store Abstraction:** Introduce an abstraction layer for vector storage to support different providers (e.g., FAISS, Pinecone, dedicated vector databases integrated with Memgraph).
*   **Advanced Retrieval Strategies:** Implement more sophisticated retrieval techniques (e.g., hybrid search, re-ranking).
*   **Automated Knowledge Base Updates:** Develop pipelines for continuous and automated updates to the knowledge graph and vector store.
*   **Centralized Retriever Logic:** Refactor retrieval logic into a dedicated `src/core/rag/retriever.py` module for better organization as complexity grows.