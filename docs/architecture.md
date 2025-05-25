---
title: Project Architecture
description: Overview of the AI Agent's software architecture.
---

# AI Agent Software Architecture

This document provides an overview of the AI Agent's software architecture, detailing its main components and how they interact. The primary goal is to create a modular, extensible, and maintainable system.

## Core Components

The system is divided into several key packages and modules, primarily located within the `src` directory.

```mermaid
graph TD
    %% Define font size
    %% @config{
    %%  "themeVariables": {
    %%    "fontSize": "18px"
    %%  }
    %% }

    subgraph "Entry & Orchestration"
        Main[src/main.py]
        Agent[src/agent.py]
    end

    subgraph "Core Logic - src/core"
        subgraph "LLM Handling"
            LLMCore[LLM Client]
            Chat[Chat Service]
        end

        subgraph "RAG System"
            RAGSchema[Schema]
            RAGDB[DB Handler]
            RAGEmbed[Embedder]
            Memgraph[Memgraph Client]
        end

        subgraph "MCP"
            MCPSession[Session]
            MCPSessionMgr[Sessions Manager]
        end
        Utils[Utilities]
    end

    subgraph "Libraries - src/libs"
        subgraph "Data Loaders"
            DocLoader[Document Loader]
            WebLoader[Web Loader]
        end
        FileOps[File Operations]
        Search[Search]
    end

    subgraph "Tools - src/tools"
        ToolBase[Base Tool]
        GoogleSearchTool[Google Search]
        ReadFileTool[Read File]
        WriteFileTool[Write File]
        ListFilesTool[List Files]
        Context7Tool[Context7]
    end

    subgraph "Configuration & Environment"
        Env[.env]
        ConfigMCP[config/mcp.json]
    end

    %% Relationships
    Main --> Agent
    Main --> MCPSessionMgr
    Agent --> Chat
    Agent --> ToolBase
    Agent -- uses --> RAGSchema
    Agent -- uses --> RAGDB
    Agent -- uses --> RAGEmbed
    Agent -- uses --> FileOps
    Agent -- uses --> Search

    Chat --> LLMCore
    
    RAGDB --> Memgraph
    RAGDB -- uses --> DocLoader
    RAGDB -- uses --> WebLoader

    MCPSessionMgr --> Context7Tool
    MCPSessionMgr --> MCPSession

    ToolBase --> GoogleSearchTool
    ToolBase --> ReadFileTool
    ToolBase --> WriteFileTool
    ToolBase --> ListFilesTool
    ToolBase --> Context7Tool

    Main -- reads --> ConfigMCP
    Agent -- reads --> Env
    LLMCore -- reads --> Env

    %% Remove classDefs for colors
```

## Sequence Diagram

```mermaid
sequenceDiagram
    participant User
    participant Agent as AI Agent
    participant Azure as Azure OpenAI
    participant KnowledgeBase as RAG Knowledge Base
    participant Tools as Local Tools
    participant MCP as MCP Server
    participant ExternalServices as External Services
    
    %% Initialization Phase
    Note over Agent: Initialization
    Agent->>Azure: Initialize LLM Client (for chat & embeddings)
    Agent->>KnowledgeBase: Initialize RAG System (e.g., DB connection)
    Agent->>Tools: Initialize Local Tools
    Agent->>MCP: Initialize MCP Server
    MCP-->>Agent: Return Available Tools
    
    User->>Agent: Send query

    %% Query Processing & RAG Augmentation Phase
    Note over Agent: Augmenting query with RAG context
    Agent->>Azure: Generate embedding for user query (via RAG Embedder)
    Azure-->>Agent: Return query embedding
    Agent->>KnowledgeBase: Retrieve relevant documents using query embedding (via RAG DBHandler)
    KnowledgeBase-->>Agent: Return RAG context (retrieved documents)

    Agent->>Azure: Send User Query + RAG Context to LLM (for chat completion)

    %% Decision for Tool Usage
    loop Model decides to use tools
        Azure-->>Agent: Request Tool Call (from LLM)

        %% Tool Execution Phase
        Note over Agent: Tool Execution
        alt Local Tool
            Agent->>Tools: Use Tool (e.g., google_search)
            Tools<<->>ExternalServices: Call External Service (e.g., Google Search API)
            Tools-->>Agent: Return Tool Results
        else MCP Server Tool
            Agent->>MCP: Use Tool (e.g., get_ice_cream_recommendation)
            MCP<<->>ExternalServices: Call External Service (e.g. Database for MCP Tool)
            MCP-->>Agent: Return Tool Results
        end

        Agent->>Azure: Send Tool Results to LLM
    end
    
    %% Model generates response
    Note over Agent: Response Generation
    Azure-->>Agent: Generate Response (from LLM)
    Agent-->>User: Return Response to User
```


### 1. Entry & Orchestration (`src/`)
*   **`main.py`**: The main entry point of the application. Initializes core services, including the `MCPSessionManager` for discovering and integrating MCP-compatible tools, and starts the main agent loop.
*   **`agent.py`**: Contains the primary agent logic. It manages the conversation flow, interacts with the `Chat` service for LLM communication, and utilizes available `Tools` to perform actions or gather information.

### 2. Core Logic (`src/core/`)
This package houses the fundamental building blocks of the agent.

*   **LLM Handling (`src/core/llm/`)**
    *   `client.py`: Provides a low-level client for interacting with Large Language Models (e.g., OpenAI API). Handles API requests, responses, and error management.
    *   `chat.py`: Offers a higher-level `Chat` service that abstracts conversation management, message history, and tool integration with the LLM.

*   **RAG System (`src/core/rag/`)**: Enables Retrieval Augmented Generation.
    *   `schema.py`: Defines the nodes (e.g., `Document`, `DocumentChunk`) and edges (relationships) for the knowledge graph. Detailed node and edge types are described in the "RAG Graph Schema Details" section below.
    *   `dbhandler/__init__.py`: Defines the `GraphClient` interface for interacting with graph databases.
    *   `dbhandler/memgraph.py`: Implements `MemGraphClient` for storing and querying graph data in Memgraph.
    *   `embedder/__init__.py`: Defines the `EmbeddingService` interface for generating text embeddings.
    *   `embedder/text_embedding_3_small.py`: Implements embedding generation using a specific model (e.g., OpenAI's).
    *   For more details, see [RAG Architecture](./rag_architecture.md).

*   **MCP (Model Context Protocol) (`src/core/mcp/`)**
    *   `session.py`: Manages an individual session with an MCP-compatible tool/server.
    *   `sessions_manager.py`: Discovers, registers, and manages multiple MCP sessions, making external tools available to the agent.

*   **Utilities (`src/core/utils.py`, etc.)**: Common utility functions, decorators (e.g., `graceful_exit`, `mainloop`), and helper classes used across the application.

### 3. Libraries (`src/libs/`)
Reusable libraries providing specific functionalities.

*   **Data Loaders (`src/libs/dataloader/`)**: Modules for loading and processing data from various sources.
    *   `document.py`: Handles loading from local document files.
    *   `web.py`: Handles fetching content from web URLs.
*   **File Operations (`src/libs/fileops/file.py`)**: Utilities for file system interactions (reading, writing, listing files).
*   **Search (`src/libs/search/`)**: Components for integrating with external search services (e.g., Google Search API client and service).

### 4. Tools (`src/tools/`)
Defines the tools available to the AI agent. Each tool typically inherits from a base `Tool` class (found in `src/tools/__init__.py`) and implements specific actions.

*   `google_search.py`: Tool for performing Google searches.
*   `read_file.py`: Tool for reading file contents.
*   `write_file.py`: Tool for writing content to files.
*   `list_files.py`: Tool for listing files in a directory.
*   `context7.py`: Tool for interacting with the Context7 API (e.g., for fetching coding best practices).
*   Other tools can be added here to extend the agent's capabilities.

### 5. Configuration & Environment
*   `.env`: Stores environment variables, including API keys and other secrets. This file is not committed to the repository.
*   `config/mcp.json`: Configuration file for the `MCPSessionManager`, specifying details for connecting to MCP servers/tools.

## Design Principles

*   **Modularity:** Components are designed to be independent and interchangeable where possible.
*   **Extensibility:** New tools, LLM providers, data sources, and libraries can be added with minimal changes to the core system.
*   **Separation of Concerns:** Different functionalities (e.g., LLM interaction, RAG, tool usage) are handled by distinct modules.
*   **Abstraction:** Interfaces (e.g., `GraphClient`, `EmbeddingService`, `Tool`) allow for different implementations.

## RAG Graph Schema Details

This section outlines the types of nodes and the relationships (edges) between them within the Retrieval Augmented Generation (RAG) knowledge graph. The schema is primarily defined in `src/core/rag/schema.py`.

### Node Types

The core entities in our graph are:

*   **`DOCUMENT`**: Represents a full document, such as a file or a web page, containing content and metadata.
*   **`DOCUMENTCHUNK`**: Represents a segment of a `DOCUMENT`. These chunks are what get embedded and used for similarity searches. Content is stored in both the graph and the vector store.
*   **`INTERACTION`**: Represents a chat message (user or assistant) or a system-level interaction/event.
*   **`SOURCE`**: Represents the origin of a `DOCUMENT`, like a website URL, a file path, or an API endpoint.
*   **`VECTORSTORE`**: Represents an embedding storage system where vector embeddings are kept.
*   **`VECTOR`**: Represents the actual embedding vector for a `DOCUMENTCHUNK`.

### Edge Types (Relationships)

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

### RAG Schema Diagram

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
```

This schema allows for flexible querying of document origins, their content (via chunks and embeddings), and the history of interactions related to them.

This architecture provides a solid foundation for developing a sophisticated and adaptable AI agent.