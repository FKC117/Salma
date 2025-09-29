# Tasks: Sandbox UI with LLM Integration

**Input**: Design documents from `/specs/003-now-lets-make/`
**Prerequisites**: plan.md (required), research.md, data-model.md, contracts/

## Execution Flow (main)
```
1. Load plan.md from feature directory
   → If not found: ERROR "No implementation plan found"
   → Extract: tech stack, libraries, structure
2. Load optional design documents:
   → data-model.md: Extract entities → model tasks
   → contracts/: Each file → contract test task
   → research.md: Extract decisions → setup tasks
3. Generate tasks by category:
   → Setup: project init, dependencies, linting
   → Tests: contract tests, integration tests
   → Core: models, services, CLI commands
   → Integration: DB, middleware, logging
   → Polish: unit tests, performance, docs
4. Apply task rules:
   → Different files = mark [P] for parallel
   → Same file = sequential (no [P])
   → Tests before implementation (TDD)
5. Number tasks sequentially (T001, T002...)
6. Generate dependency graph
7. Create parallel execution examples
8. Validate task completeness:
   → All contracts have tests?
   → All entities have models?
   → All endpoints implemented?
9. Return: SUCCESS (tasks ready for execution)
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Path Conventions
- **Single project**: `analytical/` at repository root
- **Web app**: Django + HTMX structure maintained
- Paths shown below assume existing Django structure

## Phase 3.1: Setup (Backend 95% Complete - Focus on Missing Components)
- [ ] T001 [P] Create database migrations for ChatSession and AnalysisSuggestion models in analytical/analytics/migrations/
- [ ] T002 [P] Update existing ChatMessage model with new fields in analytical/analytics/models.py
- [ ] T003 [P] Configure enhanced chat API endpoints in analytical/analytics/urls.py

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3
**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**
- [ ] T004 [P] Contract test POST /api/chat/send/ in tests/contract/test_chat_send.py
- [ ] T005 [P] Contract test GET /api/chat/history/ in tests/contract/test_chat_history.py
- [ ] T006 [P] Contract test POST /api/chat/execute-suggestion/ in tests/contract/test_chat_execute.py
- [ ] T007 [P] Contract test GET /api/chat/context/ in tests/contract/test_chat_context.py
- [ ] T008 [P] Contract test PUT /api/chat/session/ in tests/contract/test_chat_session.py
- [ ] T009 [P] Integration test basic chat flow in tests/integration/test_chat_basic.py
- [ ] T010 [P] Integration test analysis suggestion execution in tests/integration/test_chat_analysis.py
- [ ] T011 [P] Integration test context management in tests/integration/test_chat_context.py

## Phase 3.3: Core Implementation (Leverage Existing Backend Services)
- [ ] T012 [P] ChatSession model in analytical/analytics/models.py
- [ ] T013 [P] AnalysisSuggestion model in analytical/analytics/models.py
- [ ] T014 [P] ChatService leveraging existing LLMProcessor and RAGService in analytical/analytics/services/chat_service.py
- [ ] T015 [P] AnalysisSuggestionService leveraging existing AnalysisExecutor in analytical/analytics/services/analysis_suggestion_service.py
- [ ] T016 POST /api/chat/send/ endpoint leveraging existing ChatViewSet in analytical/analytics/views.py
- [ ] T017 GET /api/chat/history/ endpoint leveraging existing ChatViewSet in analytical/analytics/views.py
- [ ] T018 POST /api/chat/execute-suggestion/ endpoint leveraging existing AnalysisExecutor in analytical/analytics/views.py
- [ ] T019 GET /api/chat/context/ endpoint leveraging existing SessionManager in analytical/analytics/views.py
- [ ] T020 PUT /api/chat/session/ endpoint leveraging existing SessionManager in analytical/analytics/views.py
- [ ] T021 Input validation leveraging existing validation patterns
- [ ] T022 Error handling leveraging existing audit trail system
- [ ] T023 Token usage tracking leveraging existing token management

## Phase 3.4: Frontend Integration
- [ ] T024 [P] Chat interface template in analytical/analytics/templates/analytics/chat_panel.html
- [ ] T025 [P] Chat message display template in analytical/analytics/templates/analytics/chat_message.html
- [ ] T026 [P] Analysis suggestion display template in analytical/analytics/templates/analytics/analysis_suggestion.html
- [ ] T027 HTMX integration for chat message sending
- [ ] T028 HTMX integration for chat history loading
- [ ] T029 HTMX integration for analysis suggestion execution
- [ ] T030 Chat panel integration into existing dashboard layout
- [ ] T031 Analysis result display integration with chat suggestions
- [ ] T032 Context-aware UI updates based on chat interactions

## Phase 3.5: Integration (Backend Services Already Complete)
- [ ] T033 Connect ChatService to existing LLMProcessor ✅ (Already integrated)
- [ ] T034 Integrate with existing RAG service for context retrieval ✅ (Already integrated)
- [ ] T035 Connect to existing AnalysisSession management ✅ (Already integrated)
- [ ] T036 Integrate with existing token management system ✅ (Already integrated)
- [ ] T037 Connect to existing audit trail system ✅ (Already integrated)
- [ ] T038 Rate limiting for chat endpoints
- [ ] T039 CORS and security headers for chat API
- [ ] T040 Session management for chat conversations

## Phase 3.6: Polish
- [ ] T041 [P] Unit tests for ChatService in tests/unit/test_chat_service.py
- [ ] T042 [P] Unit tests for AnalysisSuggestionService in tests/unit/test_analysis_suggestion_service.py
- [ ] T043 [P] Unit tests for chat validation in tests/unit/test_chat_validation.py
- [ ] T044 Performance tests for chat response times (<2s)
- [ ] T045 [P] Update API documentation in docs/api.md
- [ ] T046 Remove code duplication in chat services
- [ ] T047 Run manual testing scenarios from quickstart.md
- [ ] T048 Error message improvements for user experience
- [ ] T049 Loading state improvements for chat interface
- [ ] T050 Accessibility improvements for chat interface

## Dependencies
- Tests (T004-T011) before implementation (T012-T023)
- T012 blocks T014, T016, T017, T020
- T013 blocks T015, T018
- T014 blocks T016, T017, T020
- T015 blocks T018
- T016-T020 block T027-T029
- T024-T026 block T030-T032
- Implementation before frontend (T024-T032)
- Frontend before integration (T033-T040)
- Integration before polish (T041-T050)

## Parallel Example
```
# Launch T004-T011 together (Contract and Integration Tests):
Task: "Contract test POST /api/chat/send/ in tests/contract/test_chat_send.py"
Task: "Contract test GET /api/chat/history/ in tests/contract/test_chat_history.py"
Task: "Contract test POST /api/chat/execute-suggestion/ in tests/contract/test_chat_execute.py"
Task: "Contract test GET /api/chat/context/ in tests/contract/test_chat_context.py"
Task: "Contract test PUT /api/chat/session/ in tests/contract/test_chat_session.py"
Task: "Integration test basic chat flow in tests/integration/test_chat_basic.py"
Task: "Integration test analysis suggestion execution in tests/integration/test_chat_analysis.py"
Task: "Integration test context management in tests/integration/test_chat_context.py"

# Launch T012-T015 together (Models and Services):
Task: "ChatSession model in analytical/analytics/models.py"
Task: "AnalysisSuggestion model in analytical/analytics/models.py"
Task: "ChatService for message handling in analytical/analytics/services/chat_service.py"
Task: "AnalysisSuggestionService for suggestion management in analytical/analytics/services/analysis_suggestion_service.py"

# Launch T024-T026 together (Templates):
Task: "Chat interface template in analytical/analytics/templates/analytics/chat_panel.html"
Task: "Chat message display template in analytical/analytics/templates/analytics/chat_message.html"
Task: "Analysis suggestion display template in analytical/analytics/templates/analytics/analysis_suggestion.html"
```

## Notes
- [P] tasks = different files, no dependencies
- Verify tests fail before implementing
- Commit after each task
- Avoid: vague tasks, same file conflicts
- Follow existing Django + HTMX patterns
- Maintain existing dark theme and card-based design
- Integrate with existing analysis tools and results display

## Task Generation Rules
*Applied during main() execution*

1. **From Contracts**:
   - Each contract file → contract test task [P]
   - Each endpoint → implementation task
   
2. **From Data Model**:
   - Each entity → model creation task [P]
   - Relationships → service layer tasks
   
3. **From User Stories**:
   - Each story → integration test [P]
   - Quickstart scenarios → validation tasks
   
4. **Ordering**:
   - Setup → Tests → Models → Services → Endpoints → Frontend → Integration → Polish
   - Dependencies block parallel execution

## Validation Checklist
*GATE: Checked by main() before returning*

- [x] All contracts have corresponding tests
- [x] All entities have model tasks
- [x] All tests come before implementation
- [x] Parallel tasks truly independent
- [x] Each task specifies exact file path
- [x] No task modifies same file as another [P] task
- [x] Frontend tasks properly ordered after backend
- [x] Integration tasks follow implementation
- [x] Polish tasks come last
