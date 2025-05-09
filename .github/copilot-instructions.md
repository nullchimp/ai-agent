# Custom Project Instructions

* The repository can be found under: `https://github.com/nullchimp/ai-agent`
* Context7 should be used to get coding best practices for Python
* Every change that you make needs to be validated with tests.
* You have to execute all tests and they need to pass before finishing the implementation.
* Always create a virtual environment before executing any Python code.

## Folder Responsibilities
* `.github` - Houses GitHub prompts (.github/prompts/), workflows(.github/workflows/), and Copilot instructions. Used by GitHub Actions and Copilot Chat.
* `tests` - Contains all tests for the application
* Root files
    * .env – environment variables (managed via GitHub and Context7 MCP Servers)
    * README.md, LICENSE – project overview and licensing

# Python Coding Guidelines — AI-Friendly Cheat-Sheet

## Code Quality
- Use **Python 3.9+**; follow **semantic versioning** (`vX.Y.Z`).
- CI must pass **`pylint`**, **`flake8`**, **`mypy`**, and **`black`** checks.
- Follow **modular design**: One domain = one package (`src/<domain>`). Files: `service.py`, `routes.py`.
- Auto-format with **`black`** and **`isort`**; imports ordered:
  1. _stdlib
  2. third-party
  3. local_.
- **4-space indentation**, less than 88-char lines (Black default), functions less than 50 lines, single responsibility.
- Prefer **pure functions**; use dependency injection and keep side-effects isolated.
- Always use **virtual environments** for project isolation:
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate  # On Windows: venv\Scripts\activate
  pip install -r requirements.txt
  ```

## Docs & Comments
- Include **type hints** for function parameters and return values.
- Explain **why**, not **what**. Use `# NOTE:` or `# TODO: TICKET-123`.
- Update docs in the **same PR** as code changes.

## Security
- **No hard-coded secrets** (load from env or a secrets manager).
- **Validate all input**; use dataclasses, Pydantic, or attrs for data validation.
- Run **`bandit`**, **Safety**, **CodeQL**, **Dependabot**; fail build on critical CVEs.
- Use **HTTPS** for external communications and verify **JWTs** on protected routes.

## Testing & CI/CD
- **Unit-test** logic with pytest, **integration-test** I/O boundaries.
- Run `pytest --cov=src` and check coverage in CI.
- Always activate virtual environment in CI pipelines:
  ```yaml
  - name: Set up Python
    run: |
      python3 -m venv .venv
      source .venv/bin/activate
  ```