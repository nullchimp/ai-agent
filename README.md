# AI Agent

An intelligent AI agent framework written in Python, designed to facilitate seamless integration with Azure OpenAI services, file operations, web fetching, and search functionalities. This project provides modular components to build and extend AI-driven applications with best practices in testing, linting, and continuous integration.

## Table of Contents
- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Usage](#usage)
- [Development](#development)
- [Testing](#testing)
- [Contributing](#contributing)
- [License](#license)

## Features
- Integration with Azure OpenAI for chat and completion services
- Modular file operations (read, write, list)
- Web fetching and conversion utilities
- Search client with pluggable backends
- Tooling for codegen workflows
- Configurable via environment variables

## Architecture
The codebase follows a modular structure under `src/`:

```
src/
├── agent.py           # Entry point for the AI agent
├── libs/              # Core libraries and abstractions
│   ├── azureopenai/   # Azure OpenAI wrappers (chat, client)
│   ├── fileops/       # File operations utilities
│   ├── search/        # Search client and service
│   └── webfetch/      # Web fetching and conversion services
└── tools/             # Command-line tools for file and web operations
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
   source .venv/bin/activate  # On Windows: .venv\\Scripts\\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy `.env.example` to `.env` and configure your Azure OpenAI credentials:
   ```bash
   cp .env.example .env
   # Edit .env to set environment variables
   ```

## Usage

Run the **AI Chat** with:
```bash
python -m src.chat
```

Run the **AI Agent** with:
```bash
python -m src.agent
```

Customize behavior via environment variables defined in `.env`.

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

All changes must be validated with tests.

Run unit and integration tests with coverage:
```bash
pytest --cov=src
``` 

Ensure 100% pass before committing.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/YourFeature`)
3. Implement your changes, add tests
4. Run linting and tests
5. Submit a Pull Request

Please follow the [Python Coding Guidelines](#development) in this project.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
