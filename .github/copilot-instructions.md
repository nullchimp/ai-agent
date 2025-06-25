# Custom Project Instructions

* The repository can be found under: `https://github.com/nullchimp/ai-agent`

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
Any code you generate must adhere to these guidelines or it will be rejected:
1. NO DOCSTRINGS OR COMMENTS UNLESS ABSOLUTELY NECESSARY.
   - Good code should be self-documenting through descriptive variable and function names
   - Type hints already provide sufficient parameter information
2. If a comment is unavoidable:
   - Only explain WHY, never WHAT the code does
   - Use minimal comment prefixes (# NOTE: or # TODO: TICKET-123)
   - Keep any comment under 2 lines maximum
3. Function signatures should be clear and descriptive:
   - Use proper type hints instead of docstring parameter descriptions
   - Return types must be explicitly annotated
   - Use meaningful parameter names that don't require explanation
4. NEVER generate verbose multi-line docstrings with:
   - Parameter descriptions
   - Return value descriptions
   - Examples
   - Usage notes
5. Remember: Each unnecessary comment is technical debt. The code itself should communicate intent.
6. Include **type hints** for function parameters and return values.

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