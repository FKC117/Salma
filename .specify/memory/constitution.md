# Django HTMX Project Constitution
<!-- Dark Theme Card-Based Web Application -->

## Core Principles

### I. HTMX-First Architecture (NON-NEGOTIABLE)
All interactive features MUST use HTMX instead of JavaScript; No vanilla JavaScript or JavaScript frameworks allowed; HTMX provides all dynamic behavior, form submissions, and AJAX functionality; This ensures consistent, maintainable, and accessible user interactions.

### II. Dark Theme Design System (MANDATORY)
All UI components MUST follow the dark theme color scheme; Card-based layout is the primary UI pattern for all pages and components; Design must be eye-soothing, simple, and beautiful; Bootstrap framework required for all styling; No white or creamish colors allowed.

### III. Django Backend Excellence
Django MUST be the sole backend framework; All settings MUST be configured in settings.py (no .env files); Default database configuration for development; Top-notch security standards enforced; All security best practices implemented by default.

### IV. Test-Driven Development (NON-NEGOTIABLE)
TDD mandatory: Tests written → User approved → Tests fail → Then implement; Red-Green-Refactor cycle strictly enforced; All features must have comprehensive test coverage; Integration tests required for HTMX interactions.

### V. Security-First Development
Security considerations MUST be integrated from the beginning; All user inputs MUST be validated and sanitized; CSRF protection enabled by default; Secure headers implemented; Authentication and authorization properly configured; Regular security audits required.

### VI. Data Security and Privacy (NON-NEGOTIABLE)
All uploaded datasets MUST be thoroughly sanitized to remove malicious content, formulas, and macros; Sensitive user information MUST be masked or anonymized during processing; UTF-8 encoding issues MUST be handled gracefully; All file processing errors MUST be displayed clearly in the UI; No sensitive data MUST be logged or stored in plain text; Data retention policies MUST be enforced.

### VII. Dataset Column Type Management (NON-NEGOTIABLE)
Every dataset MUST have its columns automatically categorized as numeric, categorical, or date/time format; Column type information MUST be stored globally and passed to all analysis tools; Tool parameters MUST be validated against column types; Type mismatches MUST be handled gracefully with clear error messages; Column metadata MUST be preserved throughout the analysis pipeline.

### VIII. Analysis History Management (NON-NEGOTIABLE)
All analysis sessions MUST be tagged to specific datasets; When users switch datasets, analysis sessions MUST automatically change and load previous analysis results; Analysis history MUST be preserved and accessible in card-based UI; Previous analysis results MUST be restored to workspace when switching back to a dataset; Analysis continuity MUST be maintained across dataset switches; All analysis results MUST be wrapped in cards for consistent UI presentation.

### IX. REST API Architecture (NON-NEGOTIABLE)
All system entry points, tool execution points, and deliverables MUST be designed through REST API; Django REST Framework MUST be used for all API endpoints; All HTMX interactions MUST target REST API endpoints; No direct database access from frontend; All business logic MUST be encapsulated in API views; API responses MUST be consistent and well-documented; All endpoints MUST follow RESTful conventions.

### X. Django Authentication System (NON-NEGOTIABLE)
Django's default authentication system MUST be used exclusively; Built-in sign-in and sign-up system MUST be implemented; No custom authentication solutions allowed; User sessions MUST be managed through Django's session framework; CSRF protection MUST be enabled for all authenticated endpoints; Authentication state MUST be properly validated in all API calls.

### XI. HTMX Error Prevention (NON-NEGOTIABLE)
All HTMX targets MUST be validated before implementation; HTMX request/response cycles MUST be tested thoroughly; No HTMX target errors allowed in production; All HTMX interactions MUST have proper error handling; HTMX partial updates MUST be tested for all scenarios; HTMX loading states MUST be implemented for all requests; All HTMX attributes MUST be validated and tested.

### XII. Virtual Environment Activation (NON-NEGOTIABLE)
Virtual environment MUST be activated for ALL terminal tasks and operations; No Python commands, package installations, or Django operations allowed without active virtual environment; Virtual environment activation MUST be verified before any development work; All team members MUST ensure virtual environment is active before starting any task; Virtual environment status MUST be checked and confirmed in all documentation and workflows; This is CRITICAL for dependency isolation and project consistency.

### XIII. Google AI Integration and Token Management (NON-NEGOTIABLE)
Google API key MUST be used for all LLM operations with no token or rate limits; Token calculation MUST be performed for every AI input and output; Token usage MUST be stored in user database records; Maximum token limit per user MUST be enforced; Token tracking MUST be accurate and real-time; User token consumption MUST be monitored and displayed; Token limits MUST prevent excessive usage; Default token limits MUST be configured for new users; This is CRITICAL for cost control and fair usage.

### XIV. Error Handling & Recovery (NON-NEGOTIABLE)
All system errors MUST have graceful degradation; Failed operations MUST be retryable; User data MUST never be lost due to errors; Error recovery MUST be automatic where possible; Critical operations MUST have rollback capabilities; Error notifications MUST be user-friendly and actionable; System MUST maintain consistency during error states; All errors MUST be logged with correlation IDs; Error recovery procedures MUST be documented and tested.

### XV. Data Backup & Recovery (NON-NEGOTIABLE)
Automated daily backups MUST be performed for all user data; Analysis results MUST be backed up before major operations; Database migration rollback procedures MUST be implemented; User data export capabilities MUST be provided; Backup integrity MUST be verified regularly; Recovery procedures MUST be tested and documented; Data loss prevention MUST be prioritized; Backup retention policies MUST be enforced.

### XVI. Performance Monitoring & Alerting (NON-NEGOTIABLE)
Real-time performance metrics MUST be collected and displayed; Token usage alerts MUST be sent when approaching limits; System resource monitoring MUST be continuous; Automated alerting MUST be configured for critical issues; Performance baselines MUST be established; Response time monitoring MUST be implemented; Resource usage tracking MUST be comprehensive; Alert escalation procedures MUST be defined.

### XVII. API Protection & Rate Limiting (NON-NEGOTIABLE)
Per-user API rate limiting MUST be implemented; Request throttling MUST be applied for heavy operations; DDoS protection measures MUST be in place; API usage analytics MUST be collected; Rate limit violations MUST be logged and monitored; API abuse prevention MUST be enforced; Request validation MUST be comprehensive; API security headers MUST be implemented.

### XVIII. Data Retention & User Storage Management (NON-NEGOTIABLE)
User storage limit MUST be set to 250MB per user; Storage usage warnings MUST be sent when approaching limits; Users MUST be able to delete their own files and analysis results; Deletion MUST be permanent and immediate; Storage usage MUST be displayed to users; Old analysis results MUST be automatically archived when limit reached; User data export MUST be available before deletion; Storage cleanup procedures MUST be automated.

### XIX. Audit Trail & Compliance (NON-NEGOTIABLE)
All user actions MUST be logged in comprehensive audit trail; All system events MUST be logged for compliance; Sensitive data MUST be masked in audit logs; Audit logs MUST be retained for compliance period; Audit logs MUST be immutable once created; All actions MUST have correlation IDs for tracking; User IP addresses MUST be logged; API requests and responses MUST be logged; All errors MUST be logged with full context; Compliance reports MUST be available for audit; Audit trail export MUST be available in multiple formats; This is CRITICAL for security, compliance, and accountability.

### XX. Requirements Management & Dependency Installation (NON-NEGOTIABLE)
A comprehensive requirements.txt file MUST be generated and maintained; All dependencies MUST be pinned to specific versions; Requirements.txt MUST be installed before any development work; Virtual environment MUST be activated before installing requirements; All package versions MUST be compatible and tested; Development dependencies MUST be separated from production dependencies; Requirements.txt MUST be updated whenever new packages are added; This is CRITICAL for reproducible builds and dependency management.

### XXI. Data Analysis Library Requirements (NON-NEGOTIABLE)
Pandas-ai MUST NOT be used in production; Only standard pandas library MUST be used for data analysis; Lifelines library MUST be used for survival analysis; Matplotlib MUST be used for plotting with Agg backend; Seaborn MUST be used for statistical data visualization; Matplotlib Agg method MUST be used for all plotting operations; No interactive plotting libraries allowed in production; All visualizations MUST be generated server-side; This is CRITICAL for production stability and performance.

### XXII. Code Organization & Architecture (NON-NEGOTIABLE)
Tools MUST be organized in a dedicated 'tools' subfolder with individual files; Views.py MUST be separated into task-specific modules; Each tool MUST have its own file in the tools subfolder; View modules MUST be imported and called from main views.py; LLM context caching MUST be implemented; Last 10 messages from current analysis session MUST be used as LLM context; All chat messages MUST be stored for context retrieval; Context MUST be session-specific and automatically updated; This is CRITICAL for maintainable code and intelligent AI responses.

### XXIII. LLM Batch Processing & Response Formatting (NON-NEGOTIABLE)
LLM batch API calling MUST be enabled for efficient processing; Analysis results MUST be passed to LLM in proper format; LLM responses MUST be formatted correctly (tables as tables, images as PNG); Generated images MUST be stored in accessible media directory; Images MUST be passed to LLM via base64 encoding or file references; Image storage MUST be organized by session and analysis ID; Image URLs MUST be accessible via web endpoints; LLM responses MUST include proper formatting for different content types; This is CRITICAL for intelligent analysis interpretation and proper content delivery.

### XXIV. LangChain Sandbox & Code Execution (NON-NEGOTIABLE)
LangChain sandbox MUST be implemented for secure code execution; User queries MUST be processed by LLM to generate Python code; Generated code MUST be executed in isolated, secured sandbox environment; Sandbox MUST have restricted access to system resources; Code execution MUST be time-limited and memory-constrained; Only approved libraries MUST be available in sandbox; Sandbox MUST return results to users via chat interface; Error handling MUST provide LLM feedback for code correction; Sandbox MUST be completely hidden from users; This is CRITICAL for dynamic analysis capabilities and user safety.

### XXV. Report Generation & Document Export (NON-NEGOTIABLE)
Professional report generation MUST be implemented for analysis sessions; Reports MUST be generated in Microsoft Word format with beautiful design; Users MUST have control over report content selection; All analysis results MUST be included (tools results, charts, tables, interpretations); LLM responses and suggestions MUST be included in reports; Report templates MUST be customizable and professional; Download functionality MUST be available for generated reports; Report generation MUST be asynchronous for large sessions; This is CRITICAL for professional analysis documentation and client deliverables.

### XXVI. Performance Optimization & Memory Efficiency (NON-NEGOTIABLE)
Memory usage MUST be optimized for large datasets; Lazy loading MUST be implemented for all data operations; Pagination MUST be used for large result sets; Data streaming MUST be implemented for file processing; Memory cleanup MUST be automatic after operations; RAM usage MUST be monitored and limited per operation; Caching strategies MUST be implemented for frequently accessed data; Database queries MUST be optimized with select_related and prefetch_related; Image compression MUST be automatic for generated visualizations; Session data MUST be cleaned up automatically; This is CRITICAL for system performance and user experience.

### XXVII. Celery Background Task Processing (NON-NEGOTIABLE)
Celery MUST be implemented for all heavy operations; File processing MUST be handled asynchronously; Report generation MUST be background tasks; LLM batch processing MUST use Celery workers; Sandbox code execution MUST be queued tasks; Image processing MUST be background operations; Data analysis MUST be distributed across workers; Backup operations MUST be scheduled tasks; Task monitoring MUST be implemented with Celery Flower; Task retry mechanisms MUST be configured; Task prioritization MUST be implemented; Worker scaling MUST be configurable; This is CRITICAL for system scalability and user experience.

### XXVIII. Agentic AI System (NON-NEGOTIABLE)
Agentic AI MUST be implemented for end-to-end autonomous analysis; Agent controller layer MUST orchestrate analysis workflows; AgentRun model MUST track autonomous analysis sessions; AgentStep model MUST track individual agent actions; LLM MUST plan analysis strategies autonomously; Agent MUST execute analysis tools iteratively; Agent MUST adapt strategy based on results; Agent MUST respect resource constraints (max_steps, max_cost, max_time); Agent MUST provide human-readable explanations; Agent MUST handle errors and retry intelligently; This is CRITICAL for transforming the system into a truly autonomous AI platform.

### XXIX. RAG (Retrieval-Augmented Generation) System with Redis Vector Database (NON-NEGOTIABLE)
RAG system MUST be implemented using Redis as the vector database; Redis MUST store all vector embeddings with 'analytical:rag:' key prefix; Dataset-aware indexing MUST be implemented for per-dataset knowledge; Global knowledge indexing MUST be implemented for tool documentation and patterns; VectorNote model MUST store embeddings, metadata, and content; RAG retrieval MUST be integrated into agent planning and execution phases; All RAG queries MUST be logged in audit trail with correlation IDs; RAG token usage MUST be tracked in existing token management system; Multi-tenancy MUST be enforced with dataset_id filtering; PII masking MUST be implemented for all indexed content; RAG search results MUST be integrated into LLM context; This is CRITICAL for grounding agent outputs in real facts and reducing hallucinations.

## Technology Stack & Configuration

### Backend Requirements
- **Framework**: Django (latest stable version)
- **API Framework**: Django REST Framework (mandatory)
- **Authentication**: Django's built-in authentication system (exclusive)
- **Database**: PostgreSQL (metadata & results) + Parquet files (dataset content) + Redis (analytical key prefix + vector database for RAG)
- **Configuration**: All settings in settings.py (no .env files)
- **Task Queue**: Celery with Redis broker (NON-NEGOTIABLE)
- **Task Monitoring**: Celery Flower for task monitoring and management
- **AI Integration**: Google AI API with API key authentication
- **Token Management**: Real-time token calculation and tracking
- **Monitoring**: Performance monitoring and alerting system
- **Backup**: Automated backup and recovery system
- **Security**: Django's built-in security features + additional hardening
- **Testing**: Django TestCase + pytest for comprehensive coverage

### Frontend Requirements
- **Interactivity**: HTMX only (no JavaScript)
- **Styling**: Bootstrap 5+ with custom dark theme
- **Design Pattern**: Card-based layout for all components
- **Color Scheme**: Dark theme with eye-soothing colors
- **Responsiveness**: Mobile-first design approach

### Development Environment
- **Virtual Environment**: ALWAYS activated during development (NON-NEGOTIABLE)
- **Dependencies**: Requirements.txt for package management
- **Code Quality**: Black for formatting, flake8 for linting
- **Version Control**: Git with conventional commit messages
- **Environment Verification**: Virtual environment status MUST be confirmed before any task

## Design Standards & UI Guidelines

### Dark Theme Color Palette
- **Primary Background**: Deep dark (#1a1a1a or similar)
- **Secondary Background**: Slightly lighter dark (#2d2d2d)
- **Card Background**: Dark with subtle contrast (#333333)
- **Text**: Light colors (#ffffff, #e0e0e0)
- **Accent Colors**: Vibrant but not harsh (avoid pure white/cream)
- **Borders**: Subtle dark borders for definition

### Card-Based Design Rules
- All content MUST be contained within Bootstrap cards
- Cards MUST have subtle shadows and rounded corners
- Consistent spacing between cards (Bootstrap spacing utilities)
- Cards MUST be responsive and stack properly on mobile
- Each card MUST have a clear purpose and single responsibility

### HTMX Implementation Standards
- All forms MUST use HTMX for submission
- Page updates MUST be partial (no full page reloads)
- Loading states MUST be implemented for all HTMX requests
- Error handling MUST be graceful with user feedback
- HTMX attributes MUST be semantic and well-documented

## Governance

### Constitution Authority
This constitution supersedes all other development practices and guidelines; All team members MUST follow these rules without exception; Amendments require documentation, team approval, and migration plan; Constitution violations MUST be addressed immediately.

### Compliance Requirements
- All pull requests MUST verify constitution compliance
- Code reviews MUST check adherence to HTMX-only rule
- Design reviews MUST validate dark theme and card-based layout
- Security reviews MUST ensure top-notch standards are met
- Data security reviews MUST verify file sanitization and privacy protection
- Column type management MUST be validated in all analysis tools
- Analysis history management MUST be tested for dataset switching
- Card-based UI MUST be enforced for all analysis results
- REST API architecture MUST be validated for all endpoints
- Django authentication MUST be used exclusively
- HTMX error prevention MUST be tested for all interactions
- Virtual environment activation MUST be verified for all terminal operations
- Google AI integration MUST be validated for all LLM operations
- Token management MUST be tested for accuracy and limits
- Error handling and recovery MUST be tested for all operations
- Data backup and recovery MUST be validated regularly
- Performance monitoring MUST be verified for all critical paths
- API protection and rate limiting MUST be tested
- Data retention and storage management MUST be validated
- Error handling MUST be tested for all file processing operations
- All new features MUST follow TDD principles

### Quality Gates
- No JavaScript code allowed in the codebase
- All UI components MUST use Bootstrap with dark theme
- All interactive features MUST use HTMX
- All system entry points MUST use REST API
- Django authentication MUST be used exclusively
- Virtual environment MUST be activated for all operations
- Google AI API MUST be used for all LLM operations
- Token calculation MUST be accurate for all AI interactions
- User token limits MUST be enforced
- Error handling and recovery MUST be implemented
- Data backup and recovery MUST be functional
- Performance monitoring MUST be operational
- API protection and rate limiting MUST be active
- User storage limits MUST be enforced (250MB)
- No HTMX target errors allowed in production
- Security standards MUST be maintained
- Data sanitization MUST be implemented for all file uploads
- Column type detection MUST work for all supported file formats
- Analysis history MUST be preserved across dataset switches
- All analysis results MUST be displayed in cards
- Error messages MUST be user-friendly and actionable
- Test coverage MUST meet minimum requirements

### Development Workflow
1. **Environment Setup**: Activate virtual environment (CRITICAL FIRST STEP)
2. **Dependencies**: Install requirements.txt (MANDATORY BEFORE CODING)
3. **Planning**: Review constitution requirements before starting
4. **Development**: Follow TDD and constitution rules
4. **Review**: Verify compliance with all constitution rules
5. **Testing**: Ensure all tests pass and coverage is adequate
6. **Deployment**: Only deploy constitution-compliant code

**Version**: 1.1.0 | **Ratified**: 2024-12-19 | **Last Amended**: 2024-12-19