# AI Agent

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)

An advanced AI agent with a modern web interface, capable of performing complex tasks, answering questions, and interacting with various tools and data sources. This project features a comprehensive REST API, session management, debug capabilities, and seamless integration with Large Language Models (LLMs), Retrieval Augmented Generation (RAG), and Model Context Protocol (MCP) servers.

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Setup and Installation](#setup-and-installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [Tools](#tools)
- [Contributing](#contributing)
- [License](#license)

## Features

### 🎯 Core Capabilities
*   **Conversational AI:** Engage in natural language conversations with advanced context awareness.
*   **Multi-Tool Integration:** Seamlessly use a variety of tools for web searches, file operations, and specialized tasks.
*   **Session Management:** Support for multiple concurrent conversations with isolated state and debug tracking.
*   **Real-time Processing:** Asynchronous operations for efficient handling of I/O-bound tasks.

### 🌐 Web Interface & API
*   **Modern Chat UI:** ChatGPT-inspired web interface built with TypeScript, HTML5, and CSS3.
*   **REST API:** Comprehensive FastAPI-based backend with full OpenAPI documentation.
*   **Session Isolation:** Each conversation maintains its own context, tools, and debug state.
*   **Real-time Communication:** Responsive frontend with typing indicators and message streaming.

### 🔧 Advanced Features
*   **Retrieval Augmented Generation (RAG):** Enhanced responses using a Memgraph knowledge graph and vector embeddings.
*   **Model Context Protocol (MCP):** Integration with external tools and services following MCP standards.
*   **Debug System:** Comprehensive debugging with per-session event capture and visualization.
*   **Tool Configuration:** Dynamic tool enabling/disabling with real-time configuration updates.
*   **Data Loading:** Support for multiple data sources including web pages, documents, and APIs.

### 🛡️ Security & Quality
*   **API Authentication:** Secure API access with configurable API key authentication.
*   **Input Validation:** Robust data validation using Pydantic models.
*   **Error Handling:** Graceful error handling with detailed logging and debugging.
*   **Code Quality:** Enforced coding standards with Black, isort, pylint, and mypy.

## Architecture

The AI Agent features a sophisticated, modular architecture designed for scalability and maintainability:

### 🏗️ Core Components
*   **Agent Core (`src/agent.py`):** Orchestrates conversation flow, tool interactions, and session management.
*   **REST API (`src/api/`):** FastAPI-based web server with session routing, authentication, and static file serving.
*   **LLM Services (`src/core/llm/`):** Manages communication with Azure OpenAI for chat and embeddings.
*   **RAG System (`src/core/rag/`):** Implements retrieval augmented generation using Memgraph and vector embeddings.
*   **MCP Integration (`src/core/mcp/`):** Handles discovery and communication with MCP-compatible external tools.
*   **Debug System (`src/core/debug_capture.py`):** Per-session debugging with event capture and analysis.

### 🧰 Supporting Infrastructure  
*   **Libraries (`src/libs/`):** Reusable modules for data loading, file operations, and search functionality.
*   **Tools (`src/tools/`):** Extensible collection of callable tools for various operations.
*   **UI (`src/ui/`):** Modern web frontend with TypeScript, responsive design, and real-time updates.

### 🔄 Session Management
*   **Isolated Sessions:** Each conversation maintains independent state, tools, and debug information.
*   **Persistent Storage:** Session data persisted in browser localStorage with seamless restoration.
*   **Dynamic Configuration:** Real-time tool configuration and debug panel management per session.

For detailed architectural information, see the [Project Architecture Document](./docs/architecture.md).

## Project Structure

The project follows a modular, well-organized structure:

```
ai-agent/
├── .github/                # GitHub Actions workflows and Copilot configuration
│   ├── prompts/            # Custom prompts for GitHub Copilot
│   └── workflows/          # CI/CD automation workflows
├── config/                 # Configuration files
│   ├── mcp.json            # MCP server configurations
│   ├── mcp-demo.json       # Demo MCP configurations
│   └── mcp.template.json   # Template for MCP setup
├── docs/                   # Comprehensive project documentation
│   ├── ADRs/               # Architecture Decision Records
│   │   ├── frontend-integration.md
│   │   ├── rag-integration.md
│   │   └── rest-api-integration.md
│   ├── architecture.md     # Main architecture overview
│   └── chat.png           # UI screenshot
├── src/                    # Main source code
│   ├── agent.py            # Core agent orchestration logic
│   ├── main.py             # Application entry point (CLI & API modes)
│   ├── api/                # REST API implementation
│   │   ├── app.py          # FastAPI application factory
│   │   ├── auth.py         # API authentication middleware
│   │   ├── models.py       # Pydantic request/response models
│   │   └── routes.py       # API endpoint definitions
│   ├── core/               # Core business logic
│   │   ├── debug_capture.py # Session-based debugging system
│   │   ├── llm/            # LLM client implementations
│   │   │   ├── chat.py     # High-level chat interface
│   │   │   └── client.py   # Azure OpenAI API clients
│   │   ├── mcp/            # Model Context Protocol integration
│   │   │   ├── session.py  # Individual MCP session management
│   │   │   └── sessions_manager.py # Multi-session coordination
│   │   └── rag/            # Retrieval Augmented Generation
│   │       ├── dbhandler/  # Graph database interfaces
│   │       │   ├── __init__.py     # Generic GraphClient
│   │       │   └── memgraph.py     # Memgraph implementation
│   │       ├── embedder/   # Text embedding services
│   │       └── schema.py   # RAG data models and relationships
│   ├── libs/               # Reusable utility libraries
│   │   ├── dataloader/     # Data loading from various sources
│   │   │   ├── document.py # Document processing
│   │   │   └── web.py      # Web scraping and crawling
│   │   ├── fileops.py      # File system operations
│   │   └── search.py       # Search functionality
│   ├── tools/              # Extensible tool system
│   │   ├── __init__.py     # Base tool interface
│   │   ├── google_search.py # Web search capabilities
│   │   ├── read_file.py    # File reading operations
│   │   ├── write_file.py   # File writing operations
│   │   ├── list_files.py   # Directory listing
│   │   └── context7.py     # Context7 API integration
│   └── ui/                 # Modern web interface
│       ├── index.html      # Main HTML structure
│       ├── styles.css      # Responsive CSS styling
│       ├── chat.ts         # TypeScript application logic
│       └── dist/           # Compiled frontend assets
├── tests/                  # Comprehensive test suite
│   ├── test_api_*          # API endpoint tests
│   ├── test_core_*         # Core component tests
│   ├── test_frontend_*     # Frontend integration tests
│   ├── test_tools_*        # Tool functionality tests
│   └── test_ui_*           # User interface tests
├── scripts/                # Utility scripts
│   ├── doc_loader.py       # Document processing scripts
│   ├── url_loader.py       # Web content loader
│   └── loader_config.py    # Configuration for data loaders
├── examples/               # Usage examples and demos
│   ├── 1-chat.py           # Basic chat example
│   ├── 2-tool.py           # Tool usage example
│   ├── 3-chat-with-tools.py # Combined chat and tools
│   ├── 4-chat-with-tools-and-mcp.py # Full MCP integration
│   ├── 5-memgraph.py       # RAG/Memgraph example
│   └── 6-embeddings.py     # Embedding generation example
├── .env                    # Environment variables (not in repo)
├── requirements.txt        # Python dependencies
├── package.json            # Node.js dependencies for frontend
├── tsconfig.json           # TypeScript configuration
└── pyproject.toml          # Python project configuration
```

## Setup and Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/nullchimp/ai-agent.git
    cd ai-agent
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up environment variables:**
    Copy `.env.example` to `.env` and fill in the required API keys and configurations (e.g., `OPENAI_API_KEY`, `MEMGRAPH_HOST`).
    ```bash
    cp .env.example .env
    # Edit .env with your credentials
    ```

5.  **Ensure Memgraph is running** (if using the RAG features with Memgraph).
    Refer to the [Memgraph documentation](https://memgraph.com/docs/getting-started) for setup instructions.

## Usage

The AI Agent supports multiple interaction modes to accommodate different use cases and deployment scenarios.

### 🖥️ CLI Mode (Command Line Interface)

For direct terminal interaction with the agent:

```bash
python src/main.py
```

This mode provides a simple command-line chat interface for testing and development.

### 🌐 Web Interface Mode (Recommended)

The agent includes a modern, ChatGPT-like web interface for the best user experience.

#### Building the Frontend

First, build the frontend assets (required for web interface):

```bash
npm install
npm run ui:build
```

#### Starting the Web Server

Run the agent with the integrated web server:

```bash
python src/main.py --api
```

The application will be available at `http://localhost:5555` (or your configured host/port).

### 🎯 Web Interface Features

![AI Agent Chat Interface](./docs/chat.png)

The web interface provides a rich, interactive experience:

#### 💬 **Chat Experience**
- **Real-time messaging** with typing indicators and smooth animations
- **Markdown support** for rich text rendering and code syntax highlighting  
- **Message history** with persistent storage across browser sessions
- **Responsive design** that works seamlessly on desktop and mobile devices

#### 🗂️ **Session Management**
- **Multiple conversations** with independent context and state
- **Session switching** with preserved history and tool configurations
- **Auto-generated titles** based on conversation content
- **Local persistence** using browser localStorage

#### 🔧 **Tool Configuration**
- **Dynamic tool management** with real-time enable/disable controls
- **Tool status indicators** showing available and active tools
- **Per-session tool configuration** maintained independently
- **Tool parameter visualization** for debugging and monitoring

#### 🐛 **Advanced Debugging**
- **Per-session debug panel** with isolated event tracking
- **Real-time event capture** showing LLM requests, tool calls, and responses
- **Color-coded event visualization** for easy debugging
- **Debug state persistence** across session switches and browser reloads
- **Event filtering and search** capabilities
- **Fullscreen debug viewer** for detailed event analysis

#### ⚡ **Performance Features**
- **Asynchronous operations** for responsive user experience
- **Optimized rendering** with efficient DOM updates
- **Lazy loading** for improved startup performance
- **Memory management** with automatic cleanup

## User Interface

The AI Agent features a modern, ChatGPT-inspired web interface that provides an intuitive and powerful user experience.

### 🎨 **Design & User Experience**

#### Modern Interface Design
- **Clean, minimalist aesthetic** inspired by ChatGPT
- **Responsive layout** that adapts to all screen sizes
- **Dark/light theme support** with system preference detection
- **Smooth animations** and transitions for enhanced usability
- **Professional typography** using Inter font family

#### Chat Experience
- **Real-time messaging** with typing indicators
- **Markdown rendering** with syntax highlighting for code blocks
- **Message threading** with clear sender identification  
- **Copy-to-clipboard** functionality for easy sharing
- **Scroll management** with auto-scroll and manual control

### 📱 **Responsive Design**

The interface is fully responsive and works seamlessly across:
- **Desktop computers** with full feature access
- **Tablets** with touch-optimized interactions
- **Mobile devices** with collapsible sidebars and optimized layouts
- **Various screen resolutions** with adaptive breakpoints

### 🎛️ **Interactive Controls**

#### Session Management
- **Sidebar navigation** with conversation history
- **One-click session creation** with auto-generated titles
- **Session switching** with preserved context
- **Session deletion** with confirmation dialogs

#### Tool Configuration Panel
- **Collapsible tools section** for space optimization
- **Visual tool status indicators** (enabled/disabled/active)
- **Real-time tool toggling** without page refresh
- **Tool description tooltips** for guidance

#### Advanced Debug Panel
- **Sliding debug overlay** with detailed event logging
- **Color-coded event types** for quick identification
- **Expandable event details** with JSON formatting
- **Event timeline** with timestamp information
- **Debug state controls** (enable/disable/clear)

### ⚡ **Performance & Accessibility**

#### Fast & Efficient
- **TypeScript implementation** for type safety and performance
- **Optimized DOM manipulation** with minimal reflows
- **Efficient memory management** with garbage collection
- **Lazy loading** for improved startup times

#### Accessible Design
- **Keyboard navigation** support throughout the interface
- **Screen reader compatibility** with proper ARIA labels
- **High contrast ratios** for visual accessibility
- **Focus management** for seamless interaction

## Configuration

The AI Agent uses a flexible configuration system supporting environment variables, JSON configuration files, and runtime settings.

### 🔐 **Environment Variables (`.env`)**

Create a `.env` file in the project root with the following configuration:

```bash
# Azure OpenAI Configuration
AZURE_OPENAI_API_KEY=your_azure_openai_api_key
AZURE_OPENAI_CHAT_MODEL=gpt-4
AZURE_OPENAI_CHAT_ENDPOINT=https://your-resource.openai.azure.com/openai/deployments/gpt-4/chat/completions?api-version=2024-02-15-preview
AZURE_OPENAI_EMBEDDINGS_MODEL=text-embedding-3-small  
AZURE_OPENAI_EMBEDDINGS_ENDPOINT=https://your-resource.openai.azure.com/openai/deployments/text-embedding-3-small/embeddings?api-version=2024-02-15-preview

# API Server Configuration
API_KEY=your_secure_api_key_here
API_HOST=localhost
API_PORT=5555

# Memgraph Database Configuration (for RAG features)
MEMGRAPH_URI=localhost
MEMGRAPH_PORT=7687
MEMGRAPH_USERNAME=memgraph
MEMGRAPH_PASSWORD=memgraph

# Google Search Configuration (optional)
GOOGLE_API_KEY=your_google_api_key
GOOGLE_CSE_ID=your_custom_search_engine_id

# Context7 API Configuration (optional)
CONTEXT7_API_KEY=your_context7_api_key
```

### 🔧 **MCP Configuration (`config/mcp.json`)**

Configure external Model Context Protocol servers and tools:

```json
{
  "servers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/allowed/files"],
      "env": {
        "NODE_ENV": "production"
      }
    },
    "github": {
      "command": "npx", 
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "your_github_token"
      }
    },
    "postgres": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres", "postgresql://user:password@localhost/dbname"]
    }
  }
}
```

### ⚙️ **Advanced Configuration Options**

#### Debug Configuration
- Set `DEBUG=true` in environment for verbose logging
- Configure debug capture per session via API or UI
- Adjust debug event retention limits in `src/core/debug_capture.py`

#### RAG System Configuration  
- **Vector Index Settings:** Configure dimension, capacity, and similarity metrics
- **Chunk Size:** Adjust document chunking parameters for optimal retrieval
- **Embedding Model:** Switch between different embedding providers and models

#### Tool Configuration
- **Dynamic Loading:** Tools are automatically discovered from `src/tools/` directory
- **Runtime Enabling:** Tools can be enabled/disabled per session via API
- **Custom Tools:** Add new tools by implementing the `Tool` interface

#### Session Configuration
- **Session Timeout:** Configure automatic session cleanup
- **Memory Limits:** Set maximum conversation history per session  
- **Storage Backend:** Configure session persistence mechanisms

## Tools & Integrations

The AI Agent features an extensible tool system that enables interaction with various external services and data sources.

### 🧰 **Built-in Tools**

#### Core Tools
*   **`GoogleSearch`** - Performs web searches using Google Custom Search API
    - Real-time web search capabilities
    - Configurable result limits and filtering
    - Source citation and URL extraction

*   **`ReadFile`** - Reads content from local and remote files
    - Support for various file formats (text, markdown, JSON, etc.)
    - Path validation and security controls
    - Encoding detection and handling

*   **`WriteFile`** - Creates and updates files with content
    - Safe file writing with backup creation
    - Directory creation and permission handling
    - Content validation and formatting

*   **`ListFiles`** - Lists files and directories with filtering
    - Recursive directory traversal
    - Pattern matching and exclusion rules
    - File metadata and size information

#### Specialized Integrations
*   **`Context7`** - Integration with Context7 API for coding best practices
    - Automated code review and suggestions
    - Best practice recommendations
    - Language-specific guidance

*   **`GitHubKnowledgebase`** - Searches GitHub topics and repositories
    - Repository search and analysis
    - Issue and PR information retrieval
    - Code snippet extraction

### 🔗 **Model Context Protocol (MCP) Support**

The agent seamlessly integrates with MCP-compatible external services:

#### Supported MCP Servers
- **Filesystem Server** - File system operations with security controls
- **GitHub Server** - Repository management and code analysis  
- **Database Servers** - PostgreSQL, MySQL, and other database integrations
- **API Servers** - REST and GraphQL API interactions
- **Custom Servers** - Your own MCP-compatible tools and services

#### MCP Features
- **Automatic Discovery** - Tools are automatically detected and registered
- **Dynamic Loading** - MCP servers can be added without restarting
- **Error Handling** - Robust error handling with fallback mechanisms
- **Session Isolation** - MCP tools operate independently per session

### 🛠️ **Tool Development**

#### Creating Custom Tools

Tools are located in the `src/tools/` directory. Create new tools by implementing the `Tool` interface:

```python
from tools import Tool

class MyCustomTool(Tool):
    def __init__(self, name: str):
        super().__init__(name, "Description of what this tool does")
    
    async def execute(self, **kwargs):
        # Tool implementation
        return result
```

#### Tool Configuration
- **Runtime Management** - Enable/disable tools per session
- **Parameter Validation** - Automatic parameter validation using JSON schemas  
- **Error Handling** - Graceful error handling with user-friendly messages
- **Debugging** - Full debug tracing for tool calls and responses

#### Tool Discovery
- **Automatic Loading** - Tools are automatically discovered at startup
- **Dynamic Registration** - Tools can be registered at runtime
- **Dependency Management** - Handle tool dependencies and requirements
- **Versioning** - Support for tool versioning and compatibility

## RAG (Retrieval Augmented Generation)

The AI Agent includes a sophisticated RAG system that enhances responses with relevant information from a knowledge graph and vector embeddings.

### 🧠 **Knowledge Graph Architecture**

#### Memgraph Integration
- **Graph Database** - Uses Memgraph for storing complex document relationships
- **Vector Indexing** - Integrated vector search capabilities for semantic retrieval
- **Relationship Modeling** - Rich graph schema for document hierarchies and connections
- **Real-time Queries** - Fast graph traversal and pattern matching

#### Data Schema
The RAG system uses a comprehensive graph schema:

- **Documents** - Full documents with metadata and content
- **Document Chunks** - Segments optimized for embedding and retrieval  
- **Sources** - Origin information for documents (URLs, files, APIs)
- **Vectors** - High-dimensional embeddings for semantic search
- **Vector Stores** - Embedding storage with model metadata
- **Interactions** - Chat history and user interaction tracking

### 🔍 **Embedding & Search**

#### Text Embedding
- **Azure OpenAI Integration** - Using `text-embedding-3-small` model
- **Configurable Models** - Support for different embedding providers
- **Batch Processing** - Efficient batch embedding generation
- **Caching** - Smart caching to avoid redundant embedding calls

#### Similarity Search
- **Vector Search** - Fast approximate nearest neighbor search
- **Hybrid Retrieval** - Combining vector and graph-based retrieval
- **Ranking & Filtering** - Relevance scoring and result filtering
- **Context Assembly** - Intelligent context construction from retrieved chunks

### 📚 **Data Loading & Processing**

#### Supported Data Sources
- **Web Pages** - Automated web scraping and content extraction
- **Local Documents** - File system integration for various formats
- **APIs** - RESTful API data ingestion
- **Databases** - Direct database content integration

#### Processing Pipeline
- **Content Extraction** - Clean text extraction from various formats
- **Chunking Strategy** - Intelligent document segmentation
- **Metadata Enhancement** - Automatic metadata generation and enrichment
- **Quality Control** - Content validation and duplicate detection

### ⚙️ **Configuration & Customization**

#### RAG Configuration
```python
# Vector store configuration
VECTOR_STORE_CONFIG = {
    "model": "text-embedding-3-small",
    "dimension": 1536,
    "capacity": 1000000,
    "metric": "cosine"
}

# Retrieval settings
RETRIEVAL_CONFIG = {
    "max_chunks": 5,
    "similarity_threshold": 0.8,
    "context_window": 4000
}
```

#### Data Loader Scripts
- **`scripts/url_loader.py`** - Load content from web URLs
- **`scripts/doc_loader.py`** - Process local document collections  
- **`scripts/loader_config.py`** - Centralized loading configuration

## Contributing

We welcome contributions to the AI Agent project! Please follow these guidelines to ensure a smooth collaboration process.

### 🤝 **How to Contribute**

1.  **Fork the repository** and create your feature branch:
    ```bash
    git checkout -b feature/your-feature-name
    ```

2.  **Set up your development environment**:
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    pip install -r requirements.txt
    npm install  # For frontend development
    ```

3.  **Make your changes** following our coding standards and architecture patterns.

4.  **Run the full test suite** to ensure your changes don't break existing functionality:
    ```bash
    pytest --cov=src tests/
    npm run ui:test  # Frontend tests
    ```

5.  **Ensure code quality** by running our linting and formatting tools:
    ```bash
    black src tests
    isort src tests  
    pylint src tests
    mypy src
    ```

6.  **Commit your changes** with descriptive commit messages:
    ```bash
    git commit -m 'Add comprehensive session management with debug isolation'
    ```

7.  **Push to your branch** and create a Pull Request:
    ```bash
    git push origin feature/your-feature-name
    ```

### 📋 **Development Guidelines**

#### Code Quality Standards
- **Python 3.9+** compatibility required
- **Type hints** mandatory for all function parameters and return values
- **Docstrings** for public APIs (following our minimal comment guidelines)
- **Test coverage** of at least 80% for new features
- **Error handling** with graceful degradation

#### Architecture Principles
- **Modular design** - One domain per package structure
- **Session isolation** - All features must respect per-session boundaries
- **Asynchronous operations** - Use `asyncio` for I/O-bound operations
- **Dependency injection** - Avoid global state and tight coupling

#### Testing Requirements
- **Unit tests** for all business logic components
- **Integration tests** for API endpoints and external service interactions
- **Frontend tests** for UI components and user interactions
- **End-to-end tests** for critical user workflows

### 🎯 **Priority Areas for Contribution**

#### High Priority
- **Additional MCP Servers** - Integration with more external services
- **Alternative LLM Providers** - Support for OpenAI, Anthropic, and local models
- **Enhanced RAG Features** - Advanced retrieval strategies and ranking
- **Mobile UI Improvements** - Better mobile responsive design

#### Medium Priority  
- **Performance Optimizations** - Caching, lazy loading, and memory management
- **Security Enhancements** - Authentication, authorization, and input validation
- **Documentation** - API documentation, tutorials, and examples
- **Monitoring & Analytics** - Advanced metrics and observability features

#### Nice to Have
- **Plugin System** - Dynamic tool loading and management
- **Multi-language Support** - Internationalization and localization
- **Advanced Visualization** - Enhanced debug and data visualization
- **Deployment Tools** - Docker, Kubernetes, and cloud deployment scripts

### 🐛 **Reporting Issues**

When reporting bugs or requesting features:

1.  **Search existing issues** to avoid duplicates
2.  **Use our issue templates** for consistent reporting
3.  **Provide detailed information** including:
    - Steps to reproduce the issue
    - Expected vs actual behavior  
    - Environment details (OS, Python version, etc.)
    - Debug logs and error messages
    - Screenshots for UI issues

### 📖 **Development Resources**

- **Architecture Documentation** - See `docs/architecture.md`
- **API Reference** - Available at `/docs` when running in API mode
- **ADRs** - Architecture Decision Records in `docs/ADRs/`
- **Examples** - Working examples in the `examples/` directory
- **Test Suite** - Comprehensive tests in the `tests/` directory

## License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.

## API Documentation

The AI Agent provides a comprehensive REST API built with FastAPI, featuring automatic OpenAPI documentation and robust session management.

### 🔌 **Core API Endpoints**

#### Session Management
- `POST /api/session/new` - Create a new conversation session
- `DELETE /api/session/{session_id}` - Delete a session and cleanup resources

#### Chat & Interaction  
- `POST /api/{session_id}/ask` - Send a message and get AI response
- `GET /api/{session_id}/tools` - List available tools for the session
- `POST /api/{session_id}/tools/toggle` - Enable/disable specific tools

#### Debug & Monitoring
- `GET /api/{session_id}/debug` - Retrieve debug events for the session
- `POST /api/{session_id}/debug/toggle` - Enable/disable debug mode
- `DELETE /api/{session_id}/debug` - Clear debug events for the session

### 🔐 **Authentication**

API endpoints (except session creation) require authentication via API key:

```bash
curl -H "X-API-Key: your_secure_api_key_here" http://localhost:5555/api/{session_id}/ask
```

Configure your API key in the `.env` file:
```bash
API_KEY=your_secure_api_key_here
```

### 📊 **Session Isolation**

Each session maintains:
- **Independent conversation history** and context
- **Separate tool configurations** and states  
- **Isolated debug events** and monitoring data
- **Individual agent instances** with per-session memory

### 🔧 **Interactive API Documentation**

When running in API mode, visit `http://localhost:5555/docs` for:
- **Swagger UI** with interactive API testing
- **Complete endpoint documentation** with request/response schemas
- **Authentication testing** capabilities
- **Real-time API exploration** and validation

## Debug & Monitoring

The AI Agent includes a comprehensive debugging and monitoring system designed for development, troubleshooting, and performance analysis.

### 🐛 **Per-Session Debug System**

#### Session Isolation
- **Independent Debug State** - Each session maintains its own debug configuration
- **Isolated Event Capture** - Debug events are tracked separately per session
- **State Persistence** - Debug settings persist across session switches and browser reloads
- **Memory Management** - Automatic cleanup when sessions are deleted

#### Event Capture
- **LLM Interactions** - Complete request/response logging for language model calls
- **Tool Execution** - Detailed logging of tool calls, parameters, and results
- **MCP Communication** - Model Context Protocol message tracing
- **Error Tracking** - Comprehensive error logging with stack traces

### 📊 **Debug Panel Features**

#### Real-time Visualization
- **Color-coded Events** - Different event types highlighted with distinct colors
- **Timeline View** - Chronological event ordering with timestamps
- **Expandable Details** - Click-to-expand for detailed event inspection
- **Fullscreen Mode** - Dedicated fullscreen viewer for complex data analysis

#### Event Management
- **Live Updates** - Real-time event streaming without page refresh
- **Event Filtering** - Filter by event type, timestamp, or content
- **Search Capability** - Full-text search across all captured events
- **Export Functionality** - Export debug data for external analysis

### 🎛️ **Debug Controls**

#### Session-Level Controls
- **Debug Toggle** - Enable/disable debug capture per session
- **Auto-Enable** - Automatic debug activation when panel is opened
- **Manual Control** - Independent debug state management
- **Clear Events** - Remove all debug events for a session

#### Developer Tools
- **API Endpoints** - RESTful API for debug data access and control
- **Programmatic Access** - Python API for debug system integration
- **Custom Event Types** - Support for application-specific debug events
- **Event Hooks** - Extensible event capture system

### 📈 **Performance Monitoring**

#### Metrics Collection
- **Response Times** - LLM and tool execution timing
- **Token Usage** - Language model token consumption tracking
- **Memory Usage** - Session memory and resource utilization
- **Error Rates** - Failure rate monitoring and analysis

#### Performance Analysis
- **Bottleneck Identification** - Automatic performance issue detection
- **Trend Analysis** - Historical performance data and trends
- **Resource Optimization** - Recommendations for performance improvements
- **Capacity Planning** - Usage analytics for scaling decisions

### 🔧 **Configuration & Customization**

#### Debug Configuration
```python
# Debug system settings
DEBUG_CONFIG = {
    "max_events_per_session": 1000,
    "event_retention_hours": 24,
    "auto_enable_on_panel_open": True,
    "capture_sensitive_data": False
}
```

#### Integration Examples
```python
# Custom debug event capture
from core.debug_capture import get_debug_capture_instance

debug_capture = get_debug_capture_instance(session_id)
debug_capture.capture_event(
    event_type="custom_operation",
    message="Custom operation completed",
    data={"operation": "data_processing", "duration": 1.5}
)
```
