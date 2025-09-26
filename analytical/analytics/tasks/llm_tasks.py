"""
LLM Processing Celery Tasks
Handles background LLM operations, chat processing, and AI interactions
"""

from celery import shared_task
from django.conf import settings
import json
import logging
from typing import Dict, Any, Optional, List
import time
import asyncio

from analytics.models import User
from analytics.services.llm_processor import LLMProcessor
from analytics.services.rag_service import RAGService
from analytics.services.audit_trail_manager import AuditTrailManager
from analytics.services.logging_service import StructuredLogger

logger = StructuredLogger(__name__)


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def process_chat_message(self, message: str, user_id: int, session_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Process chat message with LLM in background
    
    Args:
        message: User's chat message
        user_id: ID of user
        session_id: Optional session ID
        
    Returns:
        Dict with LLM response
    """
    try:
        logger.info(f"Processing chat message for user {user_id}", 
                   extra={'user_id': user_id, 'session_id': session_id})
        
        # Get user
        user = User.objects.get(id=user_id)
        
        # Initialize services
        llm_processor = LLMProcessor()
        rag_service = RAGService()
        audit_manager = AuditTrailManager()
        
        # Process message
        start_time = time.time()
        
        # Get context from RAG if available
        context = None
        if session_id:
            try:
                context = rag_service.search_relevant_context(message, user_id, limit=5)
            except Exception as e:
                logger.warning(f"RAG context retrieval failed: {str(e)}")
        
        # Generate LLM response
        response = llm_processor.generate_response(
            message=message,
            user=user,
            context=context,
            session_id=session_id
        )
        
        processing_time = time.time() - start_time
        
        # Log audit trail
        audit_manager.log_action(
            user=user,
            action='chat_message_processed',
            details={
                'message_length': len(message),
                'response_length': len(response.get('content', '')),
                'processing_time': processing_time,
                'token_usage': response.get('token_usage', {}),
                'session_id': session_id
            }
        )
        
        logger.info(f"Chat message processed successfully", 
                   extra={'user_id': user_id, 'processing_time': processing_time})
        
        return {
            'status': 'success',
            'response': response,
            'processing_time': processing_time,
            'context_used': context is not None
        }
        
    except Exception as exc:
        logger.error(f"Chat message processing failed: {str(exc)}", 
                    extra={'user_id': user_id, 'session_id': session_id})
        
        # Log audit trail for failure
        try:
            user = User.objects.get(id=user_id)
            audit_manager.log_action(
                user=user,
                action='chat_processing_failed',
                details={
                    'error': str(exc),
                    'retry_count': self.request.retries,
                    'session_id': session_id
                }
            )
        except:
            pass
        
        # Retry if not max retries reached
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying chat processing (attempt {self.request.retries + 1})")
            raise self.retry(countdown=30 * (self.request.retries + 1))
        
        return {
            'status': 'error',
            'error': str(exc),
            'message': 'Chat processing failed after maximum retries'
        }


@shared_task(bind=True, max_retries=1)
def process_batch_chat_messages(self, messages: List[Dict[str, Any]], user_id: int) -> Dict[str, Any]:
    """
    Process multiple chat messages in batch
    
    Args:
        messages: List of message dicts [{'message': str, 'session_id': str}]
        user_id: ID of user
        
    Returns:
        Dict with batch results
    """
    try:
        logger.info(f"Processing batch chat messages for user {user_id}", 
                   extra={'user_id': user_id, 'message_count': len(messages)})
        
        results = []
        total_start_time = time.time()
        
        for i, msg_data in enumerate(messages):
            message = msg_data['message']
            session_id = msg_data.get('session_id')
            
            logger.info(f"Processing message {i+1}/{len(messages)}")
            
            # Process individual message
            result = process_chat_message(message, user_id, session_id)
            results.append({
                'message': message,
                'session_id': session_id,
                'result': result
            })
            
            # Check if we should stop on first failure
            if result.get('status') == 'error':
                logger.warning(f"Batch processing stopped due to error in message {i+1}")
                break
        
        total_processing_time = time.time() - total_start_time
        
        logger.info(f"Batch chat processing completed", 
                   extra={'user_id': user_id, 'total_time': total_processing_time})
        
        return {
            'status': 'success',
            'results': results,
            'total_processing_time': total_processing_time,
            'messages_processed': len(results)
        }
        
    except Exception as exc:
        logger.error(f"Batch chat processing failed: {str(exc)}", 
                    extra={'user_id': user_id})
        
        return {
            'status': 'error',
            'error': str(exc),
            'message': 'Batch chat processing failed'
        }


@shared_task(bind=True, max_retries=2)
def generate_ai_insights(self, dataset_id: int, user_id: int, analysis_context: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Generate AI insights for a dataset
    
    Args:
        dataset_id: ID of dataset
        user_id: ID of user
        analysis_context: Optional analysis context
        
    Returns:
        Dict with AI insights
    """
    try:
        logger.info(f"Generating AI insights for dataset {dataset_id}", 
                   extra={'user_id': user_id, 'dataset_id': dataset_id})
        
        # Get user
        user = User.objects.get(id=user_id)
        
        # Initialize services
        llm_processor = LLMProcessor()
        audit_manager = AuditTrailManager()
        
        # Prepare context for AI
        context_prompt = f"""
        Generate insights for dataset {dataset_id}.
        User: {user.username}
        """
        
        if analysis_context:
            context_prompt += f"\nAnalysis Context: {json.dumps(analysis_context, indent=2)}"
        
        # Generate insights
        start_time = time.time()
        
        insights = llm_processor.generate_insights(
            context_prompt=context_prompt,
            user=user,
            dataset_id=dataset_id
        )
        
        processing_time = time.time() - start_time
        
        # Log audit trail
        audit_manager.log_action(
            user=user,
            action='ai_insights_generated',
            details={
                'dataset_id': dataset_id,
                'processing_time': processing_time,
                'insights_length': len(insights.get('content', '')),
                'token_usage': insights.get('token_usage', {})
            }
        )
        
        logger.info(f"AI insights generated successfully", 
                   extra={'user_id': user_id, 'dataset_id': dataset_id, 'processing_time': processing_time})
        
        return {
            'status': 'success',
            'insights': insights,
            'processing_time': processing_time
        }
        
    except Exception as exc:
        logger.error(f"AI insights generation failed: {str(exc)}", 
                    extra={'user_id': user_id, 'dataset_id': dataset_id})
        
        # Log audit trail for failure
        try:
            user = User.objects.get(id=user_id)
            audit_manager.log_action(
                user=user,
                action='ai_insights_failed',
                details={
                    'dataset_id': dataset_id,
                    'error': str(exc),
                    'retry_count': self.request.retries
                }
            )
        except:
            pass
        
        # Retry if not max retries reached
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying AI insights generation (attempt {self.request.retries + 1})")
            raise self.retry(countdown=60 * (self.request.retries + 1))
        
        return {
            'status': 'error',
            'error': str(exc),
            'message': 'AI insights generation failed after maximum retries'
        }


@shared_task
def update_rag_index(user_id: int, content: str, content_type: str, metadata: Optional[Dict] = None):
    """
    Update RAG index with new content
    
    Args:
        user_id: ID of user
        content: Content to index
        content_type: Type of content (dataset, analysis, etc.)
        metadata: Optional metadata
    """
    try:
        logger.info(f"Updating RAG index for user {user_id}", 
                   extra={'user_id': user_id, 'content_type': content_type})
        
        # Initialize RAG service
        rag_service = RAGService()
        
        # Update index
        result = rag_service.upsert_content(
            content=content,
            user_id=user_id,
            content_type=content_type,
            metadata=metadata or {}
        )
        
        logger.info(f"RAG index updated successfully", 
                   extra={'user_id': user_id, 'content_type': content_type})
        
        return {
            'status': 'success',
            'result': result
        }
        
    except Exception as exc:
        logger.error(f"RAG index update failed: {str(exc)}", 
                    extra={'user_id': user_id, 'content_type': content_type})
        
        return {
            'status': 'error',
            'error': str(exc)
        }


@shared_task
def cleanup_llm_cache():
    """
    Clean up old LLM cache and temporary files
    """
    try:
        logger.info("Starting LLM cache cleanup")
        
        # This would clean up temporary LLM files and cache
        # Implementation depends on your caching strategy
        
        logger.info("LLM cache cleanup completed")
        
    except Exception as exc:
        logger.error(f"LLM cache cleanup error: {str(exc)}")


@shared_task
def monitor_token_usage():
    """
    Monitor token usage and log metrics
    """
    try:
        logger.info("Monitoring token usage")
        
        # This would collect token usage metrics
        # Implementation depends on your monitoring setup
        
        logger.info("Token usage monitoring completed")
        
    except Exception as exc:
        logger.error(f"Token usage monitoring error: {str(exc)}")


@shared_task
def generate_conversation_summary(session_id: str, user_id: int) -> Dict[str, Any]:
    """
    Generate summary of conversation session
    
    Args:
        session_id: Session ID
        user_id: ID of user
        
    Returns:
        Dict with conversation summary
    """
    try:
        logger.info(f"Generating conversation summary for session {session_id}", 
                   extra={'user_id': user_id, 'session_id': session_id})
        
        # Get user
        user = User.objects.get(id=user_id)
        
        # Initialize services
        llm_processor = LLMProcessor()
        
        # Generate summary
        summary = llm_processor.generate_conversation_summary(
            session_id=session_id,
            user=user
        )
        
        logger.info(f"Conversation summary generated", 
                   extra={'user_id': user_id, 'session_id': session_id})
        
        return {
            'status': 'success',
            'summary': summary
        }
        
    except Exception as exc:
        logger.error(f"Conversation summary generation failed: {str(exc)}", 
                    extra={'user_id': user_id, 'session_id': session_id})
        
        return {
            'status': 'error',
            'error': str(exc)
        }
