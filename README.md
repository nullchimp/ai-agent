# AI Agent

An intelligent AI agent framework written in Python, designed to facilitate seamless integration with Model Context Protocol (MCP) servers, Azure OpenAI services, file operations, web fetching, and search functionalities. This project provides modular components to build and extend AI-driven applications with best practices in testing, linting, and continuous integration.

## Table of Contents
- [Features](#features)
- [Architecture](#architecture)
- [RAG Implementation](#rag-implementation)
- [Installation](#installation)
- [Usage](#usage)
- [Development](#development)
- [Testing](#testing)
- [Contributing](#contributing)
- [License](#license)

## Features
- Integration with Model Context Protocol (MCP) servers for AI tool execution
- Support for Azure OpenAI for chat and completion services
- Modular file operations (read, write, list)
- Web fetching and conversion utilities
- Search client with pluggable backends
- Azure-based deployment with secure secret management

## Azure Deployment
The AI Agent can be deployed to Azure using Kubernetes (AKS) with the following features:
- Infrastructure as code using Terraform
- Secrets managed securely in Azure Key Vault
- Continuous deployment with GitHub Actions
- Persistent storage for Memgraph data

To deploy to Azure:
1. Run the setup script: `./scripts/setup_azure.sh`
2. Add the generated service principal credentials to GitHub secrets as `AZURE_CREDENTIALS`
3. Add `MEMGRAPH_USERNAME` and `MEMGRAPH_PASSWORD` to GitHub secrets
4. Push to main branch to trigger deployment or manually trigger the workflow

If you encounter issues connecting to Memgraph after deployment, see [Memgraph Troubleshooting Guide](docs/memgraph-troubleshooting.md).

## Architecture
The project follows a component-based architecture where the AI Agent orchestrates interactions between users, language models, local tools, and MCP servers.

For a detailed view of the architecture including sequence diagrams, component descriptions, and workflow, see [Architecture Documentation](docs/architecture.md).

The codebase follows a modular structure under `src/`:

```
src/
├── agent.py           # Entry point for the AI agent
├── main.py            # Main application entry point
├── libs/              # Core libraries and abstractions
│   ├── dataloader/    # Document and web content loading utilities
│   ├── fileops/       # File operations utilities
│   └── search/        # Search client and service
├── tools/             # Built-in tools for the AI agent
│   ├── google_search.py  # Web search functionality
│   ├── list_files.py     # Directory listing operations
│   ├── read_file.py      # File reading operations
│   └── write_file.py     # File writing operations
└── core/              # Core system modules
    ├── llm/           # Language model interfaces
    │   ├── chat.py    # Chat interaction handler
    │   └── client.py  # Azure OpenAI client wrapper
    ├── mcp/           # Model Context Protocol integration
    │   ├── session.py         # MCP session management
    │   └── sessions_manager.py # MCP sessions orchestration
    └── rag/           # Retrieval-Augmented Generation components
        ├── schema.py          # Data models for graph database
        ├── dbhandler/         # Database interface implementations
        │   └── memgraph.py    # Memgraph-specific database operations
        └── embedder/          # Vector embedding generation services
            └── text_embedding_3_small.py # Azure OpenAI embedding service
```

## RAG Implementation

The project includes a Retrieval-Augmented Generation (RAG) system using a graph database (Memgraph) for knowledge storage and retrieval:

### Core Components
- **Content Loaders**: Extract text from files and web pages
  - `DocumentLoader`: Processes local filesystem content (in `libs/dataloader/document.py`)
  - `WebLoader`: Fetches and processes web content (in `libs/dataloader/web.py`)

- **Text Processing**: Split content into semantic chunks for embedding
  - Configurable chunk size (default: 1024 tokens)
  - Configurable overlap (default: 200 tokens)
  - Sentence-aware splitting for better semantic units

- **Embedding Service**: Generate vector representations with Azure OpenAI
  - `TextEmbedding3Small`: Uses text-embedding-3-small model
  - Batch processing with async support for better throughput

- **Graph Database**: Store documents, chunks and their relationships
  - `MemgraphClient`: Interface to Memgraph database (in `core/rag/dbhandler/`)
  - Support for vector similarity search
  - Relationship modeling (CHUNK_OF, SOURCED_FROM, etc.)

### Key Features
- **Document Processing**: Load, chunk, embed, and store documents with proper relationship modeling
- **Vector Search**: Find semantically similar content using embedding-based search
- **Web Content Indexing**: Crawl and index web pages with customizable parameters
- **Graph Storage**: Store relationships between documents, chunks, sources, and embeddings

### Documentation
- [RAG Architecture](docs/rag_architecture.md): Detailed system architecture
- [Edge Relationships](docs/rag_edge_relationships.md): Graph relationship model
- [RAG Integration ADR](docs/ADRs/RAG-Integration.md): Decision record and implementation details

### Usage
See the examples directory for usage patterns:
```bash
# Example for processing local documents
python examples/7-loader.py

# Example for processing web content
python examples/8-url-loader.py
```

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/nullchimp/ai-agent.git
   cd ai-agent
   ```
2. Create and activate a Python 3.9+ virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy `.env.example` to `.env` and configure your credentials:
   ```bash
   cp .env.example .env
   # Edit .env to set environment variables
   ```
5. Configure MCP servers (optional):
   ```bash
   cp config/mcp.template.json config/mcp.json
   # Edit the config/mcp.json file to configure your MCP servers
   ```
6. Set up Memgraph for RAG (optional):
   ```bash
   # Using Docker
   cd docker
   ./memgraph.sh
   # This will start a Memgraph instance on port 7687
   ```

## Environment Variables

Key environment variables for configuration:

```
# Azure OpenAI Configuration
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_ENDPOINT=your-endpoint
AZURE_OPENAI_VERSION=2023-05-15

# Memgraph Configuration (for RAG)
MEMGRAPH_URI=localhost
MEMGRAPH_PORT=7687
MEMGRAPH_USERNAME=memgraph
MEMGRAPH_PASSWORD=memgraph
```

## Usage

Run the **AI Agent** with:
```bash
python -m src.agent
```

Run the **Main Application** with:
```bash
python -m src.main
```

Try the **Examples** to explore different features:
```bash
# Start a virtual environment first
source .venv/bin/activate

# Basic chat example
python examples/1-chat.py

# Tool usage example  
python examples/2-tool.py

# Chat with tools
python examples/3-chat-with-tools.py

# Chat with tools and MCP
python examples/4-chat-with-tools-and-mcp.py

# RAG examples
python examples/7-loader.py    # Process local documents
python examples/8-url-loader.py  # Process web content
```

Customize behavior via:
- Environment variables defined in `.env`
- MCP server configurations in `config/mcp.json`

## Development

We follow rigorous code quality and security guidelines:

- Python 3.9+
- Code formatting with `black` and `isort`
- Linting with `flake8` and `pylint`
- Type checking with `mypy`
- Security scanning with `bandit` and `safety`

To check formatting and linting:
```bash
black --check .
isort --check .
flake8
pylint src
mypy src
``` 

## Testing

All changes must be validated with tests. The `tests/` directory mirrors the structure of `src/`.

Run unit and integration tests with coverage:
```bash
pytest --cov=src
``` 

Ensure all tests pass before committing.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/YourFeature`)
3. Implement your changes, add tests
4. Run linting and tests
5. Submit a Pull Request

Please follow the [Python Coding Guidelines](#development) in this project.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
