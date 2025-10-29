---
description: "Task list for database-backed session storage implementation"
---

# Tasks: Database-Backed Session Storage

**Feature Branch**: `001-session-storage`  
**Input**: Design documents from `/specs/001-session-storage/`  
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅

**Tests**: Tests are included as per TDD workflow mandated in constitution check

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

This is a **single project** structure:
- Backend: `src/` at repository root
- Tests: `tests/` at repository root
- Frontend: `src/ui/` (existing)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and database infrastructure setup

- [ ] T001 Verify Memgraph database is running via docker-compose up -d memgraph
- [ ] T002 Create database indexes script in scripts/create_indexes.py
- [ ] T003 [P] Run database index creation for SESSION and DEBUG_EVENT nodes
- [ ] T004 [P] Verify database connection pool configuration in src/core/db/__init__.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 Create DebugEventType enum in src/core/db/schemas/debug_objects.py
- [ ] T006 [P] Create DebugEvent node class in src/core/db/schemas/debug_objects.py
- [ ] T007 Update src/core/db/schemas/__init__.py to import debug objects
- [ ] T008 [P] Implement create_debug_event() in src/core/db/debug.py
- [ ] T009 [P] Implement get_debug_events_by_session() in src/core/db/debug.py
- [ ] T010 [P] Implement delete_debug_events_by_session() in src/core/db/debug.py
- [ ] T011 Extend Session schema with all required fields in src/core/db/schemas/session_objects.py
- [ ] T012 [P] Implement save_session_state() with JSON serialization in src/core/db/session.py
- [ ] T013 [P] Implement restore_session_state() with JSON deserialization in src/core/db/session.py
- [ ] T014 [P] Implement create_db_session() for new session creation in src/core/db/session.py

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Session Persistence Across Server Restarts (Priority: P1) 🎯 MVP

**Goal**: Enable agent sessions to survive server restarts by persisting conversation history, tool configurations, and agent settings to Memgraph database

**Independent Test**: Create a session with conversation history, stop the server, restart it, and verify the session is restored with all data intact

### Tests for User Story 1 (TDD - Write FIRST, ensure they FAIL)

- [ ] T015 [P] [US1] Create test_session_db_operations.py in tests/unit/ with test cases for save_session_state()
- [ ] T016 [P] [US1] Create test_session_persistence.py in tests/integration/ with server restart simulation test
- [ ] T017 [P] [US1] Add test case for restore_session_state() in tests/unit/test_session_db_operations.py
- [ ] T018 [US1] Run tests to verify they FAIL (pytest tests/unit/test_session_db_operations.py -v)

### Implementation for User Story 1

- [ ] T019 [US1] Add restore_from_db parameter to Agent.__init__() in src/agent.py
- [ ] T020 [US1] Implement _restore_from_db() method in src/agent.py to load state from database
- [ ] T021 [US1] Update Agent.__init__() to call save_session_state() for new sessions in src/agent.py
- [ ] T022 [US1] Modify get_agent_instance() to check database on cache miss in src/agent.py
- [ ] T023 [US1] Add save_session_state() call after Agent.chat() method in src/agent.py
- [ ] T024 [US1] Add save_session_state() call when tool configurations change in src/agent.py
- [ ] T025 [US1] Add save_session_state() call when MCP is initialized in src/agent.py
- [ ] T026 [US1] Update last_activity and conversation_count timestamps on session modifications in src/core/db/session.py

### Integration & Validation for User Story 1

- [ ] T027 [US1] Run unit tests to verify they PASS (pytest tests/unit/test_session_db_operations.py -v)
- [ ] T028 [US1] Run integration tests to verify server restart scenario (pytest tests/integration/test_session_persistence.py -v)
- [ ] T029 [US1] Manual test: Create session, add messages, restart server, verify restoration
- [ ] T030 [US1] Verify conversation history integrity after restoration in Memgraph Lab

**Checkpoint**: At this point, User Story 1 should be fully functional - sessions survive server restarts with complete state restoration

---

## Phase 4: User Story 2 - Debug Session Persistence (Priority: P2)

**Goal**: Persist debug events to database so they can be reviewed after server restarts or across multiple debugging sessions

**Independent Test**: Enable debug mode, generate debug events, restart the server, and verify all debug events are still accessible

### Tests for User Story 2 (TDD - Write FIRST, ensure they FAIL)

- [ ] T031 [P] [US2] Create test_debug_db_operations.py in tests/unit/ with test_create_debug_event()
- [ ] T032 [P] [US2] Add test_get_debug_events_by_session() to tests/unit/test_debug_db_operations.py
- [ ] T033 [P] [US2] Add test_delete_debug_events_cascade() to tests/unit/test_debug_db_operations.py
- [ ] T034 [P] [US2] Create test_debug_persistence.py in tests/integration/ with restart scenario test
- [ ] T035 [US2] Run tests to verify they FAIL (pytest tests/unit/test_debug_db_operations.py -v)

### Implementation for User Story 2

- [ ] T036 [US2] Modify DebugCapture.capture_event() to persist events to database in src/core/debug_capture.py
- [ ] T037 [US2] Add database error handling with logging in DebugCapture.capture_event() in src/core/debug_capture.py
- [ ] T038 [US2] Implement load_events_from_db() method in DebugCapture class in src/core/debug_capture.py
- [ ] T039 [US2] Update get_debug_capture_instance() to load events from database on creation in src/core/debug_capture.py
- [ ] T040 [US2] Update delete_session() to cascade delete debug events in src/core/db/session.py

### Integration & Validation for User Story 2

- [ ] T041 [US2] Run unit tests to verify they PASS (pytest tests/unit/test_debug_db_operations.py -v)
- [ ] T042 [US2] Run integration tests to verify debug persistence across restart (pytest tests/integration/test_debug_persistence.py -v)
- [ ] T043 [US2] Manual test: Enable debug, generate events, restart server, verify events exist
- [ ] T044 [US2] Verify BELONGS_TO relationships in Memgraph Lab for debug events

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently - sessions and debug events persist across restarts

---

## Phase 5: User Story 3 - Frontend Session Synchronization (Priority: P2)

**Goal**: Synchronize frontend sessions (localStorage) with backend database to ensure consistency between client and server

**Independent Test**: Create a session in the frontend, verify it's saved to the database, clear browser storage, and confirm the session can be restored from the database

### Tests for User Story 3 (TDD - Write FIRST, ensure they FAIL)

- [ ] T045 [P] [US3] Create test_session_sync.py in tests/integration/ with frontend-backend sync test
- [ ] T046 [P] [US3] Add test case for session verification on frontend load in tests/integration/test_session_sync.py
- [ ] T047 [P] [US3] Add test case for lazy backend session creation in tests/integration/test_session_sync.py
- [ ] T048 [US3] Run tests to verify they FAIL (pytest tests/integration/test_session_sync.py -v)

### API Implementation for User Story 3

- [ ] T049 [P] [US3] Update GET /api/session/{session_id} to check database on cache miss in src/api/routes/session.py
- [ ] T050 [P] [US3] Update GET /api/session/new to create database session immediately in src/api/routes/session.py
- [ ] T051 [P] [US3] Add GET /api/sessions endpoint to list user sessions in src/api/routes/session.py
- [ ] T052 [US3] Update get_agent_instance() to restore from database if not in cache in src/api/routes/session.py
- [ ] T053 [US3] Add async wrapper for save_session_state() using thread pool executor in src/api/routes/session.py

### Frontend Implementation for User Story 3

- [ ] T054 [US3] Add verifySessionExists() function to frontend in src/ui/[session-manager].js
- [ ] T055 [US3] Update frontend session initialization to verify backend sessions on load in src/ui/[app-init].js
- [ ] T056 [US3] Add lazy backend session creation on first message send in src/ui/[chat-handler].js
- [ ] T057 [US3] Update localStorage to save backend session IDs in src/ui/[session-storage].js

### Integration & Validation for User Story 3

- [ ] T058 [US3] Run integration tests to verify they PASS (pytest tests/integration/test_session_sync.py -v)
- [ ] T059 [US3] Manual test: Create frontend session, verify backend session created
- [ ] T060 [US3] Manual test: Clear localStorage, reload app, verify sessions restored from backend
- [ ] T061 [US3] Test session verification handles 404 responses gracefully

**Checkpoint**: All three user stories (1, 2, 3) should now work independently and together - full session persistence with frontend-backend sync

---

## Phase 6: User Story 4 - Multi-User Session Isolation (Priority: P3)

**Goal**: Ensure sessions are properly isolated by user ID so each user can only access their own sessions

**Independent Test**: Create sessions for different users and verify each user can only access their own sessions

### Tests for User Story 4 (TDD - Write FIRST, ensure they FAIL)

- [ ] T062 [P] [US4] Create test_multi_user_isolation.py in tests/integration/ with user isolation tests
- [ ] T063 [P] [US4] Add test case for user_id filtering in get_all_sessions() in tests/integration/test_multi_user_isolation.py
- [ ] T064 [P] [US4] Add test case for cross-user access prevention in tests/integration/test_multi_user_isolation.py
- [ ] T065 [US4] Run tests to verify they FAIL (pytest tests/integration/test_multi_user_isolation.py -v)

### Implementation for User Story 4

- [ ] T066 [P] [US4] Add user_id parameter to create_db_session() in src/core/db/session.py
- [ ] T067 [P] [US4] Add user_id filtering to get_all_sessions() query in src/core/db/session.py
- [ ] T068 [P] [US4] Add user_id filtering to get_session_by_id() query in src/core/db/session.py
- [ ] T069 [US4] Update GET /api/sessions to extract user_id from JWT token in src/api/routes/session.py
- [ ] T070 [US4] Update GET /api/session/{session_id} to verify user ownership in src/api/routes/session.py
- [ ] T071 [US4] Update DELETE /api/session/{session_id} to verify user ownership in src/api/routes/session.py
- [ ] T072 [US4] Add get_user_id() dependency function to extract user from JWT in src/api/auth.py

### Integration & Validation for User Story 4

- [ ] T073 [US4] Run integration tests to verify they PASS (pytest tests/integration/test_multi_user_isolation.py -v)
- [ ] T074 [US4] Manual test: Create sessions for user A and user B, verify isolation
- [ ] T075 [US4] Manual test: Attempt cross-user access, verify 403 Forbidden response
- [ ] T076 [US4] Verify user_id index performance in Memgraph Lab

**Checkpoint**: All user stories should now be independently functional with full multi-user support and session isolation

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T077 [P] Add error handling for database connection failures with graceful degradation in src/core/db/session.py
- [ ] T078 [P] Add retry logic with exponential backoff for database operations in src/core/db/session.py
- [ ] T079 [P] Add logging for all database operations (save, restore, delete) in src/core/db/session.py
- [ ] T080 [P] Add logging for debug event persistence in src/core/db/debug.py
- [ ] T081 [P] Add monitoring metrics for cache hit/miss rates in src/agent.py
- [ ] T082 [P] Add database health check endpoint in src/api/routes/health.py
- [ ] T083 [P] Update API documentation with new session endpoints in docs/api.md
- [ ] T084 [P] Add session cleanup job for inactive sessions (>30 days) in scripts/cleanup_old_sessions.py
- [ ] T085 [P] Add unit tests for JSON serialization/deserialization in tests/unit/test_session_serialization.py
- [ ] T086 Run complete test suite with coverage report (pytest tests/ --cov=src --cov-report=html)
- [ ] T087 Verify code coverage meets 80% minimum threshold
- [ ] T088 Run static analysis tools (mypy, pylint, flake8) and fix any issues
- [ ] T089 Run quickstart.md validation following all setup and testing steps
- [ ] T090 Update README.md with database setup instructions

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phases 3-6)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (US1 → US2 → US3 → US4)
- **Polish (Phase 7)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Integrates with US1 session deletion but independently testable
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) - Uses US1 session persistence but independently testable
- **User Story 4 (P3)**: Can start after Foundational (Phase 2) - Adds filtering to US1 but independently testable

### Within Each User Story

1. Tests MUST be written FIRST and FAIL before implementation
2. Schema/model changes before CRUD operations
3. CRUD operations before integration with existing code
4. Core implementation before API layer
5. API layer before frontend integration
6. Story complete and validated before moving to next priority

### Parallel Opportunities

**Phase 1 (Setup)**:
- T003 and T004 can run in parallel

**Phase 2 (Foundational)**:
- T006 (DebugEvent class) and T005 (DebugEventType) can run in parallel
- T008, T009, T010 (debug CRUD operations) can run in parallel
- T012, T013, T014 (session CRUD operations) can run in parallel

**Phase 3 (User Story 1)**:
- T015, T016, T017 (all US1 tests) can run in parallel

**Phase 4 (User Story 2)**:
- T031, T032, T033, T034 (all US2 tests) can run in parallel

**Phase 5 (User Story 3)**:
- T045, T046, T047 (all US3 tests) can run in parallel
- T049, T050, T051 (API endpoints) can run in parallel
- T066, T067, T068 (database operations) can run in parallel

**Phase 6 (User Story 4)**:
- T062, T063, T064 (all US4 tests) can run in parallel
- T066, T067, T068 (database operations with user filtering) can run in parallel

**Phase 7 (Polish)**:
- T077, T078, T079, T080, T081, T082, T083, T084, T085 (all independent improvements) can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (TDD - write first):
Task T015: "Create test_session_db_operations.py in tests/unit/"
Task T016: "Create test_session_persistence.py in tests/integration/"
Task T017: "Add test case for restore_session_state() in tests/unit/"

# After tests fail, launch parallel implementation tasks:
# (None for US1 - tasks have sequential dependencies)

# Run tests together after implementation:
pytest tests/unit/test_session_db_operations.py tests/integration/test_session_persistence.py -v
```

## Parallel Example: User Story 2

```bash
# Launch all tests for User Story 2 together (TDD - write first):
Task T031: "Create test_debug_db_operations.py in tests/unit/"
Task T032: "Add test_get_debug_events_by_session() to tests/unit/"
Task T033: "Add test_delete_debug_events_cascade() to tests/unit/"
Task T034: "Create test_debug_persistence.py in tests/integration/"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup → ~30 minutes
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories) → ~2-3 hours
3. Complete Phase 3: User Story 1 → ~2-3 hours
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready → **MVP DELIVERED: Sessions survive server restarts!**

**Estimated Time**: 5-7 hours for MVP

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready (~3 hours)
2. Add User Story 1 → Test independently → Deploy/Demo (MVP! ~3 hours)
3. Add User Story 2 → Test independently → Deploy/Demo (~2 hours)
4. Add User Story 3 → Test independently → Deploy/Demo (~2 hours)
5. Add User Story 4 → Test independently → Deploy/Demo (~1 hour)
6. Polish → Final touches (~1 hour)

**Total Estimated Time**: 12-14 hours for complete feature

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together (~3 hours)
2. Once Foundational is done:
   - **Developer A**: User Story 1 (MVP) - ~3 hours
   - **Developer B**: User Story 2 (Debug persistence) - ~2 hours
   - **Developer C**: User Story 3 (Frontend sync) - ~2 hours
3. Stories complete and integrate independently
4. **Developer D** (or rotate): User Story 4 (Multi-user isolation) - ~1 hour
5. All developers: Polish phase together - ~1 hour

**Parallel Completion Time**: ~6-7 hours with 3-4 developers

---

## Task Summary

- **Total Tasks**: 90
- **Setup Tasks**: 4 (Phase 1)
- **Foundational Tasks**: 10 (Phase 2) ⚠️ BLOCKING
- **User Story 1 Tasks**: 16 (Phase 3) 🎯 MVP
- **User Story 2 Tasks**: 14 (Phase 4)
- **User Story 3 Tasks**: 13 (Phase 5)
- **User Story 4 Tasks**: 15 (Phase 6)
- **Polish Tasks**: 14 (Phase 7)

### Tasks by User Story

| User Story | Priority | Test Tasks | Implementation Tasks | Total |
|------------|----------|------------|---------------------|-------|
| US1 - Session Persistence | P1 🎯 | 4 | 12 | 16 |
| US2 - Debug Persistence | P2 | 5 | 9 | 14 |
| US3 - Frontend Sync | P2 | 4 | 9 | 13 |
| US4 - Multi-User Isolation | P3 | 4 | 11 | 15 |

### Parallel Opportunities

- **Phase 1**: 2 parallel tasks
- **Phase 2**: 6 parallel tasks (2 groups of 3)
- **Phase 3 (US1)**: 3 test tasks in parallel
- **Phase 4 (US2)**: 4 test tasks in parallel
- **Phase 5 (US3)**: 6 parallel tasks (3 tests + 3 API endpoints)
- **Phase 6 (US4)**: 6 parallel tasks (3 tests + 3 database operations)
- **Phase 7**: 9 parallel tasks

**Total Parallel Opportunities**: 36 tasks can run in parallel with proper staffing

### MVP Scope (Recommended First Delivery)

**MVP = Phase 1 + Phase 2 + Phase 3 (User Story 1 only)**

- 30 tasks total
- Delivers core value: Sessions survive server restarts
- Estimated time: 5-7 hours
- Independently testable and deployable

---

## Format Validation ✅

All tasks follow the required format:
- ✅ Checkbox: `- [ ]` prefix
- ✅ Task ID: Sequential (T001-T090)
- ✅ [P] marker: Present for parallelizable tasks only
- ✅ [Story] label: Present for user story tasks (US1, US2, US3, US4)
- ✅ Description: Clear action with exact file path
- ✅ No story label for Setup, Foundational, and Polish phases

**Example Task Formats**:
- Setup: `- [ ] T001 Verify Memgraph database is running via docker-compose up -d memgraph`
- Foundational: `- [ ] T008 [P] Implement create_debug_event() in src/core/db/debug.py`
- User Story: `- [ ] T019 [US1] Add restore_from_db parameter to Agent.__init__() in src/agent.py`
- User Story (Parallel): `- [ ] T049 [P] [US3] Update GET /api/session/{session_id} in src/api/routes/session.py`

---

## Next Actions

1. ✅ Tasks.md generated and saved to `/specs/001-session-storage/tasks.md`
2. ⏭️ Review tasks with team for any adjustments
3. ⏭️ Begin Phase 1: Setup (estimated 30 minutes)
4. ⏭️ Proceed to Phase 2: Foundational (MUST complete before user stories)
5. ⏭️ Implement MVP (Phase 3 - User Story 1) for first delivery
6. ⏭️ Iterate on remaining user stories based on priority

**Ready to begin implementation!** 🚀
