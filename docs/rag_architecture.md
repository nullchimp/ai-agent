# RAG Architecture

This document outlines the architecture of our Retrieval-Augmented Generation (RAG) system using llama-index for document loading and text chunking with overlapping strategy.

## Architecture Diagram

```mermaid
graph TD
    A[Raw Documents] --> B[Document Loader]
    B --> C[Text Splitter]
    C --> D[Document Chunks with Overlap]
    D --> E[Embedding Generation]
    E --> F[Database Storage]
    
    subgraph "Document Loading"
        B
        B1[PDF Loader] --> B
        B2[Text Loader] --> B
        B3[HTML Loader] --> B
        B4[Markdown Loader] --> B
        B5[DOCX Loader] --> B
    end
    
    subgraph "Text Splitting"
        C
        C1[Chunk Size] --> C
        C2[Overlap Size] --> C
        C3[Split Strategy] --> C
    end
    
    subgraph "Database Integration"
        F
        F1[Store Parent Document] --> F
        F2[Store Chunks] --> F
        F3[Link Chunks to Parent] --> F
        F4[Store Metadata] --> F
    end
    
    G[Query] --> H[Vector Search]
    H --> I[Retrieve Relevant Chunks]
    I --> J[Response Generation]
    
    subgraph "Semantic Search"
        H
        H1[Chunk-Based Search] --> H
        H2[Parent Document Search] --> H
        H3[Conversation-Aware Search] --> H
    end