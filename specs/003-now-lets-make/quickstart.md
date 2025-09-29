# Quickstart Guide: Sandbox UI with LLM Integration

**Feature**: 003-now-lets-make  
**Date**: 2025-09-29  
**Status**: Complete

## Prerequisites

- Django application running with existing dashboard
- User authenticated and logged in
- At least one dataset uploaded
- Active analysis session
- Google AI API key configured
- Virtual environment activated

## Quick Test Scenarios

### Scenario 1: Basic Chat Interaction
**Goal**: Verify basic chat functionality with AI responses

**Steps**:
1. Navigate to dashboard (`/dashboard/`)
2. Ensure a dataset is loaded in the main panel
3. Open the chat panel (right side of three-panel layout)
4. Type: "Hello, can you tell me about this dataset?"
5. Press Enter or click Send
6. **Expected**: AI responds with dataset overview and analysis suggestions

**Validation**:
- ✅ Chat message appears in chat history
- ✅ AI response generated within 5 seconds
- ✅ Response includes dataset information
- ✅ Analysis suggestions displayed
- ✅ Token usage tracked

### Scenario 2: Analysis Suggestion Execution
**Goal**: Test AI-suggested analysis execution

**Steps**:
1. Complete Scenario 1
2. In AI response, click on a suggested analysis tool
3. **Expected**: Analysis tool executes automatically
4. **Expected**: Results appear in main dashboard panel

**Validation**:
- ✅ Suggestion marked as executed
- ✅ Analysis result displayed in card format
- ✅ Results integrated with existing analysis history
- ✅ Execution time tracked

### Scenario 3: Context-Aware Responses
**Goal**: Verify AI maintains context across conversation

**Steps**:
1. Complete Scenario 2
2. Ask: "What does this correlation matrix show?"
3. **Expected**: AI explains the specific correlation matrix from previous analysis
4. Ask: "What should I analyze next?"
5. **Expected**: AI suggests relevant next steps based on current results

**Validation**:
- ✅ AI references previous analysis results
- ✅ Suggestions are contextually relevant
- ✅ Conversation history maintained
- ✅ Context summary updated

### Scenario 4: Dataset Switching Integration
**Goal**: Test chat integration with dataset switching

**Steps**:
1. Complete Scenario 3
2. Switch to a different dataset using dataset switcher
3. Ask: "Tell me about this new dataset"
4. **Expected**: AI responds about the new dataset
5. **Expected**: Previous conversation context preserved

**Validation**:
- ✅ AI recognizes dataset change
- ✅ Response relevant to new dataset
- ✅ Previous conversation accessible
- ✅ Analysis suggestions updated for new dataset

### Scenario 5: Error Handling
**Goal**: Verify graceful error handling

**Steps**:
1. Ask: "Analyze the data using a tool that doesn't exist"
2. **Expected**: AI explains limitation and suggests alternatives
3. Send empty message
4. **Expected**: System prompts for valid input
5. Ask question exceeding token limits
6. **Expected**: System explains token limit and suggests shorter question

**Validation**:
- ✅ Error messages are user-friendly
- ✅ System suggests alternatives
- ✅ No system crashes or errors
- ✅ Token limits properly enforced

## Integration Tests

### Test 1: Chat Message Flow
```python
def test_chat_message_flow():
    # Send message
    response = client.post('/api/chat/send/', {
        'message': 'What are the key trends in this data?',
        'session_id': session.id
    })
    assert response.status_code == 200
    assert 'ai_response' in response.json()
    
    # Verify message stored
    chat_message = ChatMessage.objects.filter(
        message_type='user'
    ).last()
    assert chat_message.content == 'What are the key trends in this data?'
```

### Test 2: Analysis Suggestion Execution
```python
def test_suggestion_execution():
    # Create suggestion
    suggestion = AnalysisSuggestion.objects.create(
        chat_message=chat_message,
        analysis_tool=descriptive_stats_tool,
        suggested_parameters={'columns': 'all'},
        confidence_score=0.8
    )
    
    # Execute suggestion
    response = client.post('/api/chat/execute-suggestion/', {
        'suggestion_id': suggestion.id
    })
    assert response.status_code == 200
    assert suggestion.is_executed == True
```

### Test 3: Context Management
```python
def test_context_management():
    # Get context
    response = client.get('/api/chat/context/')
    assert response.status_code == 200
    
    context = response.json()
    assert 'current_dataset' in context
    assert 'recent_analyses' in context
    assert 'available_tools' in context
```

## Performance Benchmarks

### Response Time Targets
- Chat message processing: < 2 seconds
- AI response generation: < 5 seconds
- Analysis suggestion execution: < 3 seconds
- Context retrieval: < 500ms

### Load Testing
- Support 50 concurrent chat sessions
- Handle 1000 messages per hour per user
- Maintain < 1 second response time under load

## Troubleshooting

### Common Issues

**Issue**: Chat not responding
- **Check**: Virtual environment activated
- **Check**: Google AI API key configured
- **Check**: User authentication status
- **Check**: Token limits not exceeded

**Issue**: Analysis suggestions not executing
- **Check**: Dataset loaded and accessible
- **Check**: Analysis tools properly configured
- **Check**: User permissions for analysis execution
- **Check**: Tool parameters valid

**Issue**: Context not maintained
- **Check**: Analysis session active
- **Check**: Chat session properly linked
- **Check**: RAG system operational
- **Check**: Redis connection stable

### Debug Commands
```bash
# Check chat sessions
python manage.py shell -c "from analytics.models import ChatSession; print(ChatSession.objects.filter(is_active=True).count())"

# Check token usage
python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); user = User.objects.get(id=1); print(f'Tokens used: {user.tokens_used_this_month}')"

# Check RAG system
python manage.py shell -c "from analytics.services.rag_service import RAGService; rag = RAGService(); print(rag.get_index_stats())"
```

## Success Criteria

### Functional Requirements
- ✅ Chat interface integrated into dashboard
- ✅ AI responses generated for user questions
- ✅ Analysis suggestions provided and executable
- ✅ Context maintained across conversation
- ✅ Integration with existing analysis tools
- ✅ Results displayed in existing card format

### Performance Requirements
- ✅ Response times meet benchmarks
- ✅ System handles expected load
- ✅ Token usage properly tracked
- ✅ Error handling graceful

### User Experience Requirements
- ✅ Intuitive chat interface
- ✅ Clear analysis suggestions
- ✅ Seamless integration with existing workflow
- ✅ Consistent visual design
- ✅ Helpful error messages

## Next Steps

After successful quickstart validation:
1. Run full test suite
2. Deploy to staging environment
3. Conduct user acceptance testing
4. Monitor performance metrics
5. Gather user feedback
6. Iterate based on feedback
