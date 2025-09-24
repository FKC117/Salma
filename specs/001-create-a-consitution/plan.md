
# Implementation Plan: Data Analysis System

**Branch**: `001-create-a-consitution` | **Date**: 2024-12-19 | **Spec**: [link]
**Input**: Feature specification from `/specs/001-create-a-consitution/spec.md`

## User Requirements Summary
Build a comprehensive data analysis system with:
- **UI**: Three-panel layout (statistical tools, analytical dashboard, AI chat) with draggable resizing
- **Theme**: Cursor AI dark theme with card-based design
- **File Upload**: Support for XLS, CSV, JSON files with security sanitization
- **Data Processing**: Convert to Parquet format, strip formulas/macros for security
- **Analysis Tools**: LangChain tool registry with dynamic parameter modals
- **Session Management**: User and dataset-specific sessions with caching
- **AI Integration**: LLM-powered analysis and interpretation

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
Build a Django + HTMX data analysis system with three-panel UI, file upload/processing, LangChain tool registry, **agentic AI-powered analysis**, and **RAG (Retrieval-Augmented Generation) system using Redis as vector database**. The system will provide statistical tools, analytical dashboards, and AI chat functionality with robust session management, caching, **autonomous AI agent execution**, and **grounded AI responses through RAG**. Users can upload datasets and click "Analyze" to trigger end-to-end autonomous analysis workflows with intelligent context retrieval.

## Technical Context
**Language/Version**: Python 3.11+ (Django backend)  
**Primary Dependencies**: Django, HTMX, Bootstrap 5+, pandas, pyarrow (Parquet), LangChain, lifelines, matplotlib, seaborn, Google AI API, sentence-transformers, redis  
**Storage**: PostgreSQL (metadata & results), Parquet files (dataset content), Redis (analytical key prefix for caching + vector database for RAG)  
**Testing**: Django TestCase, pytest, HTMX integration tests  
**Requirements Management**: Comprehensive requirements.txt with pinned versions, mandatory installation before development  
**Target Platform**: Web application (cross-browser)  
**Project Type**: web (frontend + backend)  
**Performance Goals**: <2s file upload processing, <500ms analysis tool execution, <1s UI updates  
**Constraints**: HTMX-only (no JavaScript), dark theme mandatory, card-based design, security-first  
**Scale/Scope**: Multi-user, multiple datasets per user, 100+ analysis tools, real-time AI chat

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### ✅ HTMX-First Architecture Compliance
- **Status**: COMPLIANT
- **Evidence**: All interactive features will use HTMX (file upload, tool execution, AI chat, panel resizing)
- **Implementation**: HTMX for form submissions, partial page updates, dynamic content loading

### ✅ Dark Theme Design System Compliance  
- **Status**: COMPLIANT
- **Evidence**: Cursor AI dark theme specified, card-based layout for all components
- **Implementation**: Bootstrap 5+ with custom dark theme, all content in cards

### ✅ Django Backend Excellence Compliance
- **Status**: COMPLIANT  
- **Evidence**: Django as sole backend framework, settings.py configuration, SQLite default
- **Implementation**: Django models, views, templates with HTMX integration

### ✅ Test-Driven Development Compliance
- **Status**: COMPLIANT
- **Evidence**: TDD mandatory for all features, comprehensive test coverage required
- **Implementation**: Django TestCase + pytest for backend, HTMX integration tests

### ✅ Security-First Development Compliance
- **Status**: COMPLIANT
- **Evidence**: File sanitization, formula/macro removal, input validation, CSRF protection
- **Implementation**: Secure file processing, input sanitization, Django security features

**Overall Status**: ✅ ALL CONSTITUTION REQUIREMENTS MET

## Project Structure

### Documentation (this feature)
```
specs/[###-feature]/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
# Option 1: Single project (DEFAULT)
src/
├── models/
├── services/
├── cli/
└── lib/

tests/
├── contract/
├── integration/
└── unit/

# Option 2: Web application (when "frontend" + "backend" detected)
backend/
├── src/
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/

# Option 3: Mobile + API (when "iOS/Android" detected)
api/
└── [same as backend above]

ios/ or android/
└── [platform-specific structure]
```

**Structure Decision**: Option 2 (Web application) - Frontend + Backend architecture required for Django + HTMX data analysis system

## Phase 0: Outline & Research
1. **Extract unknowns from Technical Context** above:
   - For each NEEDS CLARIFICATION → research task
   - For each dependency → best practices task
   - For each integration → patterns task

2. **Generate and dispatch research agents**:
   ```
   For each unknown in Technical Context:
     Task: "Research {unknown} for {feature context}"
   For each technology choice:
     Task: "Find best practices for {tech} in {domain}"
   ```

3. **Consolidate findings** in `research.md` using format:
   - Decision: [what was chosen]
   - Rationale: [why chosen]
   - Alternatives considered: [what else evaluated]

**Output**: research.md with all NEEDS CLARIFICATION resolved

## Phase 1: Design & Contracts
*Prerequisites: research.md complete*

1. **Extract entities from feature spec** → `data-model.md`:
   - Entity name, fields, relationships
   - Validation rules from requirements
   - State transitions if applicable

2. **Generate API contracts** from functional requirements:
   - For each user action → endpoint
   - Use standard REST/GraphQL patterns
   - Output OpenAPI/GraphQL schema to `/contracts/`

3. **Generate contract tests** from contracts:
   - One test file per endpoint
   - Assert request/response schemas
   - Tests must fail (no implementation yet)

4. **Extract test scenarios** from user stories:
   - Each story → integration test scenario
   - Quickstart test = story validation steps

5. **Generate requirements.txt** with comprehensive dependencies:
   - Pin all package versions for reproducibility
   - Separate development and production dependencies
   - Include all packages from research.md decisions
   - Ensure compatibility between versions

6. **Update agent file incrementally** (O(1) operation):
   - Run `.specify/scripts/powershell/update-agent-context.ps1 -AgentType cursor`
     **IMPORTANT**: Execute it exactly as specified above. Do not add or remove any arguments.
   - If exists: Add only NEW tech from current plan
   - Preserve manual additions between markers
   - Update recent changes (keep last 3)
   - Keep under 150 lines for token efficiency
   - Output to repository root

**Output**: data-model.md, /contracts/*, failing tests, quickstart.md, requirements.txt, agent-specific file

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
- Load `.specify/templates/tasks-template.md` as base
- Generate tasks from Phase 1 design docs (contracts, data model, quickstart)
- Each API endpoint → contract test task [P]
- Each data model → Django model creation task [P] 
- Each user story → integration test task
- HTMX integration → frontend component tasks
- File processing → data pipeline tasks
- AI integration → LangChain tool tasks
- Implementation tasks to make tests pass

**Ordering Strategy**:
- TDD order: Tests before implementation 
- Dependency order: Models → Services → API → Frontend → Integration
- Security order: File validation → Input sanitization → CSRF protection
- Mark [P] for parallel execution (independent files)

**Estimated Output**: 50-55 numbered, ordered tasks in tasks.md covering:
- Requirements.txt generation and dependency installation
- Django project setup and configuration
- Celery setup and configuration with Redis broker
- Data models and database migrations (including AgentRun/AgentStep)
- Code organization (tools subfolder, separated views)
- LLM context caching implementation
- LLM batch processing and image management
- LangChain sandbox and secure code execution
- Performance optimization and memory efficiency
- Celery task implementation for all heavy operations
- **Agentic AI runtime wiring (Celery loop + DRF endpoints)**
- **AgentRun creation and execution workflow**
- **Real-time agent progress updates via HTMX**
- **RAG System Implementation with Redis Vector Database**
- **VectorNote model and Redis vector storage**
- **Dataset-aware indexing and global knowledge indexing**
- **RAG API endpoints (upsert, search, clear)**
- **Agent integration with RAG retrieval**
- **PII masking and multi-tenancy for RAG**
- File upload and processing pipeline
- Analysis tool registry and execution
- HTMX frontend components
- Three-panel UI with draggable resizing
- **"Analyze" button integration with agentic AI + RAG**
- AI chat integration with context, images, and sandbox
- Session management and caching
- Security hardening
- Testing and validation

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## RAG Implementation Strategy
*Redis-based Vector Database Integration*

### RAG Architecture Overview
The RAG system will use Redis as both cache and vector database, leveraging existing infrastructure:
- **Vector Storage**: Redis with 'analytical:rag:' key prefix for all embeddings
- **Embedding Model**: sentence-transformers/all-MiniLM-L6-v2 (lightweight, fast)
- **Search Method**: Cosine similarity with Redis-based vector operations
- **Indexing Strategy**: Automatic indexing on dataset upload and analysis completion

### RAG Integration Points
1. **File Processing Service**: Auto-index dataset metadata after upload
2. **Analysis Executor**: Auto-index analysis results after completion
3. **Agentic AI Controller**: RAG retrieval before planning and execution
4. **LLM Processor**: Enhanced context with retrieved RAG content

### RAG Data Flow
1. **Indexing**: Dataset/analysis → Extract content → Generate embeddings → Store in Redis
2. **Retrieval**: Agent query → Generate query embedding → Search Redis → Return top-k results
3. **Integration**: Retrieved content → Add to LLM context → Enhanced agent responses

### RAG Security & Privacy
- **Multi-tenancy**: All queries filtered by dataset_id and user_id
- **PII Masking**: Only summaries and metadata indexed, never raw data
- **Audit Trail**: All RAG operations logged with correlation IDs
- **Token Tracking**: RAG retrieval costs tracked in existing token system

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)  
**Phase 4**: Implementation (execute tasks.md following constitutional principles)  
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Complexity Tracking
*Fill ONLY if Constitution Check has violations that must be justified*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |


## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command)
- [x] Phase 1: Design complete (/plan command)
- [x] Phase 2: Task planning complete (/plan command - describe approach only)
- [x] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS
- [x] Post-Design Constitution Check: PASS
- [x] All NEEDS CLARIFICATION resolved
- [x] Complexity deviations documented

---
*Based on Constitution v2.1.1 - See `/memory/constitution.md`*
