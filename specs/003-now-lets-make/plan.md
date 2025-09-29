# Implementation Plan: Sandbox UI with LLM Integration

**Branch**: `003-now-lets-make` | **Date**: 2025-09-29 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/003-now-lets-make/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → If not found: ERROR "No feature spec at {path}"
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → Detect Project Type from context (web=frontend+backend, mobile=app+api)
   → Set Structure Decision based on project type
3. Fill the Constitution Check section based on the content of the constitution document.
4. Evaluate Constitution Check section below
   → If violations exist: Document in Complexity Tracking
   → If no justification possible: ERROR "Simplify approach first"
   → Update Progress Tracking: Initial Constitution Check
5. Execute Phase 0 → research.md
   → If NEEDS CLARIFICATION remain: ERROR "Resolve unknowns"
6. Execute Phase 1 → contracts, data-model.md, quickstart.md, agent-specific template file (e.g., `CLAUDE.md` for Claude Code, `.github/copilot-instructions.md` for GitHub Copilot, `GEMINI.md` for Gemini CLI, `QWEN.md` for Qwen Code or `AGENTS.md` for opencode).
7. Re-evaluate Constitution Check section
   → If new violations: Refactor design, return to Phase 1
   → Update Progress Tracking: Post-Design Constitution Check
8. Plan Phase 2 → Describe task generation approach (DO NOT create tasks.md)
9. STOP - Ready for /tasks command
```

**IMPORTANT**: The /plan command STOPS at step 7. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary
Build an AI-powered sandbox interface that integrates chat functionality with the existing three-panel dashboard, connecting users to LLM services for intelligent data analysis. The system will display only analysis results in card-based UI format, leveraging existing LLM processor, RAG system, and analysis tools to provide context-aware responses about datasets and analysis results.

## Technical Context
**Language/Version**: Python 3.11+ (Django backend)  
**Primary Dependencies**: Django, HTMX, Bootstrap 5+, Google AI API, existing LLM processor service, RAG service  
**Storage**: PostgreSQL (metadata), Redis (caching + vector database), existing models  
**Testing**: Django TestCase, pytest, HTMX integration tests  
**Target Platform**: Web application (existing Django + HTMX system)  
**Performance Goals**: <2s response time for AI queries, <500ms UI updates  
**Constraints**: Must integrate with existing token management, user authentication, and analysis history  
**Scale/Scope**: Existing user base with enhanced AI interaction capabilities  
**Project Type**: Web application (frontend + backend integration)

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Initial Constitution Check: ✅ PASS
- ✅ **HTMX-First Architecture**: Chat interface will use HTMX for all interactions
- ✅ **Dark Theme Design System**: Will integrate with existing dark theme and card-based layout
- ✅ **Django Backend Excellence**: Leverages existing Django backend and services
- ✅ **Test-Driven Development**: Will follow TDD with tests before implementation
- ✅ **Security-First Development**: Uses existing authentication and security systems
- ✅ **Data Security and Privacy**: Integrates with existing data sanitization and PII masking
- ✅ **Analysis History Management**: Will preserve and display analysis results in existing card format
- ✅ **REST API Architecture**: Will use existing API endpoints and create new ones as needed
- ✅ **Django Authentication System**: Uses existing authentication system
- ✅ **HTMX Error Prevention**: Will test all HTMX interactions thoroughly
- ✅ **Virtual Environment Activation**: Follows existing virtual environment requirements
- ✅ **Google AI Integration**: Uses existing Google AI service and token management
- ✅ **Agentic AI System**: Integrates with existing agentic AI controller
- ✅ **RAG System**: Leverages existing Redis-based RAG system
- ✅ **UI Development Feedback Loop**: Will follow incremental implementation with user feedback

### Post-Design Constitution Check: ✅ PASS
- ✅ All constitutional requirements maintained through design phase
- ✅ No violations introduced during design process

## Project Structure

### Documentation (this feature)
```
specs/003-now-lets-make/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
# Existing Django + HTMX structure maintained
analytical/
├── analytics/
│   ├── templates/analytics/     # Existing templates enhanced
│   ├── services/                # Existing services leveraged
│   ├── models.py                # Existing models used
│   ├── views.py                 # Existing views enhanced
│   └── urls.py                  # Existing URLs extended
└── tests/                       # Existing test structure used
```

**Structure Decision**: Maintain existing single Django project structure with enhancements

## Phase 0: Outline & Research
1. **Extract unknowns from Technical Context** above:
   - Chat interface integration patterns with existing dashboard
   - HTMX chat implementation best practices
   - LLM response formatting for analysis results
   - Context management between chat and analysis sessions

2. **Generate and dispatch research agents**:
   ```
   Task: "Research HTMX chat interface patterns for Django applications"
   Task: "Find best practices for integrating LLM responses with existing UI components"
   Task: "Research context management patterns for AI chat in data analysis applications"
   Task: "Find patterns for displaying analysis results in chat interfaces"
   ```

3. **Consolidate findings** in `research.md` using format:
   - Decision: [what was chosen]
   - Rationale: [why chosen]
   - Alternatives considered: [what else evaluated]

**Output**: research.md with all NEEDS CLARIFICATION resolved

## Phase 1: Design & Contracts
*Prerequisites: research.md complete*

1. **Extract entities from feature spec** → `data-model.md`:
   - ChatMessage model enhancements for analysis context
   - ChatSession model for conversation management
   - Integration with existing AnalysisSession and AnalysisResult models

2. **Generate API contracts** from functional requirements:
   - POST /api/chat/send/ - Send chat message and receive AI response
   - GET /api/chat/history/ - Get conversation history for current session
   - POST /api/chat/analyze/ - Trigger analysis based on AI suggestion
   - GET /api/chat/context/ - Get current dataset and session context

3. **Generate contract tests** from contracts:
   - One test file per endpoint
   - Assert request/response schemas
   - Tests must fail (no implementation yet)

4. **Extract test scenarios** from user stories:
   - Each story → integration test scenario
   - Quickstart test = story validation steps

5. **Update agent file incrementally** (O(1) operation):
   - Run `.specify/scripts/powershell/update-agent-context.ps1 -AgentType cursor`
   - Add new chat interface and LLM integration patterns
   - Preserve existing context and recent changes

**Output**: data-model.md, /contracts/*, failing tests, quickstart.md, agent-specific file

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
- Load `.specify/templates/tasks-template.md` as base
- Generate tasks from Phase 1 design docs (contracts, data model, quickstart)
- Each contract → contract test task [P]
- Each entity → model creation task [P] 
- Each user story → integration test task
- Implementation tasks to make tests pass

**Ordering Strategy**:
- TDD order: Tests before implementation 
- Dependency order: Models before services before UI
- Mark [P] for parallel execution (independent files)

**Estimated Output**: 20-25 numbered, ordered tasks in tasks.md

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)  
**Phase 4**: Implementation (execute tasks.md following constitutional principles)  
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Complexity Tracking
*No violations detected - all constitutional requirements maintained*

## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command)
- [x] Phase 1: Design complete (/plan command)
- [x] Phase 2: Task planning complete (/plan command - describe approach only)
- [ ] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS
- [x] Post-Design Constitution Check: PASS
- [x] All NEEDS CLARIFICATION resolved
- [x] Complexity deviations documented

---
*Based on Constitution v1.1.0 - See `/memory/constitution.md`*
