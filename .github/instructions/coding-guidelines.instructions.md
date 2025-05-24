---
applyTo: "*.py"
---

# High-Level Coding Best Practices
* Use **Python 3.9+** with strict type hints enabled
* Follow modular design pattern: one domain = one package (`src/<domain>`)
* Descriptive names – PascalCase for classes, snake_case for functions/variables, ALL_CAPS for constants
* Alphabetical, grouped imports (stdlib, third-party, local); 4-space indentation; max 88-char lines
* Keep functions less than 50 lines and follow single-responsibility principle
* Prefer pure functions; isolate side-effects to service layer
* Fail CI on type-checker (mypy), linter (pylint, flake8), formatter (black) warnings

# Documentation & Comment Guidelines
* Code should be self-documenting with descriptive variable and function names
* Type hints required for function parameters and return values
* Comments explain WHY, not WHAT; delete when they expire
* Inline comments sparingly, prefixed with # NOTE: or # TODO: and a ticket ID
* Keep any comment under 2 lines maximum
* Update documentation in the same PR as code changes

# Security Best Practices
* No hard-coded credentials: read from environment variables or a secrets manager
* Use dataclasses, Pydantic, or attrs for data validation of external inputs
* Remove debug or "unsecure" code paths before deployment
* Run security scans: bandit, Safety, CodeQL, Dependabot
* Enforce HTTPS for external communications and verify JWTs on protected routes
* Pin and auto-update dependencies; fail builds on critical CVEs 

# Testing & CI/CD Essentials
* Use pytest for unit tests (business logic) and integration tests (I/O boundaries)
* Run pytest with coverage checks: `pytest --cov=src`
* Always use virtual environments for project isolation
* Pre-commit hooks: black, isort, mypy, pylint, flake8, tests, security scan
* Context7 MCP Server for model orchestration and evaluation
* Require passing tests and security scans before merge