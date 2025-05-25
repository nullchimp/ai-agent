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
    subgraph "Entry & Orchestration"
        Main[src/main.py]
        Agent[src/agent.py]
    end

    subgraph "Core Logic - src/core"
        subgraph "LLM Handling - src/core/llm"
            LLMCore[LLM Client - src/core/llm/client.py]
            Chat[Chat Service - src/core/llm/chat.py]
        end

        subgraph "RAG System - src/core/rag"
            RAGSchema[Schema - src/core/rag/schema.py]
            RAGDB[DB Handler - src/core/rag/dbhandler/__init__.py]
            RAGEmbed[Embedder - src/core/rag/embedder/__init__.py]
            Memgraph[Memgraph Client - src/core/rag/dbhandler/memgraph.py]
        end

        subgraph "MCP (Model Context Protocol) - src/core/mcp"
            MCPSession[Session - src/core/mcp/session.py]
            MCPSessionMgr[Sessions Manager - src/core/mcp/sessions_manager.py]
        end
        Utils[Utilities - src/core/utils.py, etc.]
    end

    subgraph "Libraries - src/libs"
        subgraph "Data Loaders - src/libs/dataloader"
            DocLoader[Document - src/libs/dataloader/document.py]
            WebLoader[Web - src/libs/dataloader/web.py]
        end
        FileOps[File Operations - src/libs/fileops/file.py]
        Search[Search Client/Service - src/libs/search/]
    end

    subgraph "Tools - src/tools"
        ToolBase[Base Tool - src/tools/__init__.py]
        GoogleSearchTool[Google Search - src/tools/google_search.py]
        ReadFileTool[Read File - src/tools/read_file.py]
        WriteFileTool[Write File - src/tools/write_file.py]
        ListFilesTool[List Files - src/tools/list_files.py]
        Context7Tool[Context7 - src/tools/context7.py]
        %% Add other tools as they are implemented
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
    MCPSessionMgr --> Context7Tool
    MCPSessionMgr --> MCPSession

    Chat --> LLMCore
    ToolBase --> GoogleSearchTool
    ToolBase --> ReadFileTool
    ToolBase --> WriteFileTool
    ToolBase --> ListFilesTool
    ToolBase --> Context7Tool

    %% RAG Integration (Simplified)
    Agent -- uses --> RAGSchema
    Agent -- uses --> RAGDB
    Agent -- uses --> RAGEmbed
    RAGDB --> Memgraph

    %% Libs Usage (Simplified)
    Agent -- uses --> FileOps
    Agent -- uses --> Search
    RAGDB -- uses --> DocLoader
    RAGDB -- uses --> WebLoader

    %% Config Usage
    Main -- reads --> ConfigMCP
    Agent -- reads --> Env
    LLMCore -- reads --> Env

    classDef entry fill:#E1F5FE,stroke:#0288D1,stroke-width:2px
    classDef core fill:#E8EAF6,stroke:#3F51B5,stroke-width:2px
    classDef libs fill:#E0F2F1,stroke:#00796B,stroke-width:2px
    classDef tools fill:#FCE4EC,stroke:#D81B60,stroke-width:2px
    classDef config fill:#FFFDE7,stroke:#FBC02D,stroke-width:2px

    class Main,Agent entry
    class LLMCore,Chat,RAGSchema,RAGDB,RAGEmbed,Memgraph,MCPSession,MCPSessionMgr,Utils core
    class DocLoader,WebLoader,FileOps,Search libs
    class ToolBase,GoogleSearchTool,ReadFileTool,WriteFileTool,ListFilesTool,Context7Tool tools
    class Env,ConfigMCP config
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
    *   `schema.py`: Defines the nodes (e.g., `Document`, `DocumentChunk`) and edges (relationships) for the knowledge graph.
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

This architecture provides a solid foundation for developing a sophisticated and adaptable AI agent.