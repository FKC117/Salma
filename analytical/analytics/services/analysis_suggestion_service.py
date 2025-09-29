"""
Analysis Suggestion Service for AI-Generated Analysis Recommendations

This service handles the execution of AI-suggested analysis tools by leveraging
the existing AnalysisExecutor and integrating with the chat system.
"""

import logging
import time
from typing import Dict, List, Any, Optional
from django.utils import timezone
from django.db import transaction

from analytics.models import (
    AnalysisSuggestion, AnalysisResult, AnalysisSession, User, AnalysisTool
)
from analytics.services.analysis_executor import AnalysisExecutor
from analytics.services.audit_trail_manager import AuditTrailManager

logger = logging.getLogger(__name__)


class AnalysisSuggestionService:
    """
    Service for managing and executing AI-generated analysis suggestions
    """
    
    def __init__(self):
        self.analysis_executor = AnalysisExecutor()
        self.audit_manager = AuditTrailManager()
    
    def execute_suggestion(self, suggestion_id: int, user: User, 
                          parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute an analysis suggestion
        
        Args:
            suggestion_id: ID of the analysis suggestion
            user: User executing the suggestion
            parameters: Optional parameter overrides
            
        Returns:
            Dict containing execution result and updated suggestion
        """
        correlation_id = f"suggestion_{int(timezone.now().timestamp())}"
        start_time = time.time()
        
        try:
            # Get the suggestion
            suggestion = AnalysisSuggestion.objects.get(id=suggestion_id)
            
            # Verify user owns the suggestion
            if suggestion.chat_message.user != user:
                return {
                    'success': False,
                    'error': 'Access denied to suggestion'
                }
            
            # Check if already executed
            if suggestion.is_executed:
                return {
                    'success': True,
                    'message': 'Suggestion already executed',
                    'suggestion': self._format_suggestion(suggestion),
                    'analysis_result': self._format_analysis_result(suggestion.execution_result) if suggestion.execution_result else None
                }
            
            # Get analysis session
            analysis_session = suggestion.chat_message.session
            
            # Use provided parameters or suggested parameters
            execution_parameters = parameters or suggestion.suggested_parameters
            
            # Execute the analysis tool
            with transaction.atomic():
                execution_result = self.analysis_executor.execute_analysis(
                    tool_name=suggestion.analysis_tool.name,
                    parameters=execution_parameters,
                    session=analysis_session,
                    user=user
                )
                
                if execution_result['success']:
                    # Get the created analysis result
                    analysis_result = AnalysisResult.objects.get(
                        id=execution_result['analysis_result_id']
                    )
                    
                    # Update suggestion
                    suggestion.is_executed = True
                    suggestion.execution_result = analysis_result
                    suggestion.save()
                    
                    # Log audit trail
                    self.audit_manager.log_user_action(
                        user_id=user.id,
                        action_type='analysis_suggestion_executed',
                        resource_type='analysis_suggestion',
                        resource_id=suggestion.id,
                        resource_name="Analysis Suggestion Execution",
                        action_description=f"Executed suggestion: {suggestion.analysis_tool.display_name}",
                        success=True,
                        correlation_id=correlation_id,
                        execution_time_ms=int((time.time() - start_time) * 1000)
                    )
                    
                    logger.info(f"Analysis suggestion {suggestion_id} executed successfully")
                    
                    return {
                        'success': True,
                        'suggestion': self._format_suggestion(suggestion),
                        'analysis_result': self._format_analysis_result(analysis_result),
                        'execution_time_ms': execution_result.get('execution_time_ms', 0)
                    }
                else:
                    # Log failed execution
                    self.audit_manager.log_user_action(
                        user_id=user.id,
                        action_type='analysis_suggestion_execution_failed',
                        resource_type='analysis_suggestion',
                        resource_id=suggestion.id,
                        resource_name="Analysis Suggestion Execution Failed",
                        action_description=f"Failed to execute suggestion: {suggestion.analysis_tool.display_name}",
                        success=False,
                        correlation_id=correlation_id,
                        execution_time_ms=int((time.time() - start_time) * 1000)
                    )
                    
                    return {
                        'success': False,
                        'error': 'Analysis execution failed',
                        'details': execution_result.get('error', 'Unknown error')
                    }
            
        except AnalysisSuggestion.DoesNotExist:
            return {
                'success': False,
                'error': 'Suggestion not found'
            }
        except Exception as e:
            logger.error(f"Error executing suggestion {suggestion_id}: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to execute suggestion',
                'details': str(e)
            }
    
    def get_suggestion_details(self, suggestion_id: int, user: User) -> Dict[str, Any]:
        """
        Get detailed information about a suggestion
        
        Args:
            suggestion_id: ID of the suggestion
            user: User requesting details
            
        Returns:
            Dict containing suggestion details
        """
        try:
            suggestion = AnalysisSuggestion.objects.get(id=suggestion_id)
            
            # Verify user access
            if suggestion.chat_message.user != user:
                return {
                    'success': False,
                    'error': 'Access denied to suggestion'
                }
            
            return {
                'success': True,
                'suggestion': self._format_suggestion(suggestion),
                'analysis_result': self._format_analysis_result(suggestion.execution_result) if suggestion.execution_result else None,
                'chat_message': {
                    'id': suggestion.chat_message.id,
                    'content': suggestion.chat_message.content[:200] + "..." if len(suggestion.chat_message.content) > 200 else suggestion.chat_message.content,
                    'created_at': suggestion.chat_message.created_at.isoformat()
                }
            }
            
        except AnalysisSuggestion.DoesNotExist:
            return {
                'success': False,
                'error': 'Suggestion not found'
            }
        except Exception as e:
            logger.error(f"Error getting suggestion details {suggestion_id}: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to get suggestion details',
                'details': str(e)
            }
    
    def list_user_suggestions(self, user: User, session_id: Optional[int] = None,
                            limit: int = 20, offset: int = 0) -> Dict[str, Any]:
        """
        List suggestions for a user
        
        Args:
            user: User requesting suggestions
            session_id: Optional session filter
            limit: Number of suggestions to return
            offset: Offset for pagination
            
        Returns:
            Dict containing suggestions list and pagination info
        """
        try:
            # Build query
            query = AnalysisSuggestion.objects.filter(
                chat_message__user=user
            )
            
            if session_id:
                query = query.filter(chat_message__session_id=session_id)
            
            # Get suggestions
            suggestions = query.order_by('-created_at')[offset:offset + limit]
            
            # Format suggestions
            suggestions_data = [self._format_suggestion(suggestion) for suggestion in suggestions]
            
            # Get total count
            total_count = query.count()
            
            return {
                'success': True,
                'suggestions': suggestions_data,
                'pagination': {
                    'total_count': total_count,
                    'limit': limit,
                    'offset': offset,
                    'has_next': offset + limit < total_count
                }
            }
            
        except Exception as e:
            logger.error(f"Error listing suggestions for user {user.id}: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to list suggestions',
                'details': str(e)
            }
    
    def get_suggestions_by_confidence(self, user: User, min_confidence: float = 0.7,
                                     limit: int = 10) -> List[AnalysisSuggestion]:
        """
        Get high-confidence suggestions for a user
        
        Args:
            user: User requesting suggestions
            min_confidence: Minimum confidence threshold
            limit: Maximum number of suggestions
            
        Returns:
            List of high-confidence suggestions
        """
        try:
            suggestions = AnalysisSuggestion.objects.filter(
                chat_message__user=user,
                confidence_score__gte=min_confidence,
                is_executed=False
            ).order_by('-confidence_score', '-created_at')[:limit]
            
            return list(suggestions)
            
        except Exception as e:
            logger.error(f"Error getting high-confidence suggestions: {str(e)}")
            return []
    
    def update_suggestion_feedback(self, suggestion_id: int, user: User,
                                 feedback: str, rating: Optional[int] = None) -> Dict[str, Any]:
        """
        Update feedback for a suggestion (for future ML improvement)
        
        Args:
            suggestion_id: ID of the suggestion
            user: User providing feedback
            feedback: Feedback text
            rating: Optional rating (1-5)
            
        Returns:
            Dict containing update result
        """
        try:
            suggestion = AnalysisSuggestion.objects.get(id=suggestion_id)
            
            # Verify user access
            if suggestion.chat_message.user != user:
                return {
                    'success': False,
                    'error': 'Access denied to suggestion'
                }
            
            # Store feedback in metadata (for future ML training)
            metadata = suggestion.chat_message.metadata or {}
            metadata['suggestion_feedback'] = {
                'suggestion_id': suggestion_id,
                'feedback': feedback,
                'rating': rating,
                'timestamp': timezone.now().isoformat()
            }
            
            suggestion.chat_message.metadata = metadata
            suggestion.chat_message.save()
            
            logger.info(f"Feedback updated for suggestion {suggestion_id}")
            
            return {
                'success': True,
                'message': 'Feedback recorded successfully'
            }
            
        except AnalysisSuggestion.DoesNotExist:
            return {
                'success': False,
                'error': 'Suggestion not found'
            }
        except Exception as e:
            logger.error(f"Error updating suggestion feedback {suggestion_id}: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to update feedback',
                'details': str(e)
            }
    
    def _format_suggestion(self, suggestion: AnalysisSuggestion) -> Dict[str, Any]:
        """Format suggestion for API response"""
        return {
            'id': suggestion.id,
            'tool_name': suggestion.analysis_tool.name,
            'tool_display_name': suggestion.analysis_tool.display_name,
            'tool_category': suggestion.analysis_tool.category,
            'suggested_parameters': suggestion.suggested_parameters,
            'confidence_score': suggestion.confidence_score,
            'reasoning': suggestion.reasoning,
            'is_executed': suggestion.is_executed,
            'execution_result_id': suggestion.execution_result.id if suggestion.execution_result else None,
            'created_at': suggestion.created_at.isoformat()
        }
    
    def _format_analysis_result(self, analysis_result: AnalysisResult) -> Dict[str, Any]:
        """Format analysis result for API response"""
        return {
            'id': analysis_result.id,
            'name': analysis_result.name,
            'description': analysis_result.description,
            'result_type': analysis_result.output_type,
            'tool_name': analysis_result.tool_used.name if analysis_result.tool_used else 'Unknown',
            'tool_display_name': analysis_result.tool_used.display_name if analysis_result.tool_used else 'Unknown',
            'execution_time_ms': analysis_result.execution_time_ms,
            'confidence_score': analysis_result.confidence_score,
            'quality_score': analysis_result.quality_score,
            'created_at': analysis_result.created_at.isoformat(),
            'result_data': analysis_result.result_data
        }
