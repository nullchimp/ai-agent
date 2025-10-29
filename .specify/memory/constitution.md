<!--
  SYNC IMPACT REPORT
  ==================
  Version Change: Template → 1.0.0
  
  Modified Principles:
  - PRINCIPLE_1_NAME → I. Modular Architecture & Separation of Concerns
  - PRINCIPLE_2_NAME → II. Code Readability & Self-Documentation
  - PRINCIPLE_3_NAME → III. Test-First Development (NON-NEGOTIABLE)
  - PRINCIPLE_4_NAME → IV. Type Safety & Static Analysis
  - PRINCIPLE_5_NAME → V. Python Best Practices
  
  Added Sections:
  - Core Principles (5 principles defined)
  - Security & Quality Standards
  - Development Workflow & Review Process
  - Governance
  
  Templates Requiring Updates:
  ✅ plan-template.md - Reviewed, constitution check section aligns
  ✅ spec-template.md - Reviewed, requirements and acceptance criteria align
  ✅ tasks-template.md - Reviewed, test-first and phase structure aligns
  ✅ coding-guidelines.instructions.md - Source of truth for principles
  
  Follow-up TODOs: None - all principles fully defined
  
  Rationale for Version 1.0.0:
  - Initial ratification of constitution from template
  - Establishes foundational governance for AI Agent project
  - All principles and sections are now concrete and actionable
-->

# AI Agent Constitution

## Core Principles

### I. Modular Architecture & Separation of Concerns

Every component in the AI Agent project MUST adhere to strict modularity and separation of concerns:

- **One domain = one package**: Each logical domain (e.g., `llm`, `rag`, `tools`, `api`) MUST reside in its own package under `src/<domain>`
- **Single Responsibility Principle**: Each module, class, and function MUST have exactly one reason to change
- **Clear boundaries**: Domain packages MUST expose well-defined interfaces and MUST NOT leak implementation details
- **Dependency direction**: Dependencies MUST flow inward toward core business logic; outer layers (API, UI) depend on inner layers (services, models), never vice versa
- **Isolated side effects**: Pure business logic MUST be separated from side effects (I/O, database, external APIs) which belong in service layers

**Rationale**: Modular architecture enables independent development, testing, and evolution of components. It reduces coupling, improves maintainability, and allows teams to work in parallel without conflicts.

### II. Code Readability & Self-Documentation

Code MUST be written to be immediately understandable by humans without requiring extensive comments:

- **Descriptive naming**: Variable, function, and class names MUST clearly express intent and purpose
  - Classes: PascalCase (e.g., `SessionManager`, `DebugCapture`)
  - Functions/variables: snake_case (e.g., `capture_event`, `session_id`)
  - Constants: ALL_CAPS (e.g., `MAX_EVENTS_PER_SESSION`)
- **Type hints required**: All function parameters and return values MUST include type hints for clarity and tool support
- **Self-explanatory structure**: Code structure and flow MUST convey logic; avoid "clever" code that requires explanation
- **Minimal comments**: Comments explain WHY decisions were made, not WHAT code does; if code needs WHAT comments, refactor for clarity
- **Comment discipline**: Comments MUST be under 2 lines; use `# NOTE:` or `# TODO: <ticket-id>` prefixes; delete expired comments

**Rationale**: Self-documenting code reduces cognitive load, speeds up onboarding, and prevents documentation drift. Type hints enable better IDE support and catch errors early.

### III. Test-First Development (NON-NEGOTIABLE)

Testing MUST drive implementation through strict Test-Driven Development:

- **Red-Green-Refactor cycle**: Tests MUST be written first, verified to fail, then implementation makes them pass, followed by refactoring
- **Test location**: All tests MUST be placed in the `tests/` folder at repository root, never co-located with source
- **Test coverage**: Unit tests required for all business logic; integration tests required for I/O boundaries (API endpoints, database, external services)
- **Coverage gate**: CI MUST enforce minimum 80% code coverage; uncovered code MUST be explicitly justified
- **Test categories**:
  - **Unit tests**: Pure functions, business logic, algorithms (`tests/unit/`)
  - **Integration tests**: API endpoints, database operations, MCP sessions (`tests/integration/`)
  - **Contract tests**: External API interfaces and protocol compliance (`tests/contract/`)
- **Test execution**: Use `pytest --cov=src` for all test runs; tests MUST pass before any code merge

**Rationale**: Test-first development catches bugs before they exist, documents intended behavior, enables confident refactoring, and ensures every line of code has proven value.

### IV. Type Safety & Static Analysis

All Python code MUST pass strict static analysis without warnings:

- **Type checking**: `mypy` MUST run in strict mode with no type errors; use `# type: ignore[specific-error]` only with justification comment
- **Linting**: `pylint` and `flake8` MUST pass without warnings; configure exceptions in `pyproject.toml` only when justified
- **Code formatting**: `black` and `isort` MUST auto-format all code; 88 characters max line length; 4-space indentation
- **Pre-commit hooks**: All quality tools (black, isort, mypy, pylint, flake8) MUST run before commits
- **CI enforcement**: Pull requests MUST fail if any static analysis tool reports warnings or errors
- **Validation framework**: Use Pydantic models for all external input validation (API requests, environment variables, configuration files)

**Rationale**: Static analysis prevents entire classes of bugs before runtime, improves code quality, and provides better IDE support. Type safety documentation becomes executable and verified.

### V. Python Best Practices

All code MUST follow Python idioms and modern best practices:

- **Python version**: Target Python 3.9+ for all features and dependencies
- **Virtual environments**: Always use isolated virtual environments; never install packages globally
- **Dependency management**: Pin exact versions in `requirements.txt`; regularly update and audit dependencies
- **Async/await**: Use `asyncio` for I/O-bound operations (API calls, database queries, file I/O)
- **Error handling**: Prefer specific exceptions over generic; always provide context in error messages; use structured logging
- **Resource management**: Use context managers (`with` statements) for file handles, database connections, and locks
- **Data classes**: Use `dataclasses`, `Pydantic`, or `attrs` for data containers; avoid dictionaries for structured data
- **Configuration**: Load from environment variables (via `.env`); never hard-code secrets or configuration
- **Logging**: Use structured logging with proper levels (DEBUG, INFO, WARNING, ERROR); include context (session_id, user_id, etc.)

**Rationale**: Consistent Python idioms make code predictable and maintainable. Modern features (async, type hints, data classes) improve performance and developer experience.

## Security & Quality Standards

### Security Requirements

All code MUST adhere to security best practices:

- **No hard-coded secrets**: API keys, passwords, tokens MUST be loaded from environment variables or secrets manager
- **Input validation**: All external input (API requests, file uploads, user input) MUST be validated using Pydantic models or similar
- **Secure communications**: HTTPS required for all external communications; verify TLS certificates
- **Authentication**: API endpoints MUST enforce authentication via API keys; protected routes MUST verify JWTs
- **Security scanning**: CI MUST run security tools (`bandit`, `Safety`, Dependabot) and fail on critical CVEs
- **Audit logging**: Security events (authentication, authorization failures, data access) MUST be logged with sufficient detail

### Quality Gates

Before any merge to main branch:

- **All tests pass**: Unit, integration, and contract tests MUST succeed
- **Coverage threshold**: Minimum 80% code coverage achieved
- **Static analysis clean**: mypy, pylint, flake8 report zero warnings
- **Security scan clean**: No critical or high-severity vulnerabilities
- **Code formatting**: All code formatted with black and isort
- **Documentation updated**: README, docstrings, and architecture docs reflect changes

## Development Workflow & Review Process

### Code Review Requirements

All pull requests MUST undergo code review before merge:

- **Constitution compliance**: Reviewer MUST verify adherence to all principles in this constitution
- **Test verification**: Reviewer MUST verify tests were written first and originally failed
- **Architecture alignment**: Changes MUST align with modular architecture and separation of concerns
- **Naming review**: Variable, function, and class names MUST be clear and descriptive
- **Documentation**: Changes requiring documentation updates MUST include those updates in the same PR

### Complexity Justification

Any violation of constitution principles MUST be explicitly justified:

- **Document in plan**: Complexity justification MUST appear in `specs/[feature]/plan.md`
- **Alternative considered**: Justification MUST explain why simpler alternatives were rejected
- **Review approval**: Complexity violations require explicit approval from senior developers
- **Technical debt tracking**: Violations MUST be tracked as technical debt with a remediation plan

### Branch Strategy

- **Main branch protection**: Direct commits to `main` forbidden; all changes via pull requests
- **Feature branches**: Use format `###-feature-name` aligned with specification documents
- **Commit discipline**: Commit after each logical unit of work (typically one task from `tasks.md`)

## Governance

### Constitutional Authority

This constitution supersedes all other development practices and guidelines:

- **Precedence**: In case of conflict between this constitution and other documents, constitution takes precedence
- **Mandatory compliance**: All code changes, regardless of urgency, MUST comply with constitutional principles
- **No exceptions without documentation**: Any exception MUST be documented and justified in the feature's `plan.md`

### Amendment Process

Amendments to this constitution require:

1. **Proposal document**: Written proposal explaining the change, rationale, and impact
2. **Impact analysis**: Assessment of changes required in codebase and existing specifications
3. **Team review**: Discussion and consensus among development team
4. **Migration plan**: For breaking changes, a clear migration path for existing code
5. **Version update**: Semantic versioning applied to constitution version
6. **Template propagation**: Update all affected templates (plan, spec, tasks) to align with amendments

### Versioning Policy

Constitution versions follow semantic versioning (MAJOR.MINOR.PATCH):

- **MAJOR**: Backward-incompatible changes (principle removals, redefinitions that invalidate existing code)
- **MINOR**: New principles or sections added, material expansions to existing principles
- **PATCH**: Clarifications, wording improvements, typo fixes, non-semantic refinements

### Compliance Review

- **Every pull request**: Reviewer MUST verify constitutional compliance
- **Quarterly audits**: Conduct quarterly reviews of codebase for constitutional drift
- **Metrics tracking**: Track metrics on test coverage, static analysis violations, security issues
- **Continuous improvement**: Use metrics to identify areas for process improvement

### Runtime Guidance

For day-to-day development guidance and practical implementation details, developers SHOULD reference:

- **Coding guidelines**: `.github/instructions/coding-guidelines.instructions.md`
- **Architecture documentation**: `docs/architecture.md`
- **Architecture Decision Records**: `docs/ADRs/` for historical context on technical decisions
- **Template files**: `.specify/templates/*.md` for specification and planning workflows

**Version**: 1.0.0 | **Ratified**: 2025-10-29 | **Last Amended**: 2025-10-29
