# AI Agent Architecture

This document describes the architecture and workflow of the AI Agent application, specifically focusing on the chat-with-tools-and-mcp functionality.

## Sequence Diagram

```mermaid
sequenceDiagram
    participant User
    participant Agent as AI Agent
    participant Azure as Azure OpenAI
    participant Tools as Local Tools
    participant MCP as MCP Server
    participant ExternalServices as External Services
    
    %% Initialization Phase
    Note over Agent: Initialization
    Agent->>Azure: Initialize Client
    Agent->>Tools: Initialize Local Tools
    Agent->>MCP: Initialize MCP Server
    MCP-->>Agent: Return Available Tools
    
    User->>Agent: Send query

    %% Query Processing Phase
    Note over Agent: Query Processing
    Agent->>Azure: Send User Query to Model
    
    %% Decision for Tool Usage
    loop Model decides to use tools
        Azure-->>Agent: Request Tool Call
        
        %% Tool Execution Phase
        Note over Agent: Tool Execution
        alt Local Tool
            Agent->>Tools: Use Tool (e.g., google_search)
            Tools<<->>ExternalServices: Call External Service (e.g., Google Search API)
            Tools-->>Agent: Return Tool Results
        else MCP Server Tool
            Agent->>MCP: Use Tool (e.g., get_ice_cream_recommendation)
            MCP<<->>ExternalServices: Call External Service (e.g. Database)
            MCP-->>Agent: Return Tool Results
        end
        
        Agent->>Azure: Send Tool Results to Model
    end
    
    %% Model generates response
    Note over Agent: Response Generation
    Azure-->>Agent: Generate Response
    Agent-->>User: Return Response to User
```
    Agent-->>User: Return Response to User
```

## Components

1. **User**: Initiates interaction by sending queries to the AI Agent.

2. **AI Agent**: The main application that orchestrates the entire workflow:
   - Initializes the Azure OpenAI client
   - Discovers and initializes available tools (both local and MCP-based)
   - Processes user queries
   - Routes tool calls to appropriate services
   - Returns final responses to the user

3. **Azure OpenAI Service (GPT-4.1)**: Provides the language model capabilities:
   - Processes natural language queries
   - Determines when and which tools to call
   - Generates final responses based on user queries and tool results

4. **Local Tools**: Built-in tools available to the agent:
   - google_search: Searches the web for information
   - list_files: Lists files in a directory
   - read_file: Reads content from files
   - write_file: Writes content to files

5. **MCP Server**: Model Context Protocol server that provides additional tools:
   - get_ice_cream_recommendation: Provides ice cream flavor recommendations
   - Additional tools that may be available depending on server configuration

6. **External Services**: Third-party services called by tools:
   - Search engines (for google_search)
   - File systems (for file operations)
   - Databases (for MCP tools)
   - Other APIs as needed

## Workflow Description

1. **Initialization Phase**:
   - The AI Agent initializes connections to Azure OpenAI Service
   - Local tools are registered and prepared for use
   - The MCP Server connection is established
   - Available MCP tools are discovered and registered with the Agent

2. **Query Processing**:
   - The user sends a natural language query to the AI Agent
   - The Agent passes this query to the Azure OpenAI model (GPT-4.1)
   - The model analyzes the query to determine the appropriate response strategy

3. **Tool Selection and Execution**:
   - If the model determines tools are needed, it requests specific tool calls
   - The Agent evaluates whether the requested tool is local or MCP-based:
     - For local tools: The Agent executes the tool directly, which may interact with external services
     - For MCP tools: The Agent forwards the request to the MCP Server, which handles execution
   - Tool execution results are collected and formatted by the Agent

4. **Response Generation**:
   - Tool results are sent back to the Azure OpenAI model
   - The model integrates these results with its knowledge to generate a comprehensive response
   - The Agent formats and returns the final response to the user

This workflow enables the AI Agent to leverage both built-in capabilities and external tools to provide rich, contextual responses to user queries while maintaining a clean separation of concerns between components.

## Component Architecture

```mermaid
graph TB
    subgraph "AI Agent Application"
        Agent[agent.py]
        Main[main.py]
    end
    
    subgraph "Core Modules"
        LLM[core/llm/]
        MCP[core/mcp/]
        RAG[core/rag/]
        
        subgraph "LLM Components"
            Chat[chat.py]
            Client[client.py]
        end
        
        subgraph "MCP Components"
            Session[session.py]
            SessionsManager[sessions_manager.py]
        end
        
        subgraph "RAG Components"
            Schema[schema.py]
            DBHandler[dbhandler/]
            Embedder[embedder/]
            
            subgraph "Database"
                GraphClient[GraphClient]
                MemgraphClient[MemgraphClient]
            end
            
            subgraph "Embeddings"
                TextEmbedding[TextEmbedding3Small]
            end
        end
    end
    
    subgraph "Libraries"
        DataLoader[libs/dataloader/]
        FileOps[libs/fileops/]
        Search[libs/search/]
        
        subgraph "Data Loading"
            DocLoader[document.py]
            WebLoader[web.py]
        end
    end
    
    subgraph "Tools"
        GoogleSearch[google_search.py]
        ListFiles[list_files.py]
        ReadFile[read_file.py]
        WriteFile[write_file.py]
    end
    
    subgraph "External Services"
        AzureOpenAI[Azure OpenAI]
        GoogleAPI[Google Search API]
        Memgraph[Memgraph Database]
        FileSystem[File System]
    end
    
    Agent --> LLM
    Agent --> Tools
    Main --> Agent
    Main --> MCP
    
    LLM --> Chat
    LLM --> Client
    Client --> AzureOpenAI
    
    MCP --> Session
    MCP --> SessionsManager
    
    RAG --> Schema
    RAG --> DBHandler
    RAG --> Embedder
    DBHandler --> GraphClient
    DBHandler --> MemgraphClient
    MemgraphClient --> Memgraph
    Embedder --> TextEmbedding
    TextEmbedding --> AzureOpenAI
    
    DataLoader --> DocLoader
    DataLoader --> WebLoader
    
    Tools --> GoogleSearch
    Tools --> ListFiles
    Tools --> ReadFile
    Tools --> WriteFile
    
    GoogleSearch --> GoogleAPI
    ListFiles --> FileSystem
    ReadFile --> FileSystem
    WriteFile --> FileSystem
```

## Component Details

### Core Application Files
- **`agent.py`**: Main AI agent entry point with conversation handling and tool orchestration
- **`main.py`**: Application startup script that initializes MCP sessions and starts the agent

### Core Modules

#### LLM (Language Model) - `core/llm/`
- **`chat.py`**: Handles chat interactions, tool calling, and message processing
- **`client.py`**: Azure OpenAI client wrapper for API communication

#### MCP (Model Context Protocol) - `core/mcp/`
- **`session.py`**: Individual MCP server session management
- **`sessions_manager.py`**: Orchestrates multiple MCP server connections and tool discovery

#### RAG (Retrieval-Augmented Generation) - `core/rag/`
- **`schema.py`**: Data models for graph database entities (Document, Chunk, Source, etc.)
- **`dbhandler/`**: Database interface implementations
  - **`__init__.py`**: Base GraphClient interface and implementation
  - **`memgraph.py`**: Memgraph-specific client implementation
- **`embedder/`**: Vector embedding services
  - **`text_embedding_3_small.py`**: Azure OpenAI embedding service implementation

### Libraries - `libs/`

#### Data Loading - `dataloader/`
- **`document.py`**: File-based document loader with chunking capabilities
- **`web.py`**: Web content loader with crawling support

#### File Operations - `fileops/`
- **`file.py`**: Core file operation utilities

#### Search - `search/`
- **`client.py`**: Search client interface
- **`service.py`**: Search service implementation

### Tools - `tools/`
Built-in tools available to the AI agent:
- **`google_search.py`**: Web search functionality using Google Search API
- **`list_files.py`**: Directory listing operations
- **`read_file.py`**: File content reading operations
- **`write_file.py`**: File content writing operations