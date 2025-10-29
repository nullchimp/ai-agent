# Implementation Plan: Database-Backed Session Storage

**Branch**: `001-session-storage` | **Date**: 2025-10-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-session-storage/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Move individual user sessions from in-memory dictionary storage (`_agent_sessions` in `agent.py` and `_debug_sessions` in `debug_capture.py`) to persistent database-backed storage using Memgraph. This ensures session state (conversation history, tool configurations, debug events) survives server restarts and enables multi-user scenarios with proper session isolation. The implementation will maintain an in-memory cache for performance while using the database as the source of truth, with automatic synchronization between frontend localStorage and backend database.

## Technical Context

**Language/Version**: Python 3.9+  
**Primary Dependencies**: FastAPI, Memgraph (graph database in Docker), mgclient (Memgraph Python driver)  
**Storage**: Memgraph graph database (running in Docker via docker-compose.yml)  
**Testing**: pytest with --cov=src, unit tests in tests/unit/, integration tests in tests/integration/  
**Target Platform**: Linux/macOS server (local development), containerized deployment (Docker)  
**Project Type**: Web application (backend API + frontend)  
**Performance Goals**: Session save <200ms, session restore <500ms, support 100+ concurrent sessions  
**Constraints**: Database must be available for writes, graceful degradation if DB connection fails (continue with in-memory), session data must be atomic (no partial saves)  
**Scale/Scope**: Multi-user system, 1000s of sessions, conversation histories up to 100 messages, debug events up to 1000 per session

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Modular Architecture & Separation of Concerns ✅
- **Pass**: Session storage logic is already modularized in `src/core/db/session.py` with clear domain boundaries
- **Pass**: Session schema defined in `src/core/db/schemas/session_objects.py` following single responsibility
- **Pass**: Separation between in-memory cache (agent.py) and persistence layer (db/session.py) is clear

### II. Code Readability & Self-Documentation ✅
- **Pass**: Existing code uses descriptive naming (Session, DebugCapture, conversation_history, session_id)
- **Pass**: Type hints are present throughout (e.g., `List[Dict[str, Any]]`, `Optional[str]`)
- **Pass**: Functions are self-explanatory (save_session_state, restore_session_state, get_session_by_id)

### III. Test-First Development (NON-NEGOTIABLE) ⚠️
- **Action Required**: Tests must be written FIRST for all new database operations
- **Action Required**: Integration tests required for session persistence across server restarts
- **Action Required**: Unit tests required for session synchronization logic
- **Target**: Maintain 80% code coverage minimum

### IV. Type Safety & Static Analysis ✅
- **Pass**: Existing codebase uses type hints consistently
- **Pass**: Pydantic models used for API validation (NewSessionResponse)
- **Action Required**: Ensure all new code passes mypy --strict, pylint, flake8

### V. Python Best Practices ✅
- **Pass**: Using Python 3.9+ features, virtual environments (.venv), async/await for I/O
- **Pass**: Context managers used for database connections (ConnectionPool.get_connection)
- **Pass**: Structured logging in place, environment variables for configuration
- **Pass**: Using dataclasses approach (Node base class with properties)

### Security Requirements ✅
- **Pass**: No hard-coded secrets (using environment variables for MEMGRAPH_URI, etc.)
- **Pass**: API key authentication in place (Depends(get_api_key))
- **Pass**: User ID isolation for multi-user scenarios (user_id filtering)

### Summary
**GATE STATUS**: ✅ PASS with action items

**Action Items Before Implementation**:
1. Write integration tests for session persistence (test server restart scenario)
2. Write unit tests for debug event persistence
3. Write tests for frontend-backend session synchronization
4. Ensure all new code passes static analysis tools

---

## Constitution Check - Post-Design Re-evaluation

**Date**: 2025-10-29 (after Phase 1 design completion)

### Re-evaluation Results

#### I. Modular Architecture & Separation of Concerns ✅
- **Pass**: Design maintains clear separation between:
  - Persistence layer (`src/core/db/debug.py`, `src/core/db/session.py`)
  - Schema definitions (`src/core/db/schemas/debug_objects.py`)
  - In-memory cache layer (`agent.py`, `debug_capture.py`)
  - API layer (`src/api/routes/session.py`)
- **Pass**: No violations of dependency direction - API depends on core, core doesn't depend on API

#### II. Code Readability & Self-Documentation ✅
- **Pass**: Data model clearly documented with field descriptions and validation rules
- **Pass**: API contracts specify all endpoints, request/response formats, and error handling
- **Pass**: JSON serialization formats documented with examples
- **Pass**: All new classes follow naming conventions (DebugEvent, DebugEventType, etc.)

#### III. Test-First Development (NON-NEGOTIABLE) ✅
- **Pass**: Quickstart guide mandates TDD workflow with "write tests first" approach
- **Pass**: Test files specified before implementation files in workflow
- **Pass**: Both unit tests (`test_debug_db_operations.py`) and integration tests (`test_session_persistence.py`) defined
- **Ready**: Tests are documented and ready to be written before implementation

#### IV. Type Safety & Static Analysis ✅
- **Pass**: All schemas use type hints (`Optional[str]`, `List[Dict[str, Any]]`, `datetime`)
- **Pass**: Enums used for event types (DebugEventType) to prevent invalid values
- **Pass**: Pydantic models used for API validation
- **Ready**: Code examples in quickstart include proper type hints

#### V. Python Best Practices ✅
- **Pass**: Async patterns addressed (thread pool executor for sync DB calls)
- **Pass**: Context managers used for database connections (existing ConnectionPool pattern)
- **Pass**: Error handling with graceful degradation specified
- **Pass**: JSON serialization/deserialization documented
- **Pass**: Resource management patterns followed (connection pool, cache management)

### Security Requirements ✅
- **Pass**: User ID filtering enforced at database query level
- **Pass**: API key authentication required for all endpoints
- **Pass**: JWT token validation for multi-user scenarios
- **Pass**: No new secrets introduced (using existing MEMGRAPH_* env vars)
- **Pass**: Defense in depth - filtering at both DB and API levels

### Design Quality ✅
- **Pass**: Cache-aside pattern well-documented for performance
- **Pass**: Write-through cache ensures consistency
- **Pass**: Graph relationships leverage Memgraph strengths
- **Pass**: Graceful degradation handles database failures
- **Pass**: Cascade deletion for data integrity

**FINAL GATE STATUS**: ✅ **PASS** - All constitutional principles satisfied

**Clearance for Phase 2**: Proceed to task breakdown (tasks.md) - Design is sound and compliant

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
# Backend (Python/FastAPI)
src/
├── agent.py                    # Contains _agent_sessions dict - MODIFY for DB integration
├── core/
│   ├── db/
│   │   ├── __init__.py         # ConnectionPool - ALREADY EXISTS
│   │   ├── session.py          # Session CRUD operations - ALREADY EXISTS, MAY EXTEND
│   │   ├── schemas/
│   │   │   ├── session_objects.py  # Session node schema - ALREADY EXISTS
│   │   │   └── debug_objects.py    # DebugCapture, DebugEvent schemas - NEW
│   │   └── debug.py            # Debug persistence operations - NEW
│   ├── debug_capture.py        # Contains _debug_sessions dict - MODIFY for DB integration
│   └── ...
├── api/
│   ├── routes/
│   │   ├── session.py          # Session API endpoints - MAY EXTEND
│   │   └── debug.py            # Debug API endpoints - MAY EXTEND
│   └── ...
└── ui/                         # Frontend (if modifications needed)
    └── ...

tests/
├── integration/
│   ├── test_session_persistence.py     # NEW - Test server restart scenarios
│   ├── test_debug_persistence.py       # NEW - Test debug event persistence
│   └── test_session_sync.py            # NEW - Test frontend-backend sync
└── unit/
    ├── test_session_db_operations.py   # NEW - Test session CRUD
    └── test_debug_db_operations.py     # NEW - Test debug CRUD

docker/
└── docker-compose.yml          # Memgraph configuration - ALREADY EXISTS

config/
└── ...

specs/001-session-storage/
├── plan.md                     # This file
├── research.md                 # Phase 0 output
├── data-model.md               # Phase 1 output
├── quickstart.md               # Phase 1 output
└── contracts/                  # Phase 1 output (API contracts)
```

**Structure Decision**: 

This is a **web application** (backend + frontend) with the following characteristics:

1. **Backend (Python)**: Core session storage logic in `src/core/db/` following existing modular architecture
2. **Database**: Memgraph graph database in Docker (already configured)
3. **API Layer**: FastAPI endpoints in `src/api/routes/`
4. **Frontend**: Existing UI in `src/ui/` that uses localStorage for session management
5. **Tests**: Separated into `tests/integration/` and `tests/unit/` as per constitution

The implementation will leverage existing infrastructure:
- **Session schema** already defined in `src/core/db/schemas/session_objects.py`
- **ConnectionPool** already implemented in `src/core/db/__init__.py`
- **Session CRUD** already partially implemented in `src/core/db/session.py`

New components needed:
- Debug event schemas and persistence (NEW)
- Integration between in-memory cache and database (MODIFY)
- Frontend-backend session synchronization logic (NEW)

## Complexity Tracking

> **No constitutional violations requiring justification.**

All design decisions align with constitutional principles:
- Modular architecture maintained (session storage in dedicated `core/db/` package)
- Type safety enforced throughout
- Test-first development mandated
- Separation of concerns between cache layer and persistence layer
- No additional complexity introduced beyond what's necessary for persistence requirements
