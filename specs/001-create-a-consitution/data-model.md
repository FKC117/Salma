# Data Model: Data Analysis System

**Date**: 2024-12-19  
**Feature**: Data Analysis System  
**Database**: SQLite (development), PostgreSQL (production)

## Core Entities

### User
**Purpose**: System users who upload datasets and perform analysis (Django's built-in User model)  
**Fields**:
- `id`: Primary key (auto-increment)
- `username`: Unique username (max 150 chars)
- `email`: Email address (unique, validated)
- `password`: Hashed password (Django's built-in hashing)
- `first_name`: User's first name (max 150 chars)
- `last_name`: User's last name (max 150 chars)
- `is_active`: Account status (boolean)
- `is_staff`: Staff status (boolean)
- `is_superuser`: Superuser status (boolean)
- `date_joined`: Account creation timestamp
- `last_login`: Last login timestamp
- `token_limit`: Maximum tokens allowed per user (default: 10000)
- `tokens_used`: Total tokens consumed by user (default: 0)
- `tokens_used_this_month`: Tokens used in current month (default: 0)
- `last_token_reset`: Last token limit reset timestamp
- `storage_limit`: Maximum storage allowed per user in bytes (default: 262144000 = 250MB)
- `storage_used`: Current storage used by user in bytes (default: 0)
- `storage_warning_sent`: Whether storage warning has been sent (default: false)

**Relationships**:
- One-to-many with Dataset
- One-to-many with AnalysisSession
- One-to-many with AnalysisResult
- One-to-many with TokenUsage

**Validation Rules**:
- Username: 3-150 characters, alphanumeric + underscore only
- Email: Valid email format, unique constraint
- Password: Django's built-in password validators
- Token limit: Positive integer, minimum 1000
- Tokens used: Non-negative integer
- Django's built-in User model validation rules apply

### Dataset
**Purpose**: Uploaded data files converted to Parquet format with security sanitization  
**Fields**:
- `id`: Primary key (auto-increment)
- `user`: Foreign key to User
- `name`: Dataset name (max 200 chars)
- `original_filename`: Original uploaded filename
- `file_path`: Path to Parquet file on disk
- `file_size`: File size in bytes
- `row_count`: Number of rows in dataset
- `column_count`: Number of columns in dataset
- `uploaded_at`: Upload timestamp
- `last_accessed`: Last access timestamp
- `is_active`: Dataset status (boolean)
- `sanitization_status`: Security sanitization status (pending, completed, failed)
- `sensitive_data_detected`: Whether sensitive data was found and masked
- `encoding_issues`: UTF-8 encoding issues encountered during processing

**Relationships**:
- Many-to-one with User
- One-to-many with DatasetColumn
- One-to-many with AnalysisSession

**Validation Rules**:
- Name: 1-200 characters, required
- File path: Valid file path, exists on disk
- File size: Positive integer, reasonable limits
- Row/column count: Non-negative integers

### DatasetColumn
**Purpose**: Column metadata for each dataset with automatic type categorization  
**Fields**:
- `id`: Primary key (auto-increment)
- `dataset`: Foreign key to Dataset
- `name`: Column name (max 100 chars)
- `data_type`: Column data type (string, integer, float, boolean, datetime)
- `column_category`: Column category (numeric, categorical, datetime) - NON-NEGOTIABLE
- `is_numeric`: Whether column contains numeric data
- `is_categorical`: Whether column contains categorical data
- `is_datetime`: Whether column contains date/time data
- `null_count`: Number of null values
- `unique_count`: Number of unique values
- `sample_values`: JSON array of sample values (max 10)
- `encoding_info`: UTF-8 encoding details and issues detected

**Relationships**:
- Many-to-one with Dataset

**Validation Rules**:
- Name: 1-100 characters, required
- Data type: Must be one of predefined types
- Column category: Must be one of (numeric, categorical, datetime) - NON-NEGOTIABLE
- Counts: Non-negative integers
- Sample values: Valid JSON array, max 10 items
- Encoding info: Valid JSON object with UTF-8 details

### AnalysisTool
**Purpose**: Registered analysis tools in LangChain registry  
**Fields**:
- `id`: Primary key (auto-increment)
- `name`: Tool name (max 100 chars, unique)
- `description`: Tool description (max 500 chars)
- `category`: Tool category (statistical, visualization, machine_learning, etc.)
- `parameters_schema`: JSON schema for tool parameters
- `is_active`: Tool availability status
- `created_at`: Tool registration timestamp
- `updated_at`: Last modification timestamp

**Relationships**:
- One-to-many with AnalysisResult

**Validation Rules**:
- Name: 1-100 characters, unique, required
- Description: 1-500 characters, required
- Category: Must be one of predefined categories
- Parameters schema: Valid JSON schema

### AnalysisSession
**Purpose**: User session for specific dataset analysis with history management  
**Fields**:
- `id`: Primary key (auto-increment)
- `user`: Foreign key to User
- `dataset`: Foreign key to Dataset (NON-NEGOTIABLE tagging)
- `session_key`: Unique session identifier
- `created_at`: Session creation timestamp
- `last_activity`: Last activity timestamp
- `is_active`: Session status
- `settings`: JSON field for session-specific settings
- `workspace_state`: JSON field for current workspace layout and state
- `analysis_history`: JSON field for analysis history tracking

**Relationships**:
- Many-to-one with User
- Many-to-one with Dataset (dataset-tagged sessions)
- One-to-many with AnalysisResult
- One-to-many with AnalysisHistory

**Validation Rules**:
- Session key: Unique, 32 characters
- Settings: Valid JSON object
- Workspace state: Valid JSON object with UI state
- Analysis history: Valid JSON array of analysis references

### AnalysisResult
**Purpose**: Cached analysis results for performance  
**Fields**:
- `id`: Primary key (auto-increment)
- `session`: Foreign key to AnalysisSession
- `tool`: Foreign key to AnalysisTool
- `parameters_hash`: Hash of tool parameters for cache key
- `result_data`: JSON field containing analysis results
- `execution_time`: Tool execution time in milliseconds
- `created_at`: Result creation timestamp
- `expires_at`: Cache expiration timestamp
- `is_cached`: Whether result is from cache

**Relationships**:
- Many-to-one with AnalysisSession
- Many-to-one with AnalysisTool

**Validation Rules**:
- Parameters hash: 64 characters (SHA-256)
- Execution time: Non-negative integer
- Result data: Valid JSON object
- Expires at: Future timestamp

### ChatMessage
**Purpose**: AI chat messages for analysis interpretation  
**Fields**:
- `id`: Primary key (auto-increment)
- `session`: Foreign key to AnalysisSession
- `role`: Message role (user, assistant, system)
- `content`: Message content (max 5000 chars)
- `analysis_result`: Foreign key to AnalysisResult (optional)
- `created_at`: Message timestamp
- `tokens_used`: Number of tokens used (for cost tracking)

**Relationships**:
- Many-to-one with AnalysisSession
- Many-to-one with AnalysisResult (optional)

**Validation Rules**:
- Role: Must be one of predefined roles
- Content: 1-5000 characters, required
- Tokens used: Non-negative integer

### FileProcessingError
**Purpose**: Track and display file processing errors with user-friendly messages  
**Fields**:
- `id`: Primary key (auto-increment)
- `dataset`: Foreign key to Dataset
- `error_type`: Type of error (security, encoding, format, validation)
- `error_code`: Machine-readable error code
- `user_message`: User-friendly error message (max 500 chars)
- `technical_details`: Technical error details (max 2000 chars)
- `severity`: Error severity (low, medium, high, critical)
- `resolved`: Whether error was resolved
- `created_at`: Error timestamp
- `resolved_at`: Resolution timestamp

**Relationships**:
- Many-to-one with Dataset

**Validation Rules**:
- Error type: Must be one of predefined types
- User message: 1-500 characters, required
- Technical details: 1-2000 characters, required
- Severity: Must be one of predefined levels

### AnalysisHistory
**Purpose**: Track analysis history for dataset-tagged sessions with card-based UI  
**Fields**:
- `id`: Primary key (auto-increment)
- `session`: Foreign key to AnalysisSession
- `analysis_result`: Foreign key to AnalysisResult
- `tool`: Foreign key to AnalysisTool
- `execution_order`: Order of execution in session
- `card_position`: Position in workspace (x, y coordinates)
- `card_size`: Size of card in workspace (width, height)
- `card_visible`: Whether card is currently visible
- `created_at`: Analysis execution timestamp
- `last_accessed`: Last time analysis was viewed

**Relationships**:
- Many-to-one with AnalysisSession
- Many-to-one with AnalysisResult
- Many-to-one with AnalysisTool

**Validation Rules**:
- Execution order: Non-negative integer, unique per session
- Card position: Valid JSON object with x, y coordinates
- Card size: Valid JSON object with width, height
- Card visible: Boolean value

### TokenUsage
**Purpose**: Track token consumption for Google AI operations per user  
**Fields**:
- `id`: Primary key (auto-increment)
- `user`: Foreign key to User
- `session`: Foreign key to AnalysisSession (optional)
- `operation_type`: Type of AI operation (chat, analysis, interpretation)
- `input_tokens`: Number of input tokens used
- `output_tokens`: Number of output tokens generated
- `total_tokens`: Total tokens consumed (input + output)
- `model_used`: Google AI model used (e.g., gemini-pro)
- `cost_estimate`: Estimated cost in USD
- `created_at`: Token usage timestamp
- `analysis_result`: Foreign key to AnalysisResult (optional)

**Relationships**:
- Many-to-one with User
- Many-to-one with AnalysisSession (optional)
- Many-to-one with AnalysisResult (optional)

**Validation Rules**:
- Input tokens: Non-negative integer
- Output tokens: Non-negative integer
- Total tokens: Must equal input_tokens + output_tokens
- Operation type: Must be one of predefined types
- Model used: Must be valid Google AI model name
- Cost estimate: Non-negative decimal

### SystemHealth
**Purpose**: Monitor system health and performance metrics  
**Fields**:
- `id`: Primary key (auto-increment)
- `metric_name`: Name of the metric (e.g., 'response_time', 'memory_usage')
- `metric_value`: Value of the metric (float)
- `metric_unit`: Unit of measurement (e.g., 'ms', 'MB', 'GB')
- `threshold_warning`: Warning threshold value (float)
- `threshold_critical`: Critical threshold value (float)
- `status`: Current status (normal, warning, critical)
- `created_at`: Metric timestamp
- `server_instance`: Server instance identifier (string)

**Relationships**:
- None (system-level metrics)

**Validation Rules**:
- Metric name: 1-100 characters, required
- Metric value: Real number, required
- Status: Must be one of predefined levels
- Threshold values: Non-negative real numbers

### ErrorLog
**Purpose**: Track system errors and exceptions  
**Fields**:
- `id`: Primary key (auto-increment)
- `user`: Foreign key to User (optional)
- `session`: Foreign key to AnalysisSession (optional)
- `error_type`: Type of error (e.g., 'FileProcessingError', 'APIError')
- `error_message`: Error message (text)
- `error_code`: Error code (string)
- `stack_trace`: Full stack trace (text)
- `request_path`: API endpoint that caused error (string)
- `request_method`: HTTP method (string)
- `correlation_id`: Unique identifier for request tracking (string)
- `resolved`: Whether error has been resolved (boolean)
- `resolved_at`: Resolution timestamp
- `created_at`: Error timestamp

**Relationships**:
- Many-to-one with User (optional)
- Many-to-one with AnalysisSession (optional)

**Validation Rules**:
- Error type: Must be one of predefined types
- Error message: 1-1000 characters, required
- Correlation ID: 1-50 characters, required
- Request path: Valid URL path format

### BackupRecord
**Purpose**: Track backup operations and status  
**Fields**:
- `id`: Primary key (auto-increment)
- `backup_type`: Type of backup (full, incremental, user_data)
- `backup_size`: Size of backup in bytes (integer)
- `backup_path`: Path to backup file (string)
- `status`: Backup status (in_progress, completed, failed)
- `started_at`: Backup start timestamp
- `completed_at`: Backup completion timestamp
- `verified`: Whether backup integrity has been verified (boolean)
- `retention_until`: When backup should be deleted (timestamp)
- `error_message`: Error message if backup failed (text)

**Relationships**:
- None (system-level operations)

**Validation Rules**:
- Backup type: Must be one of predefined types
- Backup size: Non-negative integer
- Status: Must be one of predefined statuses
- Backup path: Valid file path format

### APIRateLimit
**Purpose**: Track API rate limiting per user  
**Fields**:
- `id`: Primary key (auto-increment)
- `user`: Foreign key to User
- `endpoint`: API endpoint being rate limited (string)
- `request_count`: Number of requests in current window (integer)
- `window_start`: Start of current rate limit window (timestamp)
- `window_duration`: Duration of rate limit window in seconds (integer)
- `max_requests`: Maximum requests allowed in window (integer)
- `blocked_until`: When user is unblocked (timestamp)
- `last_request_at`: Timestamp of last request (timestamp)

**Relationships**:
- Many-to-one with User

**Validation Rules**:
- Endpoint: Valid API endpoint format
- Request count: Non-negative integer
- Window duration: Positive integer
- Max requests: Positive integer

### AuditTrail
**Purpose**: Track all user actions and system events for audit and compliance  
**Fields**:
- `id`: Primary key (auto-increment)
- `user`: Foreign key to User (optional for system events)
- `session`: Foreign key to AnalysisSession (optional)
- `action_type`: Type of action performed (e.g., 'login', 'file_upload', 'analysis_execute', 'data_delete')
- `action_category`: Category of action (authentication, data_management, analysis, system, security)
- `action_description`: Human-readable description of the action
- `resource_type`: Type of resource affected (dataset, analysis_result, user, system)
- `resource_id`: ID of the affected resource (optional)
- `resource_name`: Name of the affected resource (optional)
- `ip_address`: IP address of the user (string)
- `user_agent`: User agent string from request
- `request_path`: API endpoint or page accessed
- `request_method`: HTTP method used
- `request_data`: JSON data of the request (sensitive data masked)
- `response_status`: HTTP response status code
- `response_data`: JSON data of the response (sensitive data masked)
- `duration_ms`: Duration of the action in milliseconds
- `success`: Whether the action was successful (boolean)
- `error_message`: Error message if action failed (optional)
- `correlation_id`: Correlation ID for request tracking
- `metadata`: Additional metadata as JSON (optional)
- `created_at`: Action timestamp
- `retention_until`: When audit record should be deleted (timestamp)

**Relationships**:
- Many-to-one with User (optional)
- Many-to-one with AnalysisSession (optional)

**Validation Rules**:
- Action type: Must be one of predefined types
- Action category: Must be one of predefined categories
- Action description: 1-500 characters, required
- Resource type: Must be one of predefined types
- IP address: Valid IP address format
- Request path: Valid URL path format
- Duration: Non-negative integer
- Success: Boolean value
- Correlation ID: 1-50 characters, required

### LLMContextCache
**Purpose**: Store and manage LLM context for intelligent AI responses  
**Fields**:
- `id`: Primary key (auto-increment)
- `session`: Foreign key to AnalysisSession
- `context_type`: Type of context (chat_history, analysis_context, tool_context)
- `context_data`: JSON data containing the context information
- `message_count`: Number of messages in context (max 10)
- `last_updated`: Timestamp of last context update
- `is_active`: Whether this context is currently active
- `context_hash`: Hash of context data for quick comparison
- `created_at`: Context creation timestamp

**Relationships**:
- Many-to-one with AnalysisSession

**Validation Rules**:
- Context type: Must be one of predefined types
- Message count: Must be between 1 and 10
- Context data: Valid JSON object
- Context hash: 32-character hash string
- Is active: Boolean value

### GeneratedImage
**Purpose**: Store and manage images generated by analysis tools  
**Fields**:
- `id`: Primary key (auto-increment)
- `session`: Foreign key to AnalysisSession
- `analysis_result`: Foreign key to AnalysisResult (optional)
- `tool`: Foreign key to AnalysisTool
- `image_type`: Type of image (histogram, scatter_plot, correlation_matrix, survival_curve)
- `file_path`: Path to image file in media directory
- `file_name`: Original filename of the image
- `file_size`: Size of image file in bytes
- `image_format`: Image format (PNG, JPEG, SVG)
- `width`: Image width in pixels
- `height`: Image height in pixels
- `dpi`: Dots per inch (for print quality)
- `base64_data`: Base64 encoded image data for LLM processing
- `access_url`: Web-accessible URL for the image
- `created_at`: Image generation timestamp
- `expires_at`: Image expiration timestamp (optional)

**Relationships**:
- Many-to-one with AnalysisSession
- Many-to-one with AnalysisResult (optional)
- Many-to-one with AnalysisTool

**Validation Rules**:
- Image type: Must be one of predefined types
- File path: Valid file path format
- File size: Positive integer
- Image format: Must be PNG, JPEG, or SVG
- Width/Height: Positive integers
- DPI: Positive number
- Access URL: Valid URL format

### SandboxExecution
**Purpose**: Track and manage secure code execution in LangChain sandbox  
**Fields**:
- `id`: Primary key (auto-increment)
- `session`: Foreign key to AnalysisSession
- `user`: Foreign key to User
- `execution_id`: Unique execution identifier (UUID)
- `user_query`: Original user query that triggered code generation
- `generated_code`: Python code generated by LLM
- `execution_status`: Status (pending, running, completed, failed, timeout)
- `execution_result`: JSON result data from code execution
- `error_message`: Error message if execution failed
- `execution_time_ms`: Execution time in milliseconds
- `memory_used_mb`: Memory usage in MB
- `cpu_time_ms`: CPU time in milliseconds
- `output_data`: Formatted output data for user display
- `images_generated`: Array of image IDs generated during execution
- `tables_generated`: Array of table data generated during execution
- `variables_created`: JSON object of variables created during execution
- `libraries_used`: Array of libraries used in execution
- `security_violations`: Array of security violations detected
- `retry_count`: Number of retry attempts
- `max_retries`: Maximum retry attempts allowed
- `created_at`: Execution start timestamp
- `completed_at`: Execution completion timestamp
- `expires_at`: Execution data expiration timestamp

**Relationships**:
- Many-to-one with AnalysisSession
- Many-to-one with User
- One-to-many with GeneratedImage (via images_generated)

**Validation Rules**:
- Execution ID: Valid UUID format
- Execution status: Must be one of predefined statuses
- Execution time: Non-negative integer
- Memory usage: Non-negative number
- CPU time: Non-negative integer
- Retry count: Non-negative integer, max 3
- Security violations: Array of strings

### AuditTrail
**Purpose**: Comprehensive audit trail for user actions and system events (NON-NEGOTIABLE)  
**Fields**:
- `id`: Primary key (auto-increment)
- `user`: Foreign key to User (nullable for system events)
- `session`: Foreign key to AnalysisSession (optional)
- `action_type`: Type of action (login, logout, upload, analysis, delete, export, admin_action, system_event)
- `action_category`: Category (authentication, data_management, analysis, system, security, compliance)
- `resource_type`: Type of resource affected (user, dataset, analysis_result, report, image, session, system)
- `resource_id`: ID of the affected resource
- `resource_name`: Human-readable name of the resource
- `action_description`: Detailed description of the action performed
- `before_snapshot`: JSON snapshot of resource state before action (masked for sensitive data)
- `after_snapshot`: JSON snapshot of resource state after action (masked for sensitive data)
- `ip_address`: IP address of the user (IPv4/IPv6)
- `user_agent`: User agent string from HTTP request
- `correlation_id`: Unique correlation ID for tracking related events
- `request_id`: Unique request identifier
- `session_id`: HTTP session identifier
- `success`: Whether the action was successful
- `error_message`: Error message if action failed
- `execution_time_ms`: Time taken to perform the action
- `data_changed`: Whether any data was modified
- `sensitive_data_accessed`: Whether sensitive data was accessed
- `compliance_flags`: Array of compliance flags (gdpr, hipaa, sox, pci_dss)
- `retention_status`: Retention status (active, archived, purged)
- `retention_expires_at`: When the audit record expires
- `created_at`: Action timestamp
- `created_by`: Who created the record (user_id or 'system')

**Relationships**:
- Many-to-one with User (nullable)
- Many-to-one with AnalysisSession (optional)
- One-to-many with AuditTrailDetail (for additional context)

**Validation Rules**:
- Action type: Must be one of predefined types
- Action category: Must be one of predefined categories
- Resource type: Must be one of predefined types
- Resource ID: Non-negative integer
- Action description: 1-500 characters, required
- IP address: Valid IPv4 or IPv6 format
- User agent: 1-500 characters
- Correlation ID: 1-50 characters, required
- Request ID: Valid UUID format
- Success: Boolean value
- Execution time: Non-negative integer
- Data changed: Boolean value
- Sensitive data accessed: Boolean value
- Compliance flags: Array of valid compliance standards
- Retention status: Must be one of predefined statuses

### AuditTrailDetail
**Purpose**: Additional context and metadata for audit trail entries  
**Fields**:
- `id`: Primary key (auto-increment)
- `audit_trail`: Foreign key to AuditTrail
- `detail_type`: Type of detail (parameter, header, cookie, file_info, database_change, api_call)
- `detail_key`: Key name for the detail
- `detail_value`: Value of the detail (masked if sensitive)
- `is_sensitive`: Whether this detail contains sensitive information
- `masked_value`: Masked version of the value (if sensitive)
- `created_at`: Detail creation timestamp

**Relationships**:
- Many-to-one with AuditTrail

**Validation Rules**:
- Detail type: Must be one of predefined types
- Detail key: 1-100 characters, required
- Detail value: 1-2000 characters
- Is sensitive: Boolean value
- Masked value: 1-2000 characters (if sensitive)

### AgentRun
**Purpose**: Track autonomous AI agent analysis sessions (NON-NEGOTIABLE)  
**Fields**:
- `id`: Primary key (auto-increment)
- `user`: Foreign key to User
- `dataset`: Foreign key to Dataset
- `session`: Foreign key to AnalysisSession (optional)
- `goal`: User-defined analysis goal or question
- `plan_json`: JSON object containing the agent's analysis plan
- `status`: Current status (planning, running, paused, completed, failed, cancelled)
- `current_step`: Current step number in the plan
- `total_steps`: Total number of steps planned
- `max_steps`: Maximum steps allowed (resource constraint)
- `max_cost`: Maximum cost allowed in tokens (resource constraint)
- `max_time`: Maximum time allowed in seconds (resource constraint)
- `total_cost`: Total cost incurred so far in tokens
- `total_time`: Total time elapsed in seconds
- `progress_percentage`: Progress percentage (0-100)
- `agent_version`: Version of the agent system used
- `llm_model`: LLM model used for planning and execution
- `started_at`: When the agent run started
- `finished_at`: When the agent run completed (nullable)
- `error_message`: Error message if run failed (nullable)
- `correlation_id`: Unique correlation ID for tracking
- `parent_run`: Foreign key to AgentRun (for sub-runs)
- `created_at`: Agent run creation timestamp

**Relationships**:
- Many-to-one with User
- Many-to-one with Dataset
- Many-to-one with AnalysisSession (optional)
- One-to-many with AgentStep
- One-to-many with AgentRun (sub-runs)
- Many-to-one with AgentRun (parent run)

**Validation Rules**:
- Goal: 1-1000 characters, required
- Status: Must be one of predefined statuses
- Current step: Non-negative integer
- Total steps: Non-negative integer
- Max steps: Positive integer, minimum 1, maximum 100
- Max cost: Positive integer, minimum 1000, maximum 100000
- Max time: Positive integer, minimum 60, maximum 3600
- Progress percentage: Integer between 0 and 100
- Agent version: 1-50 characters
- LLM model: 1-100 characters
- Correlation ID: 1-50 characters, required

### AgentStep
**Purpose**: Track individual agent actions and decisions (NON-NEGOTIABLE)  
**Fields**:
- `id`: Primary key (auto-increment)
- `agent_run`: Foreign key to AgentRun
- `step_number`: Step number in the agent run
- `thought`: Agent's reasoning and thought process
- `tool_name`: Name of the tool/action to execute
- `parameters_json`: JSON object containing tool parameters
- `observation_json`: JSON object containing tool results/observations
- `status`: Step status (planned, running, completed, failed, skipped)
- `token_usage`: Tokens used for this step
- `execution_time_ms`: Time taken to execute this step
- `memory_used_mb`: Memory used during this step
- `confidence_score`: Agent's confidence in this step (0-1)
- `reasoning`: Detailed reasoning for this step
- `next_action`: Suggested next action based on results
- `started_at`: When the step started
- `finished_at`: When the step completed (nullable)
- `error_message`: Error message if step failed (nullable)
- `retry_count`: Number of retry attempts
- `max_retries`: Maximum retry attempts allowed
- `created_at`: Step creation timestamp

**Relationships**:
- Many-to-one with AgentRun
- One-to-many with AnalysisResult (if step creates analysis results)

**Validation Rules**:
- Step number: Positive integer
- Thought: 1-2000 characters, required
- Tool name: 1-100 characters, required
- Parameters JSON: Valid JSON object
- Observation JSON: Valid JSON object
- Status: Must be one of predefined statuses
- Token usage: Non-negative integer
- Execution time: Non-negative integer
- Memory used: Non-negative number
- Confidence score: Number between 0 and 1
- Reasoning: 1-1000 characters
- Next action: 1-500 characters
- Retry count: Non-negative integer, maximum 3
- Max retries: Positive integer, maximum 3

### ReportGeneration
**Purpose**: Manage professional report generation and document export  
**Fields**:
- `id`: Primary key (auto-increment)
- `session`: Foreign key to AnalysisSession
- `user`: Foreign key to User
- `report_id`: Unique report identifier (UUID)
- `report_title`: User-defined report title
- `report_type`: Type of report (analysis_summary, detailed_report, executive_summary)
- `report_status`: Status (pending, generating, completed, failed, expired)
- `content_selection`: JSON object defining what content to include
- `template_id`: ID of the report template used
- `file_path`: Path to generated Word document
- `file_name`: Original filename of the report
- `file_size`: Size of report file in bytes
- `generation_progress`: Progress percentage (0-100)
- `sections_included`: Array of section IDs included in report
- `images_included`: Array of image IDs included in report
- `tables_included`: Array of table IDs included in report
- `chat_messages_included`: Array of chat message IDs included
- `analysis_results_included`: Array of analysis result IDs included
- `sandbox_executions_included`: Array of sandbox execution IDs included
- `custom_sections`: JSON object of custom sections added by user
- `generation_settings`: JSON object of generation parameters
- `error_message`: Error message if generation failed
- `generation_time_ms`: Time taken to generate report in milliseconds
- `download_count`: Number of times report has been downloaded
- `last_downloaded_at`: Timestamp of last download
- `expires_at`: Report expiration timestamp
- `created_at`: Report generation start timestamp
- `completed_at`: Report generation completion timestamp

**Relationships**:
- Many-to-one with AnalysisSession
- Many-to-one with User
- One-to-many with GeneratedImage (via images_included)
- One-to-many with AnalysisResult (via analysis_results_included)
- One-to-many with SandboxExecution (via sandbox_executions_included)

**Validation Rules**:
- Report ID: Valid UUID format
- Report status: Must be one of predefined statuses
- Generation progress: Integer between 0 and 100
- File size: Non-negative integer
- Download count: Non-negative integer
- Generation time: Non-negative integer

## State Transitions

### Dataset Lifecycle
1. **Uploaded**: File uploaded, validation in progress
2. **Processing**: Converting to Parquet, analyzing columns
3. **Ready**: Available for analysis
4. **Archived**: User archived, not available for new analysis
5. **Deleted**: Permanently removed from system

### AnalysisSession Lifecycle
1. **Created**: New session created for dataset (dataset-tagged)
2. **Active**: User performing analysis
3. **Dataset Switch**: Session changes when user switches datasets
4. **History Restore**: Previous analysis results loaded from history
5. **Idle**: No activity for configured period
6. **Expired**: Session timeout reached
7. **Closed**: User explicitly closed session

### AnalysisHistory Lifecycle
1. **Created**: Analysis result added to history
2. **Card Created**: Analysis wrapped in card and positioned in workspace
3. **Visible**: Card displayed in workspace
4. **Hidden**: Card hidden but preserved in history
5. **Restored**: Card restored when switching back to dataset
6. **Archived**: Old analysis moved to archive

### AnalysisResult Lifecycle
1. **Computing**: Tool execution in progress
2. **Cached**: Result stored in cache
3. **Expired**: Cache expiration reached
4. **Invalidated**: Dataset or tool changed

## Database Indexes

### Performance Indexes
- `User.email` (unique index)
- `User.username` (unique index)
- `Dataset.user_id` (foreign key index)
- `DatasetColumn.dataset_id` (foreign key index)
- `AnalysisSession.user_id` (foreign key index)
- `AnalysisSession.dataset_id` (foreign key index)
- `AnalysisResult.session_id` (foreign key index)
- `AnalysisResult.tool_id` (foreign key index)
- `AnalysisResult.parameters_hash` (index for cache lookups)
- `ChatMessage.session_id` (foreign key index)

### Composite Indexes
- `AnalysisResult(session_id, tool_id, parameters_hash)` (unique constraint for cache)
- `AnalysisSession(user_id, dataset_id, is_active)` (active session lookup)

## Data Validation Rules

### File Upload Validation
- File size: Maximum 100MB per file
- File types: XLS, XLSX, CSV, JSON only
- Row limit: Maximum 1,000,000 rows per dataset
- Column limit: Maximum 1,000 columns per dataset
- Processing timeout: Maximum 5 minutes per file
- Security scanning: All files MUST be scanned for malicious content
- Formula removal: All formulas and macros MUST be stripped
- Sensitive data detection: PII and sensitive data MUST be masked
- UTF-8 encoding: All encoding issues MUST be handled gracefully

### Analysis Tool Validation
- Parameter validation: Based on tool's JSON schema
- Execution timeout: Maximum 30 seconds per tool
- Memory limit: Maximum 2GB per analysis
- Result size: Maximum 10MB per result
- Column type validation: Tools MUST validate parameters against column categories
- Type mismatch handling: Graceful error messages for type mismatches

### Column Type Management (NON-NEGOTIABLE)
- Automatic categorization: All columns MUST be categorized as numeric, categorical, or datetime
- Global storage: Column type information MUST be stored globally for each dataset
- Tool integration: All analysis tools MUST receive column type information
- Type validation: Tool parameters MUST be validated against column types
- Error handling: Type mismatches MUST display clear, actionable error messages

### Analysis History Management (NON-NEGOTIABLE)
- Dataset tagging: All analysis sessions MUST be tagged to specific datasets
- Session switching: When users switch datasets, sessions MUST automatically change
- History preservation: Analysis history MUST be preserved and accessible
- Workspace restoration: Previous analysis results MUST be restored to workspace
- Card-based UI: All analysis results MUST be wrapped in cards
- Position tracking: Card positions and sizes MUST be preserved
- Continuity: Analysis continuity MUST be maintained across dataset switches

### REST API Architecture (NON-NEGOTIABLE)
- API endpoints: All system entry points MUST use REST API
- Django REST Framework: DRF MUST be used for all API endpoints
- HTMX targeting: All HTMX interactions MUST target REST API endpoints
- No direct DB access: Frontend MUST NOT access database directly
- Business logic: All business logic MUST be in API views
- Response consistency: API responses MUST be consistent and documented
- RESTful conventions: All endpoints MUST follow REST standards

### Django Authentication (NON-NEGOTIABLE)
- Built-in system: Django's default authentication MUST be used exclusively
- Sign-in/Sign-up: Built-in authentication views MUST be implemented
- No custom auth: No custom authentication solutions allowed
- Session management: Django's session framework MUST be used
- CSRF protection: CSRF protection MUST be enabled for all authenticated endpoints
- Auth validation: Authentication state MUST be validated in all API calls

### HTMX Error Prevention (NON-NEGOTIABLE)
- Target validation: All HTMX targets MUST be validated before implementation
- Request/response testing: HTMX cycles MUST be tested thoroughly
- No target errors: No HTMX target errors allowed in production
- Error handling: All HTMX interactions MUST have proper error handling
- Partial updates: HTMX partial updates MUST be tested for all scenarios
- Loading states: HTMX loading states MUST be implemented for all requests
- Attribute validation: All HTMX attributes MUST be validated and tested

### Virtual Environment Activation (NON-NEGOTIABLE)
- Always activated: Virtual environment MUST be activated for ALL terminal tasks
- No exceptions: No Python commands allowed without active virtual environment
- Verification required: Virtual environment status MUST be verified before any work
- Team compliance: All team members MUST ensure virtual environment is active
- Documentation: Virtual environment activation MUST be documented in all workflows
- Critical requirement: This is CRITICAL for dependency isolation and project consistency

### Google AI Integration and Token Management (NON-NEGOTIABLE)
- Google API key: Google AI API MUST be used for all LLM operations
- No rate limits: No token or rate limits on Google AI API usage
- Token calculation: Token calculation MUST be performed for every AI input and output
- Token storage: Token usage MUST be stored in user database records
- User limits: Maximum token limit per user MUST be enforced
- Real-time tracking: Token tracking MUST be accurate and real-time
- User monitoring: User token consumption MUST be monitored and displayed
- Limit enforcement: Token limits MUST prevent excessive usage
- Default limits: Default token limits MUST be configured for new users
- Cost control: This is CRITICAL for cost control and fair usage

### Error Handling & Recovery (NON-NEGOTIABLE)
- Graceful degradation: All system errors MUST have graceful degradation
- Retryable operations: Failed operations MUST be retryable
- Data protection: User data MUST never be lost due to errors
- Automatic recovery: Error recovery MUST be automatic where possible
- Rollback capabilities: Critical operations MUST have rollback capabilities
- User-friendly errors: Error notifications MUST be user-friendly and actionable
- System consistency: System MUST maintain consistency during error states
- Error logging: All errors MUST be logged with correlation IDs
- Recovery procedures: Error recovery procedures MUST be documented and tested

### Data Backup & Recovery (NON-NEGOTIABLE)
- Daily backups: Automated daily backups MUST be performed for all user data
- Pre-operation backup: Analysis results MUST be backed up before major operations
- Migration rollback: Database migration rollback procedures MUST be implemented
- Data export: User data export capabilities MUST be provided
- Backup verification: Backup integrity MUST be verified regularly
- Recovery testing: Recovery procedures MUST be tested and documented
- Data loss prevention: Data loss prevention MUST be prioritized
- Retention policies: Backup retention policies MUST be enforced

### Performance Monitoring & Alerting (NON-NEGOTIABLE)
- Real-time metrics: Real-time performance metrics MUST be collected and displayed
- Token alerts: Token usage alerts MUST be sent when approaching limits
- Resource monitoring: System resource monitoring MUST be continuous
- Critical alerts: Automated alerting MUST be configured for critical issues
- Performance baselines: Performance baselines MUST be established
- Response time monitoring: Response time monitoring MUST be implemented
- Usage tracking: Resource usage tracking MUST be comprehensive
- Alert escalation: Alert escalation procedures MUST be defined

### API Protection & Rate Limiting (NON-NEGOTIABLE)
- Per-user limits: Per-user API rate limiting MUST be implemented
- Request throttling: Request throttling MUST be applied for heavy operations
- DDoS protection: DDoS protection measures MUST be in place
- Usage analytics: API usage analytics MUST be collected
- Violation logging: Rate limit violations MUST be logged and monitored
- Abuse prevention: API abuse prevention MUST be enforced
- Request validation: Request validation MUST be comprehensive
- Security headers: API security headers MUST be implemented

### Data Retention & User Storage Management (NON-NEGOTIABLE)
- Storage limit: User storage limit MUST be set to 250MB per user
- Usage warnings: Storage usage warnings MUST be sent when approaching limits
- User deletion: Users MUST be able to delete their own files and analysis results
- Permanent deletion: Deletion MUST be permanent and immediate
- Usage display: Storage usage MUST be displayed to users
- Auto-archiving: Old analysis results MUST be automatically archived when limit reached
- Data export: User data export MUST be available before deletion
- Cleanup automation: Storage cleanup procedures MUST be automated

### Audit Trail & Compliance (NON-NEGOTIABLE)
- User action logging: All user actions MUST be logged in audit trail
- System event logging: All system events MUST be logged
- Data masking: Sensitive data MUST be masked in audit logs
- Retention policy: Audit logs MUST be retained for compliance period
- Immutable logs: Audit logs MUST be immutable once created
- Correlation tracking: All actions MUST have correlation IDs
- IP tracking: User IP addresses MUST be logged
- Request/response logging: API requests and responses MUST be logged
- Error logging: All errors MUST be logged with context
- Compliance reporting: Audit reports MUST be available for compliance

### Requirements Management & Dependency Installation (NON-NEGOTIABLE)
- Requirements file: Comprehensive requirements.txt MUST be generated and maintained
- Version pinning: All dependencies MUST be pinned to specific versions
- Installation order: Requirements.txt MUST be installed before any development work
- Virtual environment: Virtual environment MUST be activated before installing requirements
- Version compatibility: All package versions MUST be compatible and tested
- Dependency separation: Development dependencies MUST be separated from production dependencies
- Update tracking: Requirements.txt MUST be updated whenever new packages are added
- Reproducible builds: This is CRITICAL for reproducible builds and dependency management

### Data Analysis Library Requirements (NON-NEGOTIABLE)
- Pandas-ai prohibition: Pandas-ai MUST NOT be used in production
- Standard pandas only: Only standard pandas library MUST be used for data analysis
- Lifelines requirement: Lifelines library MUST be used for survival analysis
- Matplotlib requirement: Matplotlib MUST be used for plotting with Agg backend
- Seaborn requirement: Seaborn MUST be used for statistical data visualization
- Agg backend: Matplotlib Agg method MUST be used for all plotting operations
- No interactive plotting: No interactive plotting libraries allowed in production
- Server-side generation: All visualizations MUST be generated server-side
- Production stability: This is CRITICAL for production stability and performance

### Code Organization & Architecture (NON-NEGOTIABLE)
- Tools organization: Tools MUST be organized in dedicated 'tools' subfolder with individual files
- View separation: Views.py MUST be separated into task-specific modules
- Individual tool files: Each tool MUST have its own file in the tools subfolder
- View module imports: View modules MUST be imported and called from main views.py
- LLM context caching: LLM context caching MUST be implemented
- Last 10 messages: Last 10 messages from current analysis session MUST be used as LLM context
- Message storage: All chat messages MUST be stored for context retrieval
- Session-specific context: Context MUST be session-specific and automatically updated
- Maintainable code: This is CRITICAL for maintainable code and intelligent AI responses

### LLM Batch Processing & Response Formatting (NON-NEGOTIABLE)
- Batch API calling: LLM batch API calling MUST be enabled for efficient processing
- Analysis result formatting: Analysis results MUST be passed to LLM in proper format
- Response formatting: LLM responses MUST be formatted correctly (tables as tables, images as PNG)
- Image storage: Generated images MUST be stored in accessible media directory
- Image encoding: Images MUST be passed to LLM via base64 encoding or file references
- Image organization: Image storage MUST be organized by session and analysis ID
- Image accessibility: Image URLs MUST be accessible via web endpoints
- Content formatting: LLM responses MUST include proper formatting for different content types
- Intelligent interpretation: This is CRITICAL for intelligent analysis interpretation and proper content delivery

### LangChain Sandbox & Code Execution (NON-NEGOTIABLE)
- Sandbox implementation: LangChain sandbox MUST be implemented for secure code execution
- User query processing: User queries MUST be processed by LLM to generate Python code
- Secure execution: Generated code MUST be executed in isolated, secured sandbox environment
- Resource restrictions: Sandbox MUST have restricted access to system resources
- Time limits: Code execution MUST be time-limited and memory-constrained
- Library restrictions: Only approved libraries MUST be available in sandbox
- User interface: Sandbox MUST return results to users via chat interface
- Error handling: Error handling MUST provide LLM feedback for code correction
- User visibility: Sandbox MUST be completely hidden from users
- Dynamic analysis: This is CRITICAL for dynamic analysis capabilities and user safety

### Report Generation & Document Export (NON-NEGOTIABLE)
- Report generation: Professional report generation MUST be implemented for analysis sessions
- Word format: Reports MUST be generated in Microsoft Word format with beautiful design
- Content selection: Users MUST have control over report content selection
- Analysis results: All analysis results MUST be included (tools results, charts, tables, interpretations)
- LLM responses: LLM responses and suggestions MUST be included in reports
- Report templates: Report templates MUST be customizable and professional
- Download functionality: Download functionality MUST be available for generated reports
- Asynchronous generation: Report generation MUST be asynchronous for large sessions
- Professional documentation: This is CRITICAL for professional analysis documentation and client deliverables

### Session Management
- Session timeout: 24 hours of inactivity
- Maximum active sessions: 10 per user
- Cache expiration: 7 days for analysis results
- Chat history: Maximum 1000 messages per session

## Security Considerations

### Data Protection
- All file uploads scanned for malicious content
- Formulas and macros removed during processing
- Sensitive data not logged in application logs
- Database connections encrypted in production

### Access Control
- Users can only access their own datasets
- Session-based access control
- CSRF protection on all forms
- Input validation on all user inputs

### Audit Trail
- All dataset uploads logged
- All analysis executions logged
- All chat interactions logged
- User authentication events logged
