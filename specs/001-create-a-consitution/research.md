# Research Findings: Data Analysis System

**Date**: 2024-12-19  
**Feature**: Data Analysis System with Django + HTMX  
**Research Scope**: Technology choices, best practices, and implementation patterns

## Research Tasks & Findings

### 1. Django + HTMX Integration Patterns
**Task**: Research Django + HTMX integration patterns for data analysis applications

**Decision**: Use Django Class-Based Views with HTMX partial templates  
**Rationale**: 
- Class-Based Views provide better organization for complex data operations
- HTMX partial templates enable seamless partial page updates
- Django's built-in CSRF protection works seamlessly with HTMX
- Template inheritance allows for consistent dark theme implementation

**Alternatives considered**:
- Function-based views: Less organized for complex data operations
- Full page reloads: Violates HTMX-first principle
- JavaScript frameworks: Violates constitution requirements

### 2. File Upload and Security Sanitization
**Task**: Research secure file upload and sanitization for XLS, CSV, JSON files

**Decision**: Use django-cleanup + custom sanitization pipeline + sensitive data detection  
**Rationale**:
- django-cleanup provides automatic file cleanup
- Custom sanitization removes formulas, macros, and malicious content
- Pandas provides robust file parsing with security options
- PyArrow ensures safe Parquet conversion
- Sensitive data detection and masking for privacy protection
- UTF-8 encoding handling for international data

**Alternatives considered**:
- Direct file processing: Security risks with malicious files
- Third-party sanitization services: Additional complexity and cost
- Client-side validation only: Insufficient security

### 3. Database Selection
**Task**: Research database options for data analysis applications

**Decision**: Use PostgreSQL as primary database  
**Rationale**:
- PostgreSQL provides robust ACID compliance and data integrity
- Excellent support for complex queries and analytical workloads
- JSON field support for flexible data storage
- Strong performance with large datasets
- Production-ready with comprehensive backup and recovery
- Better than SQLite for concurrent users and production deployment

**Alternatives considered**:
- SQLite: Limited concurrency, not suitable for production
- MySQL: Good but PostgreSQL has better analytical features
- MongoDB: NoSQL not suitable for structured analytical data

### 4. Hybrid Data Storage Architecture
**Task**: Research optimal data storage strategy for analytical workloads

**Decision**: Use PostgreSQL + Parquet hybrid architecture  
**Rationale**:
- **PostgreSQL**: Metadata, user data, analysis results, audit trails, session management
- **Parquet**: Raw dataset files for fast analytical processing
- **Best of Both**: Relational integrity + analytical performance
- **Separation of Concerns**: Structured data in PostgreSQL, analytical data in Parquet
- **Performance**: PostgreSQL for queries, Parquet for data analysis operations

**Architecture**:
- **PostgreSQL**: User accounts, datasets metadata, analysis results, audit trails, agent runs
- **Parquet Files**: Actual dataset content (uploaded files converted to Parquet)
- **Redis**: Caching layer with "analytical" key prefix for session data and analysis results

**Alternatives considered**:
- PostgreSQL only: Slower for large analytical operations
- Parquet only: No relational integrity, complex metadata management
- MongoDB: NoSQL not suitable for structured analytical workflows

### 4. LangChain Tool Registry Implementation
**Task**: Research LangChain tool registry patterns for dynamic analysis tools

**Decision**: Use LangChain Tool class with Django model integration  
**Rationale**:
- LangChain provides standardized tool interface
- Django models store tool metadata and parameters
- Dynamic tool registration enables extensibility
- Synchronous execution maintains simplicity

**Alternatives considered**:
- Custom tool system: Reinventing existing solutions
- Asynchronous execution: Adds complexity without clear benefits
- Hardcoded tools: Reduces flexibility and extensibility

### 5. Session and Cache Management
**Task**: Research session and cache management for multi-user data analysis

**Decision**: Use Django sessions + Redis caching + database storage  
**Rationale**:
- Django sessions provide user-specific state management
- Redis enables fast caching of analysis results
- Database storage ensures persistence and audit trails
- Dataset-specific sessions enable proper isolation

**Alternatives considered**:
- File-based sessions: Poor scalability and security
- Memory-only caching: Data loss on restart
- Single global session: No user isolation

### 6. Three-Panel UI with Draggable Resizing
**Task**: Research HTMX-based draggable panel resizing without JavaScript

**Decision**: Use CSS Grid + HTMX for panel management  
**Rationale**:
- CSS Grid provides flexible layout system
- HTMX handles panel state updates
- Bootstrap 5+ provides responsive grid utilities
- No JavaScript required, maintaining constitution compliance

**Alternatives considered**:
- JavaScript drag libraries: Violates HTMX-first principle
- Fixed panel sizes: Poor user experience
- Server-side only resizing: Limited interactivity

### 7. Dark Theme Implementation with Bootstrap
**Task**: Research Bootstrap 5+ dark theme customization for Cursor AI look

**Decision**: Use Bootstrap 5+ with custom CSS variables and dark theme  
**Rationale**:
- Bootstrap 5+ provides excellent dark theme support
- CSS variables enable easy theme customization
- Card-based components align with design requirements
- Mobile-first responsive design

**Alternatives considered**:
- Custom CSS framework: Reinventing existing solutions
- Light theme: Violates constitution requirements
- Third-party theme libraries: Additional dependencies

### 8. Data Analysis Tool Integration
**Task**: Research integration patterns for statistical analysis tools

**Decision**: Use standard pandas + specialized libraries for production analysis  
**Rationale**:
- Standard pandas provides reliable, production-ready data analysis
- Lifelines library for specialized survival analysis
- Matplotlib with Agg backend for server-side plotting
- Seaborn for statistical data visualization
- No pandas-ai dependency for production stability
- Google AI API for interpretation and insights only

**Alternatives considered**:
- pandas-ai: Not suitable for production due to stability concerns
- Interactive plotting libraries: Not suitable for server-side generation
- Other visualization libraries: Matplotlib/Seaborn provide comprehensive coverage

### 9. Column Type Management and Categorization
**Task**: Research automatic column type detection and categorization for analysis tools

**Decision**: Use pandas dtype detection + custom categorization logic  
**Rationale**:
- Pandas provides robust dtype detection for various data types
- Custom categorization logic for numeric, categorical, and datetime columns
- Global storage enables tool parameter validation
- Type mismatch handling with user-friendly error messages

**Alternatives considered**:
- Manual column type specification: Poor user experience
- Third-party type detection: Additional dependencies
- No type validation: Increased error rates

### 10. Error Handling and User Experience
**Task**: Research error handling patterns for file processing and analysis operations

**Decision**: Use structured error tracking with user-friendly messages  
**Rationale**:
- FileProcessingError entity for comprehensive error tracking
- User-friendly error messages for different error types
- Technical details for debugging and support
- Error severity levels for prioritization

**Alternatives considered**:
- Generic error messages: Poor user experience
- Technical error details only: Confusing for users
- No error tracking: Difficult to debug issues

### 11. Analysis History Management and Dataset Switching
**Task**: Research analysis history management for dataset-tagged sessions

**Decision**: Use dataset-tagged sessions with analysis history tracking  
**Rationale**:
- AnalysisSession tagged to specific datasets for automatic switching
- AnalysisHistory entity tracks analysis results with card positions
- Workspace state preservation across dataset switches
- Card-based UI for consistent analysis result presentation
- Automatic restoration of previous analysis when switching back

**Alternatives considered**:
- Global analysis history: No dataset context
- Manual session management: Poor user experience
- No history preservation: Loss of analysis continuity

### 12. REST API Architecture with Django REST Framework
**Task**: Research REST API design patterns for Django + HTMX integration

**Decision**: Use Django REST Framework for all API endpoints  
**Rationale**:
- DRF provides robust API framework with built-in serialization
- Consistent API responses and error handling
- Built-in authentication and permissions
- HTMX can easily target REST API endpoints
- No direct database access from frontend
- Business logic encapsulated in API views

**Alternatives considered**:
- Custom API views: Reinventing existing solutions
- Direct database access: Security and maintainability issues
- GraphQL: Overkill for this use case

### 13. Django Authentication System Integration
**Task**: Research Django's built-in authentication for REST API integration

**Decision**: Use Django's default authentication system exclusively  
**Rationale**:
- Built-in User model provides all necessary fields
- Session-based authentication works well with HTMX
- CSRF protection built-in for security
- No need for custom authentication solutions
- Django admin integration for user management

**Alternatives considered**:
- Custom authentication: Unnecessary complexity
- JWT tokens: Overkill for session-based app
- Third-party auth: Additional dependencies

### 14. HTMX Error Prevention and Testing
**Task**: Research HTMX error prevention and testing strategies

**Decision**: Use comprehensive HTMX testing and validation  
**Rationale**:
- Target validation prevents HTMX target errors
- Request/response cycle testing ensures reliability
- Error handling for all HTMX interactions
- Loading states improve user experience
- Attribute validation prevents runtime errors

**Alternatives considered**:
- No HTMX testing: High error rates
- Manual testing only: Inefficient and error-prone
- JavaScript fallbacks: Violates HTMX-only principle

### 15. Virtual Environment Management (CRITICAL)
**Task**: Research virtual environment best practices for Python development

**Decision**: Mandatory virtual environment activation for all operations  
**Rationale**:
- Dependency isolation prevents conflicts
- Project consistency across team members
- Reproducible development environment
- Prevents system-wide package pollution
- Critical for Python project stability

**Alternatives considered**:
- Global package installation: Dependency conflicts
- Conda environments: Additional complexity
- Docker only: Overkill for development

### 16. Error Handling & Recovery Systems
**Task**: Research comprehensive error handling and recovery strategies

**Decision**: Multi-layered error handling with automatic recovery  
**Rationale**:
- Graceful degradation prevents system crashes
- Automatic recovery reduces manual intervention
- User data protection is critical
- Error correlation IDs enable better debugging
- Rollback capabilities prevent data loss

**Implementation**:
- Structured error logging with correlation IDs
- Automatic retry mechanisms for transient failures
- User-friendly error messages
- System consistency maintenance during errors
- Comprehensive error recovery procedures

### 17. Data Backup & Recovery Systems
**Task**: Research backup and recovery strategies for user data

**Decision**: Automated daily backups with integrity verification  
**Rationale**:
- Data loss prevention is critical
- Automated backups ensure consistency
- Integrity verification prevents corruption
- Recovery procedures must be tested
- User data export capabilities required

**Implementation**:
- Daily automated backups of all user data
- Pre-operation backup of analysis results
- Database migration rollback procedures
- User data export functionality
- Backup integrity verification
- Tested recovery procedures

### 18. Performance Monitoring & Alerting
**Task**: Research performance monitoring and alerting systems

**Decision**: Real-time monitoring with automated alerting  
**Rationale**:
- Proactive issue detection
- Performance baseline establishment
- Resource usage optimization
- Critical issue escalation
- User experience maintenance

**Implementation**:
- Real-time performance metrics collection
- Token usage monitoring and alerts
- System resource tracking
- Automated alerting for critical issues
- Performance baseline establishment
- Response time monitoring

### 19. API Protection & Rate Limiting
**Task**: Research API protection and rate limiting strategies

**Decision**: Per-user rate limiting with comprehensive protection  
**Rationale**:
- API abuse prevention
- Resource protection
- Fair usage enforcement
- DDoS protection
- Usage analytics for optimization

**Implementation**:
- Per-user API rate limiting
- Request throttling for heavy operations
- DDoS protection measures
- API usage analytics
- Rate limit violation logging
- Comprehensive request validation

### 20. Data Retention & User Storage Management
**Task**: Research data retention and storage management strategies

**Decision**: 250MB per user with automated cleanup  
**Rationale**:
- Storage cost control
- User data management
- Automated cleanup reduces manual work
- User-controlled deletion provides flexibility
- Storage usage transparency

**Implementation**:
- 250MB storage limit per user
- Storage usage warnings at 80% and 90%
- User-controlled file and analysis deletion
- Automated cleanup of old results
- Storage usage display to users
- Data export before deletion

### 21. Audit Trail & Compliance Systems
**Task**: Research comprehensive audit trail and compliance systems

**Decision**: Comprehensive audit logging with compliance reporting  
**Rationale**:
- Security and accountability requirements
- Regulatory compliance needs
- Forensic analysis capabilities
- User action tracking
- System event monitoring

**Implementation**:
- All user actions logged with correlation IDs
- System events tracked for compliance
- Sensitive data masking in logs
- Immutable audit records
- IP address and user agent tracking
- Request/response logging
- Compliance report generation
- Multi-format audit export

### 22. Data Visualization Libraries for Production
**Task**: Research production-suitable data visualization libraries

**Decision**: Use matplotlib with Agg backend + seaborn for statistical visualization  
**Rationale**:
- Matplotlib Agg backend enables server-side plotting without GUI dependencies
- Seaborn provides statistical data visualization capabilities
- Lifelines library for specialized survival analysis
- No interactive plotting libraries for production stability
- Server-side generation ensures consistent output across environments
- High-quality PNG output suitable for web display

**Implementation**:
- Matplotlib.use('Agg') must be set before any plotting
- All plots generated server-side and saved as PNG files
- Seaborn for statistical plots (distributions, correlations, regressions)
- Lifelines for survival analysis and time-to-event modeling
- No pandas-ai dependency for production stability

**Alternatives considered**:
- Plotly: Interactive plotting not suitable for server-side generation
- Bokeh: Overkill for static statistical visualizations
- pandas-ai: Not production-ready, stability concerns
- Interactive matplotlib backends: Require GUI dependencies

### 23. Code Organization & LLM Context Management
**Task**: Research code organization patterns and LLM context management strategies

**Decision**: Modular tool organization with separated views and intelligent context caching  
**Rationale**:
- Maintainable code structure with clear separation of concerns
- Individual tool files enable easy testing and maintenance
- Separated views prevent large, unmanageable files
- LLM context caching enables intelligent, contextual AI responses
- Last 10 messages provide optimal context without overwhelming the LLM

**Implementation**:
- Tools organized in dedicated 'tools' subfolder with individual files
- Views separated into task-specific modules (dataset_views, analysis_views, chat_views)
- Main views.py imports and calls from separated modules
- LLMContextCache entity for storing session-specific context
- Automatic context updates with last 10 messages
- Context hashing for efficient comparison and updates

**Alternatives considered**:
- Monolithic views.py: Becomes unmanageable as project grows
- Single tool file: Difficult to maintain and test individual tools
- No context caching: AI responses lack continuity and intelligence
- Unlimited context: Overwhelms LLM and increases costs

### 24. LLM Batch Processing & Image Management
**Task**: Research LLM batch processing and image handling for analysis results

**Decision**: Implement batch API processing with comprehensive image management  
**Rationale**:
- Batch processing reduces API calls and improves efficiency
- Images need proper storage, organization, and LLM integration
- Base64 encoding enables image processing by LLMs
- Session-based organization ensures proper access control
- Multiple format support (base64, URL, file path) for different use cases

**Implementation**:
- LLMBatchProcessor for efficient batch processing
- ImageManager for comprehensive image handling
- GeneratedImage entity for database storage
- Base64 encoding for LLM image processing
- Session-based image organization
- Web-accessible URLs for image display
- Automatic cleanup of expired images

**Image Processing Flow**:
1. Tool generates image using matplotlib Agg backend
2. ImageManager saves image with metadata
3. Base64 encoding generated for LLM processing
4. Image stored in session-specific directory
5. Database record created with access URL
6. LLM processes image via base64 or URL reference
7. Response formatted with proper image descriptions

**Alternatives considered**:
- Individual API calls: Less efficient, higher costs
- No image storage: Images lost after generation
- File-only storage: No LLM integration capability
- Single format: Limited flexibility for different use cases

### 25. LangChain Sandbox & Code Execution
**Task**: Research secure code execution sandbox for dynamic analysis

**Decision**: Implement LangChain sandbox with comprehensive security and resource management  
**Rationale**:
- Dynamic code execution enables flexible analysis capabilities
- Security is critical to prevent system compromise
- Resource limits prevent abuse and system overload
- LLM integration provides intelligent error correction
- Hidden execution maintains clean user experience

**Implementation**:
- SandboxExecutor for secure code execution
- SandboxSecurity for code validation and sanitization
- Resource limits (memory, CPU time, execution time)
- Approved library whitelist with blocked imports/functions
- Subprocess isolation with temporary directories
- LLM-powered error correction and suggestions
- Execution tracking and history management

**Security Features**:
- Blocked dangerous imports (os, sys, subprocess, eval, exec)
- Blocked dangerous functions (eval, exec, compile, open)
- Resource limits (512MB memory, 30s execution time)
- Temporary directory isolation
- Process-level security restrictions
- Code validation before execution

**Execution Flow**:
1. User submits query via chat interface
2. LLM generates secure Python code
3. Code validation checks for security violations
4. Code executed in isolated subprocess
5. Results parsed and formatted for user
6. Images/tables generated and stored
7. Error handling with LLM suggestions

**Alternatives considered**:
- No sandbox: Security risk, system compromise possible
- Docker containers: Overhead, complexity
- Jupyter kernels: Security concerns, resource management
- External services: Latency, dependency, costs

### 26. Performance Optimization & Memory Efficiency
**Task**: Research performance optimization and memory efficiency strategies

**Decision**: Implement comprehensive performance optimization with memory management  
**Rationale**:
- Large datasets require efficient memory management
- User experience depends on fast response times
- System stability requires resource monitoring
- Scalability requires optimized data processing
- Cost efficiency requires resource optimization

**Implementation**:
- PerformanceOptimizer for memory monitoring and cleanup
- LazyDataLoader for large dataset processing
- ImageOptimizer for visualization efficiency
- Database query optimization with select_related/prefetch_related
- Automatic memory cleanup and garbage collection
- Background monitoring and emergency cleanup
- Data compression for caching and storage
- Pagination for large result sets
- Streaming for file processing

**Memory Optimization Features**:
- DataFrame memory optimization (category conversion, downcasting)
- Image compression and resizing
- Lazy loading for large datasets
- Automatic session data cleanup
- Emergency memory cleanup at 85% usage
- Background monitoring thread
- Compressed caching for large data

**User Experience Improvements**:
- Progress indicators for long operations
- Lazy loading with pagination
- Thumbnail generation for images
- Streaming file uploads
- Background processing for heavy operations
- Real-time performance monitoring
- Automatic resource cleanup

**Alternatives considered**:
- No optimization: Poor performance with large datasets
- Client-side optimization only: Insufficient for server-side processing
- Manual memory management: Error-prone and inefficient
- No monitoring: System instability and poor user experience

### 27. Celery Background Task Processing
**Task**: Research Celery integration for background task processing

**Decision**: Implement comprehensive Celery integration with Redis broker  
**Rationale**:
- Heavy operations require background processing to maintain UI responsiveness
- File processing, report generation, and LLM operations are time-consuming
- Scalability requires distributed task processing
- User experience depends on non-blocking operations
- System reliability requires task retry mechanisms and monitoring

**Implementation**:
- Celery with Redis broker for task queue management
- Flower for task monitoring and management
- Task routing and prioritization for different operation types
- Retry mechanisms with exponential backoff
- Periodic tasks for maintenance operations
- Worker scaling and resource management
- Task result storage and retrieval

**Task Categories**:
- File Processing: XLS/CSV/JSON to Parquet conversion
- Analysis Execution: Statistical tool execution
- LLM Processing: Batch processing and response generation
- Sandbox Execution: Secure code execution
- Report Generation: Word document creation
- Image Processing: Chart generation and optimization
- Backup Operations: Automated backup and recovery
- Monitoring: System health checks and cleanup

**Queue Configuration**:
- file_processing: High priority, dedicated workers
- analysis: Medium priority, multiple workers
- llm_processing: Medium priority, limited concurrency
- sandbox: Low priority, isolated workers
- reports: Low priority, single worker
- image_processing: Medium priority, multiple workers
- backup: Low priority, scheduled execution
- monitoring: High priority, frequent execution

**Monitoring Features**:
- Real-time task status and progress
- Worker performance metrics
- Queue length and processing times
- Error rates and retry statistics
- Resource usage monitoring
- Task success/failure tracking

**Alternatives considered**:
- Django-Q: Less mature, limited features
- RQ (Redis Queue): Simpler but less powerful
- Direct threading: Complex, error-prone
- Synchronous processing: Poor user experience
- External services: Dependency, latency, costs

### 16. Google AI Integration and Token Management
**Task**: Research Google AI API integration with token tracking and user limits

**Decision**: Use Google AI API with comprehensive token management  
**Rationale**:
- Google AI API provides enterprise-grade LLM capabilities
- No rate limits or token restrictions on API usage
- Real-time token calculation for cost control
- User-specific token limits prevent excessive usage
- Token usage tracking for monitoring and billing

**Alternatives considered**:
- OpenAI API: Rate limits and token restrictions
- Anthropic API: Limited availability and higher costs
- Local models: Limited capabilities and resource requirements

## Technology Stack Summary

### Backend
- **Framework**: Django 4.2+ (latest stable)
- **API Framework**: Django REST Framework 3.14+ (mandatory)
- **Authentication**: Django's built-in authentication (exclusive)
- **Database**: SQLite (development), PostgreSQL (production)
- **Caching**: Redis
- **File Processing**: Pandas, PyArrow, openpyxl, python-json
- **AI Integration**: LangChain, pandas-ai, Google AI API
- **Security**: django-cleanup, bleach, cryptography
- **Data Privacy**: faker (for data masking), regex (for PII detection)
- **Error Handling**: structlog (for structured logging)

### Frontend
- **Interactivity**: HTMX 1.9+
- **Styling**: Bootstrap 5+ with custom dark theme
- **Layout**: CSS Grid for three-panel design
- **Icons**: Bootstrap Icons

### Development
- **Testing**: pytest, Django TestCase
- **Code Quality**: Black, flake8, mypy
- **Virtual Environment**: venv (ALWAYS activated - NON-NEGOTIABLE)
- **Environment Management**: Virtual environment verification required

## Implementation Patterns

### File Upload Pipeline
1. HTMX form submission → Django view
2. File validation and sanitization
3. Pandas parsing with security checks
4. Formula/macro removal
5. Parquet conversion and storage
6. Column type detection and storage
7. HTMX partial update of UI

### Analysis Tool Execution
1. User selects tool from left panel
2. HTMX loads dynamic parameter modal
3. User fills parameters and submits
4. LangChain tool execution
5. Results cached in Redis
6. HTMX updates middle panel with results
7. AI interpretation available in right panel

### Session Management
1. User-specific Django session
2. Dataset-specific session override
3. Analysis results cached by session + tool + parameters
4. Session changes trigger cache invalidation
5. Database persistence for audit and recovery

## Security Considerations

### File Security
- File type validation (XLS, CSV, JSON only)
- Size limits and timeout protection
- Formula and macro removal
- Malicious content detection
- Secure file storage and cleanup

### Data Security
- CSRF protection on all forms
- Input validation and sanitization
- SQL injection prevention
- XSS protection in templates
- Secure session management

### AI Security
- Local LLM execution (Ollama)
- Prompt injection prevention
- Output validation and sanitization
- User data privacy protection

## Performance Considerations

### File Processing
- Streaming file processing for large files
- Background task processing for heavy operations
- Progress indicators via HTMX
- Chunked file upload support

### Caching Strategy
- Redis for analysis results
- Database for persistent storage
- Session-based cache invalidation
- Lazy loading for large datasets

### UI Performance
- HTMX partial updates only
- Lazy loading of analysis tools
- Efficient CSS Grid layout
- Minimal DOM manipulation

## Next Steps

1. **Phase 1**: Create data models and API contracts
2. **Phase 2**: Implement file upload and processing pipeline
3. **Phase 3**: Build three-panel UI with HTMX
4. **Phase 4**: Integrate LangChain tool registry
5. **Phase 5**: Implement AI chat and analysis features
6. **Phase 6**: Add session management and caching
7. **Phase 7**: Security hardening and testing
8. **Phase 8**: Implement Agentic AI system

### 28. Agentic AI System
**Task**: Research and implement autonomous AI agent for end-to-end data analysis

**Decision**: Implement comprehensive Agentic AI system with AgentRun and AgentStep models  
**Rationale**:
- Transform system from tool-based to autonomous AI platform
- Enable end-to-end analysis with minimal user intervention
- Provide intelligent planning and execution capabilities
- Support human feedback and guidance
- Respect resource constraints and provide transparency
- Enable complex multi-step analysis workflows

**Implementation**:
- AgentRun model for tracking autonomous analysis sessions
- AgentStep model for individual agent actions and decisions
- AgenticAIController for orchestrating agent workflows
- LLM-powered planning and strategy generation
- Tool execution with intelligent parameter selection
- Result analysis and adaptive strategy adjustment
- Human feedback integration for guidance
- Resource constraint management (max_steps, max_cost, max_time)
- Celery integration for asynchronous execution

**Key Features**:
- **Autonomous Planning**: LLM generates analysis strategies based on user goals
- **Intelligent Execution**: Agent selects tools and parameters automatically
- **Adaptive Behavior**: Agent adjusts strategy based on results
- **Human Feedback**: Users can guide agent behavior during execution
- **Resource Management**: Respects constraints and provides transparency
- **Error Handling**: Intelligent retry mechanisms and error recovery
- **Progress Tracking**: Real-time progress monitoring and status updates
- **Result Analysis**: Agent analyzes results and suggests next actions

**Agent Workflow**:
1. **Planning Phase**: LLM analyzes goal and dataset to create strategy
2. **Execution Phase**: Agent executes planned steps with tool selection
3. **Analysis Phase**: Agent analyzes results and adapts strategy
4. **Completion Phase**: Agent provides comprehensive analysis summary

**Resource Constraints**:
- **Max Steps**: Limit number of analysis steps (1-100)
- **Max Cost**: Limit token usage for cost control (1000-100000)
- **Max Time**: Limit execution time for responsiveness (60-3600 seconds)

**Human Interaction**:
- **Feedback Types**: Guidance, correction, approval, rejection
- **Step-specific Feedback**: Target specific analysis steps
- **Strategy Adaptation**: Agent adjusts behavior based on feedback
- **Transparency**: Full visibility into agent reasoning and decisions

**Monitoring and Control**:
- **Real-time Status**: Current step, progress, estimated completion
- **Pause/Resume**: Control agent execution flow
- **Cancel**: Stop agent execution at any time
- **Progress Tracking**: Detailed step-by-step execution log

**Integration Points**:
- **Existing Tools**: Leverages all analysis tools in the system
- **LLM System**: Uses LLM for planning and result analysis
- **Performance Optimization**: Integrates with memory optimization
- **Audit Trail**: All agent actions logged for compliance
- **Celery Tasks**: Asynchronous execution for scalability

**Alternatives considered**:
- **Rule-based Systems**: Inflexible, limited adaptability
- **Predefined Workflows**: Not suitable for diverse analysis goals
- **Manual Tool Selection**: Defeats purpose of autonomous analysis
- **External AI Services**: Dependency, latency, cost, data privacy
- **Simple Automation**: Lacks intelligence and adaptability
