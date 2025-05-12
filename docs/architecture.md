# AI Agent Architecture

This document describes the architecture and workflow of the AI Agent application, specifically focusing on the chat-with-tools-and-mcp functionality.

## Sequence Diagram

```mermaid
sequenceDiagram
    participant User
    participant Agent as AI Agent
    participant Azure as GPT-4.1
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
        %% Decision for Tool Usage
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
   - web_fetch: Fetches content from web pages
   - write_file: Writes content to files

5. **MCP Server**: Model Context Protocol server that provides additional tools:
   - get_ice_cream_recommendation: Provides ice cream flavor recommendations
   - Additional tools that may be available depending on server configuration

6. **External Services**: Third-party services called by tools:
   - Search engines (for google_search)
   - File systems (for file operations)
   - Web services (for web_fetch)
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