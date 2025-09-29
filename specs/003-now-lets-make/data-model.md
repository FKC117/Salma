# Data Model: Sandbox UI with LLM Integration

**Feature**: 003-now-lets-make  
**Date**: 2025-09-29  
**Status**: Complete

## Entity Definitions

### ChatMessage (Enhanced)
**Purpose**: Store chat messages with analysis context integration
**Relationships**: 
- Belongs to User (existing)
- Belongs to AnalysisSession (existing)
- References AnalysisResult (existing)
- References Dataset (via AnalysisSession)

**Fields**:
- All existing fields maintained
- `analysis_context` (JSONField): Context about current dataset and analysis state
- `suggested_analysis` (JSONField): AI-suggested analysis tools and parameters
- `executed_analysis_id` (ForeignKey): Reference to executed analysis result

**Validation Rules**:
- Message content must not exceed 4000 characters
- Analysis context must be valid JSON
- Suggested analysis must reference valid analysis tools

### ChatSession (New)
**Purpose**: Manage conversation context and state
**Relationships**:
- Belongs to User
- Belongs to AnalysisSession
- Has many ChatMessages

**Fields**:
- `user` (ForeignKey to User)
- `analysis_session` (ForeignKey to AnalysisSession)
- `is_active` (BooleanField): Whether session is currently active
- `context_summary` (TextField): AI-generated summary of conversation context
- `last_activity` (DateTimeField): Last message timestamp
- `created_at` (DateTimeField)
- `updated_at` (DateTimeField)

**Validation Rules**:
- Only one active ChatSession per AnalysisSession
- Context summary must not exceed 1000 characters

### AnalysisSuggestion (New)
**Purpose**: Store AI-generated analysis suggestions
**Relationships**:
- Belongs to ChatMessage
- References AnalysisTool
- References Dataset

**Fields**:
- `chat_message` (ForeignKey to ChatMessage)
- `analysis_tool` (ForeignKey to AnalysisTool)
- `suggested_parameters` (JSONField): Suggested tool parameters
- `confidence_score` (FloatField): AI confidence in suggestion (0.0-1.0)
- `reasoning` (TextField): AI explanation for suggestion
- `is_executed` (BooleanField): Whether suggestion was executed
- `execution_result` (ForeignKey to AnalysisResult, nullable)
- `created_at` (DateTimeField)

**Validation Rules**:
- Confidence score must be between 0.0 and 1.0
- Suggested parameters must match tool parameter schema
- Reasoning must not exceed 500 characters

## Model Relationships

```
User
├── AnalysisSession (existing)
│   ├── ChatSession (new)
│   │   └── ChatMessage (enhanced)
│   │       └── AnalysisSuggestion (new)
│   └── AnalysisResult (existing)
└── Dataset (existing)
    └── AnalysisResult (existing)
```

## State Transitions

### ChatSession States
- **Created**: Initial state when first message sent
- **Active**: Receiving messages and generating responses
- **Paused**: Temporarily inactive (user switched datasets)
- **Completed**: Session ended (user logged out or session expired)

### AnalysisSuggestion States
- **Generated**: AI created suggestion
- **Presented**: Suggestion shown to user
- **Accepted**: User chose to execute suggestion
- **Executed**: Analysis tool executed successfully
- **Rejected**: User declined suggestion

## Integration Points

### Existing Models Enhanced
- **ChatMessage**: Added analysis context and suggestion tracking
- **AnalysisSession**: No changes required (existing functionality sufficient)
- **AnalysisResult**: No changes required (existing functionality sufficient)
- **User**: No changes required (existing functionality sufficient)

### New Models
- **ChatSession**: Manages conversation state and context
- **AnalysisSuggestion**: Tracks AI-generated analysis recommendations

## Database Migrations Required

1. **Add fields to ChatMessage**:
   - `analysis_context` (JSONField, default=dict)
   - `suggested_analysis` (JSONField, default=dict)
   - `executed_analysis_id` (ForeignKey to AnalysisResult, nullable)

2. **Create ChatSession model**:
   - All fields as defined above
   - Indexes on user, analysis_session, is_active

3. **Create AnalysisSuggestion model**:
   - All fields as defined above
   - Indexes on chat_message, analysis_tool, is_executed

## Validation and Constraints

### ChatMessage Constraints
- Content length: 1-4000 characters
- Analysis context: Valid JSON structure
- Suggested analysis: References valid tools

### ChatSession Constraints
- One active session per AnalysisSession
- Context summary: 0-1000 characters
- Last activity: Must be updated on each message

### AnalysisSuggestion Constraints
- Confidence score: 0.0-1.0 range
- Reasoning: 0-500 characters
- Suggested parameters: Must match tool schema
- Execution result: Only set when is_executed=True

## Performance Considerations

### Indexes
- ChatSession: (user, analysis_session, is_active)
- AnalysisSuggestion: (chat_message, analysis_tool, is_executed)
- ChatMessage: (user, session, created_at)

### Query Optimization
- Use select_related for foreign key relationships
- Implement pagination for chat history
- Cache active ChatSession for current user
- Use prefetch_related for suggestion lists

## Security Considerations

### Data Access
- Users can only access their own ChatSessions
- ChatMessages inherit AnalysisSession permissions
- AnalysisSuggestions inherit ChatMessage permissions

### Data Sanitization
- All user input sanitized before storage
- Analysis context validated against schema
- Suggested parameters validated against tool definitions
- Reasoning text sanitized for XSS prevention
