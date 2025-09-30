"""
Chat Service for AI-Powered Data Analysis Conversations

This service handles chat message processing, context management, and analysis suggestions
by leveraging existing LLMProcessor, RAGService, and AnalysisExecutor services.
"""

import json
import logging
import time
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from django.conf import settings
from django.utils import timezone
from django.db import transaction
from django.core.cache import cache

from analytics.models import (
    ChatMessage, ChatSession, AnalysisSuggestion, AnalysisSession,
    AnalysisTool, AnalysisResult, User, Dataset, SandboxExecution
)
from analytics.services.llm_processor import LLMProcessor
from analytics.services.rag_service import RAGService
from analytics.services.analysis_executor import AnalysisExecutor
from analytics.services.session_manager import SessionManager
from analytics.services.audit_trail_manager import AuditTrailManager

logger = logging.getLogger(__name__)


class ChatService:
    """
    Service for managing AI-powered chat conversations with analysis suggestions
    """
    
    def __init__(self):
        self.llm_processor = LLMProcessor()
        self.rag_service = RAGService()
        self.analysis_executor = AnalysisExecutor()
        self.session_manager = SessionManager()
        self.audit_manager = AuditTrailManager()
        
        # Chat configuration
        self.max_context_messages = 10
        self.suggestion_confidence_threshold = 0.7
        self.context_cache_timeout = 3600  # 1 hour
    
    def send_message(self, message: str, user: User, session_id: Optional[int] = None,
                    include_suggestions: bool = True) -> Dict[str, Any]:
        """
        Send a chat message and get AI response with analysis suggestions
        
        Args:
            message: User's message
            user: User sending the message
            session_id: Analysis session ID (optional)
            include_suggestions: Whether to include analysis suggestions
            
        Returns:
            Dict containing chat message, AI response, and suggestions
        """
        correlation_id = f"chat_{int(timezone.now().timestamp())}"
        start_time = time.time()
        
        # DEBUG: Log input parameters
        print(f"=== CHAT SERVICE DEBUG ===")
        print(f"User ID: {getattr(user, 'id', 'None')}")
        print(f"Session ID: {session_id}")
        print(f"Message: {message[:100]}{'...' if len(message) > 100 else ''}")
        print(f"Include suggestions: {include_suggestions}")
        print(f"========================")
        
        try:
            # Get or create analysis session
            if session_id:
                analysis_session = AnalysisSession.objects.get(id=session_id, user=user)
            else:
                # Get current active session or create default
                analysis_session = self._get_or_create_active_session(user)
            
            # DEBUG: Log session info
            print(f"=== SESSION INFO DEBUG ===")
            print(f"Analysis Session ID: {getattr(analysis_session, 'id', 'None')}")
            print(f"Dataset ID: {getattr(getattr(analysis_session, 'primary_dataset', None), 'id', 'None') if getattr(analysis_session, 'primary_dataset', None) else 'None'}")
            print(f"=========================")
            
            # Get or create chat session
            chat_session = self._get_or_create_chat_session(user, analysis_session)
            
            # Create user message
            user_message = self._create_chat_message(
                user=user,
                content=message,
                message_type='user',
                session=analysis_session,
                chat_session=chat_session
            )
            
            # Get context for AI response
            context = self._get_chat_context(chat_session, analysis_session)
            rag_context = self._get_rag_context(message, analysis_session, user)
            
            # Generate AI response with dataset context
            print(f"=== CALLING LLM PROCESSOR ===")
            ai_response = self.llm_processor.generate_text(
                prompt=message,
                user=user,
                context_messages=context,
                session=analysis_session,  # Pass session for dataset context
                rag_context=rag_context
            )
            print(f"=== LLM RESPONSE RECEIVED ===")
            print(f"AI Response success: {ai_response.get('success', 'N/A')}")
            print(f"AI Response text length: {len(ai_response.get('text', ''))}")
            print(f"============================")
            
            # Create AI message
            ai_message = self._create_chat_message(
                user=user,
                content=ai_response['text'],
                message_type='assistant',
                session=analysis_session,
                chat_session=chat_session,
                analysis_context={
                    'dataset_id': getattr(getattr(analysis_session, 'primary_dataset', None), 'id', None) if getattr(analysis_session, 'primary_dataset', None) else None,
                    'dataset_name': getattr(getattr(analysis_session, 'primary_dataset', None), 'name', None) if getattr(analysis_session, 'primary_dataset', None) else None,
                    'session_id': getattr(analysis_session, 'id', None),
                    'tokens_used': {
                        'input_tokens': ai_response.get('input_tokens', 0),
                        'output_tokens': ai_response.get('output_tokens', 0),
                        'total_tokens': ai_response.get('total_tokens', 0)
                    }
                }
            )
            
            # Generate analysis suggestions if requested
            suggestions = []
            if include_suggestions:
                print(f"=== GENERATING SUGGESTIONS ===")
                suggestions = self._generate_analysis_suggestions(
                    ai_message, analysis_session, user
                )
                print(f"=== SUGGESTIONS GENERATED ===")
                print(f"Number of suggestions: {len(suggestions)}")
                print(f"=============================")
            
            # Update chat session activity
            chat_session.last_activity = timezone.now()
            chat_session.save()
            
            # Log audit trail
            self.audit_manager.log_user_action(
                user_id=getattr(user, 'id', None),
                action_type='chat_message_sent',
                resource_type='chat_message',
                resource_id=getattr(user_message, 'id', None),
                resource_name="Chat Message",
                action_description=f"Sent message: {message[:100]}...",
                success=True,
                correlation_id=correlation_id,
                execution_time_ms=int((time.time() - start_time) * 1000)
            )
            
            logger.info(f"Chat message processed successfully for user {getattr(user, 'id', 'None')}")
            
            result = {
                'success': True,
                'chat_message': {
                    'id': getattr(user_message, 'id', None),
                    'content': user_message.content,
                    'message_type': user_message.message_type,
                    'created_at': user_message.created_at.isoformat(),
                    'analysis_context': user_message.analysis_context
                },
                'ai_response': {
                    'id': getattr(ai_message, 'id', None),
                    'content': ai_message.content,
                    'message_type': ai_message.message_type,
                    'created_at': ai_message.created_at.isoformat(),
                    'analysis_context': ai_message.analysis_context,
                    'suggestions': [
                        {
                            'id': getattr(suggestion, 'id', None),
                            'tool_name': getattr(getattr(suggestion, 'analysis_tool', None), 'name', None) if getattr(suggestion, 'analysis_tool', None) else None,
                            'tool_display_name': getattr(getattr(suggestion, 'analysis_tool', None), 'display_name', None) if getattr(suggestion, 'analysis_tool', None) else None,
                            'suggested_parameters': suggestion.suggested_parameters,
                            'confidence_score': suggestion.confidence_score,
                            'reasoning': suggestion.reasoning
                        }
                        for suggestion in suggestions
                    ]
                },
                'tokens_used': {
                    'input_tokens': ai_response.get('input_tokens', 0),
                    'output_tokens': ai_response.get('output_tokens', 0),
                    'total_tokens': ai_response.get('total_tokens', 0)
                },
                'session_info': {
                    'id': getattr(analysis_session, 'id', None),
                    'name': analysis_session.name,
                    'dataset_name': getattr(getattr(analysis_session, 'primary_dataset', None), 'name', None) if getattr(analysis_session, 'primary_dataset', None) else None,
                    'dataset_id': getattr(getattr(analysis_session, 'primary_dataset', None), 'id', None) if getattr(analysis_session, 'primary_dataset', None) else None
                }
            }
            
            # DEBUG: Log final result
            print(f"=== CHAT SERVICE FINAL RESULT ===")
            print(f"Success: {result['success']}")
            print(f"User message ID: {result['chat_message']['id']}")
            print(f"AI response ID: {result['ai_response']['id']}")
            print(f"Session ID: {result['session_info']['id']}")
            print(f"Dataset ID: {result['session_info']['dataset_id']}")
            print(f"================================")
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing chat message: {str(e)}")
            print(f"=== ERROR IN CHAT SERVICE ===")
            print(f"Error: {str(e)}")
            print(f"User ID: {getattr(user, 'id', 'None')}")
            print(f"Session ID: {session_id}")
            print(f"=============================")
            return {
                'success': False,
                'error': 'Failed to process chat message',
                'details': str(e)
            }
    
    def get_chat_history(self, user: User, session_id: Optional[int] = None,
                        limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """
        Get chat history for a session
        
        Args:
            user: User requesting history
            session_id: Analysis session ID (optional)
            limit: Number of messages to return
            offset: Offset for pagination
            
        Returns:
            Dict containing chat history and pagination info
        """
        try:
            # Get analysis session
            if session_id:
                analysis_session = AnalysisSession.objects.get(id=session_id, user=user)
            else:
                analysis_session = self._get_or_create_active_session(user)
            
            # Get chat messages
            messages = ChatMessage.objects.filter(
                session=analysis_session,
                user=user
            ).order_by('-created_at')[offset:offset + limit]
            
            # Get suggestions for each message
            message_data = []
            for message in messages:
                suggestions = AnalysisSuggestion.objects.filter(
                    chat_message=message
                ).order_by('-confidence_score')
                
                message_data.append({
                    'id': message.id,
                    'content': message.content,
                    'message_type': message.message_type,
                    'created_at': message.created_at.isoformat(),
                    'analysis_context': message.analysis_context,
                    'suggestions': [
                        {
                            'id': suggestion.id,
                            'tool_name': suggestion.analysis_tool.name,
                            'tool_display_name': suggestion.analysis_tool.display_name,
                            'suggested_parameters': suggestion.suggested_parameters,
                            'confidence_score': suggestion.confidence_score,
                            'reasoning': suggestion.reasoning,
                            'is_executed': suggestion.is_executed,
                            'execution_result_id': suggestion.execution_result.id if suggestion.execution_result else None
                        }
                        for suggestion in suggestions
                    ]
                })
            
            # Get total count
            total_count = ChatMessage.objects.filter(
                session=analysis_session,
                user=user
            ).count()
            
            return {
                'success': True,
                'messages': message_data,
                'pagination': {
                    'total_count': total_count,
                    'limit': limit,
                    'offset': offset,
                    'has_next': offset + limit < total_count
                },
                'session_info': {
                    'id': analysis_session.id,
                    'name': analysis_session.name,
                    'dataset_name': analysis_session.primary_dataset.name,
                    'dataset_id': analysis_session.primary_dataset.id,
                    'is_active': True
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting chat history: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to get chat history',
                'details': str(e)
            }
    
    def get_chat_context(self, user: User, session_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Get current chat context including dataset and session info
        
        Args:
            user: User requesting context
            session_id: Analysis session ID (optional)
            
        Returns:
            Dict containing current context
        """
        try:
            # Get analysis session
            if session_id:
                analysis_session = AnalysisSession.objects.get(id=session_id, user=user)
            else:
                analysis_session = self._get_or_create_active_session(user)
            
            # Get dataset info
            dataset = analysis_session.primary_dataset
            dataset_info = {
                'id': dataset.id,
                'name': dataset.name,
                'description': dataset.description,
                'row_count': dataset.row_count,
                'column_count': dataset.column_count,
                'data_types': dataset.data_types,
                'data_quality_score': dataset.data_quality_score,
                'created_at': dataset.created_at.isoformat(),
                'original_filename': dataset.original_filename
            }
            
            # Get recent analyses
            recent_analyses = AnalysisResult.objects.filter(
                session=analysis_session,
                user=user
            ).order_by('-created_at')[:5]
            
            recent_analyses_data = [
                {
                    'id': result.id,
                    'name': result.name,
                    'tool_name': result.tool_used.name if result.tool_used else 'Unknown',
                    'created_at': result.created_at.isoformat(),
                    'result_type': result.output_type
                }
                for result in recent_analyses
            ]
            
            # Get available tools
            available_tools = AnalysisTool.objects.filter(is_active=True).order_by('category', 'display_name')
            tools_data = [
                {
                    'id': tool.id,
                    'name': tool.name,
                    'display_name': tool.display_name,
                    'category': tool.category,
                    'description': tool.description
                }
                for tool in available_tools
            ]
            
            return {
                'success': True,
                'current_session': {
                    'id': analysis_session.id,
                    'name': analysis_session.name,
                    'dataset_name': dataset.name,
                    'dataset_id': dataset.id,
                    'analysis_count': analysis_session.analysis_count,
                    'last_analysis_at': analysis_session.last_analysis_at.isoformat() if analysis_session.last_analysis_at else None
                },
                'current_dataset': dataset_info,
                'recent_analyses': recent_analyses_data,
                'available_tools': tools_data
            }
            
        except Exception as e:
            logger.error(f"Error getting chat context: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to get chat context',
                'details': str(e)
            }
    
    def _get_or_create_active_session(self, user: User) -> AnalysisSession:
        """Get or create an active analysis session for the user"""
        try:
            # Try to get the most recent active session
            session = AnalysisSession.objects.filter(
                user=user,
                is_active=True
            ).order_by('-last_accessed').first()
            
            if session:
                return session
            
            # Create a default session if none exists
            default_dataset = Dataset.objects.filter(user=user).first()
            if not default_dataset:
                raise ValueError("No datasets available for user")
            
            session = AnalysisSession.objects.create(
                name=f"Session for {default_dataset.name}",
                description="Default analysis session",
                primary_dataset=default_dataset,
                user=user,
                is_active=True
            )
            
            logger.info(f"Created default analysis session {session.id} for user {user.id}")
            return session
            
        except Exception as e:
            logger.error(f"Error getting/creating active session: {str(e)}")
            raise
    
    def _get_or_create_chat_session(self, user: User, analysis_session: AnalysisSession) -> ChatSession:
        """Get or create a chat session for the analysis session"""
        try:
            # Try to get existing active chat session
            chat_session = ChatSession.objects.filter(
                user=user,
                analysis_session=analysis_session,
                is_active=True
            ).first()
            
            if chat_session:
                return chat_session
            
            # Create new chat session
            chat_session = ChatSession.objects.create(
                user=user,
                analysis_session=analysis_session,
                is_active=True
            )
            
            logger.info(f"Created chat session {chat_session.id} for analysis session {analysis_session.id}")
            return chat_session
            
        except Exception as e:
            logger.error(f"Error getting/creating chat session: {str(e)}")
            raise
    
    def _create_chat_message(self, user: User, content: str, message_type: str,
                           session: AnalysisSession, chat_session: ChatSession,
                           analysis_context: Optional[Dict] = None) -> ChatMessage:
        """Create a chat message record"""
        return ChatMessage.objects.create(
            user=user,
            content=content,
            message_type=message_type,
            session=session,
            analysis_context=analysis_context or {},
            llm_model=self.llm_processor.ollama_model if self.llm_processor.use_ollama else getattr(self.llm_processor, 'model_name', 'unknown'),
            token_count=len(content.split())  # Simple token estimation
        )
    
    def _get_chat_context(self, chat_session: ChatSession, analysis_session: AnalysisSession) -> List[Dict]:
        """Get recent chat context for LLM"""
        recent_messages = ChatMessage.objects.filter(
            session=analysis_session,
            user=chat_session.user
        ).order_by('-created_at')[:self.max_context_messages]
        
        context = []
        for message in reversed(recent_messages):  # Reverse to get chronological order
            context.append({
                'role': 'user' if message.message_type == 'user' else 'assistant',
                'content': message.content
            })
        
        return context
    
    def _get_rag_context(self, message: str, analysis_session: AnalysisSession, user: User) -> Optional[str]:
        """Get relevant context from RAG system"""
        try:
            # Search for relevant context using the correct method
            rag_results = self.rag_service.search_vectors_by_text(
                query=message,
                user=user,
                dataset=analysis_session.primary_dataset,
                top_k=3
            )
            
            if rag_results:
                context_parts = []
                for result in rag_results:
                    content = result.get('content', '') or result.get('text', '')
                    if content:
                        context_parts.append(f"- {content[:200]}...")
                
                if context_parts:
                    return f"Relevant context:\n" + "\n".join(context_parts)
            
            return None
            
        except Exception as e:
            logger.warning(f"RAG context retrieval failed: {str(e)}")
            return None
    
    def _generate_analysis_suggestions(self, ai_message: ChatMessage, 
                                     analysis_session: AnalysisSession, 
                                     user: User) -> List[AnalysisSuggestion]:
        """Generate analysis suggestions based on AI response"""
        try:
            # Use LLM to generate suggestions based on the response and dataset
            dataset = analysis_session.primary_dataset
            
            suggestion_prompt = f"""
            Based on this AI response about dataset "{dataset.name}" with {dataset.row_count} rows and {dataset.column_count} columns:
            
            AI Response: {ai_message.content}
            
            Dataset columns: {list(dataset.data_types.keys()) if dataset.data_types else []}
            
            Suggest 2-3 specific analysis tools that would be most relevant. For each suggestion, provide:
            1. Tool name (from available tools)
            2. Suggested parameters
            3. Confidence score (0.0-1.0)
            4. Brief reasoning
            
            Available tools: descriptive_stats, correlation_matrix, regression_analysis, scatter_plot, histogram, box_plot, missing_data_analysis, outlier_detection, kmeans_clustering, time_series_plot
            
            Format as JSON array with fields: tool_name, parameters, confidence_score, reasoning
            """
            
            # Generate suggestions using LLM
            suggestions_response = self.llm_processor.generate_text(
                prompt=suggestion_prompt,
                user=user,
                session=analysis_session
            )
            
            # Parse suggestions and create AnalysisSuggestion objects
            suggestions = []
            try:
                logger.info(f"Suggestions response: {suggestions_response['text'][:500]}...")
                suggestions_data = json.loads(suggestions_response['text'])
                
                for suggestion_data in suggestions_data:
                    if suggestion_data.get('confidence_score', 0) >= self.suggestion_confidence_threshold:
                        try:
                            tool = AnalysisTool.objects.get(name=suggestion_data['tool_name'])
                            
                            suggestion = AnalysisSuggestion.objects.create(
                                chat_message=ai_message,
                                analysis_tool=tool,
                                suggested_parameters=suggestion_data.get('parameters', {}),
                                confidence_score=suggestion_data.get('confidence_score', 0.5),
                                reasoning=suggestion_data.get('reasoning', '')
                            )
                            suggestions.append(suggestion)
                            
                        except AnalysisTool.DoesNotExist:
                            logger.warning(f"Tool {suggestion_data['tool_name']} not found")
                            continue
                            
            except json.JSONDecodeError:
                logger.warning("Failed to parse suggestions JSON")
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error generating analysis suggestions: {str(e)}")
            return []
