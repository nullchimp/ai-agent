# AI Agent

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)

An advanced AI agent capable of performing tasks, answering questions, and interacting with various tools and data sources. This project leverages Large Language Models (LLMs), Retrieval Augmented Generation (RAG), and a flexible tool integration system.

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

*   **Conversational AI:** Engage in natural language conversations.
*   **Tool Usage:** Utilize a variety of tools to perform actions like web searches, file operations, and more.
*   **Retrieval Augmented Generation (RAG):** Enhance responses with information retrieved from a knowledge graph (Memgraph) and vector embeddings.
*   **Model Context Protocol (MCP):** Integrate with external tools and services that adhere to the MCP standard.
*   **Modular Design:** Easily extendable with new tools, data sources, and functionalities.
*   **Asynchronous Operations:** Built with `asyncio` for efficient I/O-bound tasks.

## Architecture

The AI Agent's architecture is designed for modularity and scalability. Key components include:

*   **Agent Core (`src/agent.py`):** Orchestrates the conversation flow and tool interactions.
*   **LLM Services (`src/core/llm/`):** Manages communication with Large Language Models.
*   **RAG System (`src/core/rag/`):** Implements retrieval augmented generation using a graph database (Memgraph) and vector embeddings for contextual knowledge.
    *   See [RAG Architecture](./docs/rag_architecture.md) for details.
*   **MCP Integration (`src/core/mcp/`):** Handles discovery and communication with MCP-compatible tools.
*   **Libraries (`src/libs/`):** Reusable modules for data loading, file operations, etc.
*   **Tools (`src/tools/`):** A collection of callable tools that the agent can use.

For a detailed overview, please refer to the [Project Architecture Document](./docs/architecture.md).

## Project Structure

The project is organized as follows:

```
ai-agent/
├── .github/                # GitHub Actions workflows and issue templates
│   ├── prompts/            # Prompts for GitHub Copilot
│   └── workflows/          # CI/CD workflows
├── config/                 # Configuration files
│   └── mcp.json            # MCP server configurations
├── docs/                   # Project documentation
│   ├── ADRs/               # Architecture Decision Records
│   ├── architecture.md     # Main architecture overview
│   ├── rag_architecture.md # RAG system details
│   └── ...                 # Other documentation files
├── src/                    # Source code
│   ├── agent.py            # Main agent logic
│   ├── main.py             # Application entry point
│   ├── core/               # Core components (LLM, RAG, MCP, utils)
│   │   ├── llm/
│   │   ├── rag/
│   │   ├── mcp/
│   │   └── ...
│   ├── libs/               # Reusable libraries (dataloader, fileops)
│   │   ├── dataloader/
│   │   └── ...
│   └── tools/              # Agent tools (google_search, file_io, etc.)
│       └── ...
├── tests/                  # Unit and integration tests
│   └── ... 
├── .env.example            # Example environment variables file
├── .gitignore              # Files to ignore in Git
├── LICENSE                 # Project license (MIT)
├── README.md               # This file
├── requirements.txt        # Python dependencies
└── ...                     # Other project files (linters, formatters config)
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

To run the agent:

```bash
python src/main.py
```

This will start the agent, and it will typically enter a loop to listen for user input or perform tasks based on its configuration.

## Configuration

*   **Environment Variables (`.env`):** API keys, service endpoints (e.g., Memgraph host/port), and other sensitive configurations.
*   **MCP Configuration (`config/mcp.json`):** Defines connection details for external tools and services that follow the Model Context Protocol.

## Tools

The agent can be equipped with various tools to extend its capabilities. Current tools include:

*   `GoogleSearch`: Performs web searches using Google.
*   `ReadFile`: Reads content from files.
*   `WriteFile`: Writes content to files.
*   `ListFiles`: Lists files in a directory.
*   `Context7`: Interacts with the Context7 API (e.g., for coding best practices).

Tools are located in the `src/tools/` directory. New tools can be added by creating a new Python file in this directory and implementing the `Tool` interface (see `src/tools/__init__.py`).

## Contributing

Contributions are welcome! Please follow these steps:

1.  Fork the repository.
2.  Create a new branch (`git checkout -b feature/your-feature-name`).
3.  Make your changes and commit them (`git commit -m 'Add some feature'`).
4.  Ensure your code adheres to the project's coding standards (run `black .`, `isort .`, `pylint src tests`, `mypy src`).
5.  Write tests for your changes and ensure all tests pass (`pytest`).
6.  Push to the branch (`git push origin feature/your-feature-name`).
7.  Create a new Pull Request.

Please read `CONTRIBUTING.md` (if available) for more detailed guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.
