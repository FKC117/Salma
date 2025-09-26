"""
Sandbox Execution Celery Tasks
Handles background code execution in secure sandbox environment
"""

from celery import shared_task
from django.conf import settings
import logging
from typing import Dict, Any, Optional
import time
import tempfile
import os
import subprocess
import signal
from pathlib import Path

from analytics.models import User
from analytics.services.sandbox_executor import SandboxExecutor
from analytics.services.audit_trail_manager import AuditTrailManager
from analytics.services.logging_service import StructuredLogger

logger = StructuredLogger(__name__)


@shared_task(bind=True, max_retries=1, default_retry_delay=60)
def execute_sandbox_code(self, code: str, user_id: int, language: str = 'python', timeout: int = 30) -> Dict[str, Any]:
    """
    Execute code in secure sandbox environment
    
    Args:
        code: Code to execute
        user_id: ID of user
        language: Programming language (python, r, sql)
        timeout: Execution timeout in seconds
        
    Returns:
        Dict with execution results
    """
    try:
        logger.info(f"Executing sandbox code for user {user_id}", 
                   extra={'user_id': user_id, 'language': language, 'code_length': len(code)})
        
        # Get user
        user = User.objects.get(id=user_id)
        
        # Initialize services
        sandbox_executor = SandboxExecutor()
        audit_manager = AuditTrailManager()
        
        # Execute code
        start_time = time.time()
        
        result = sandbox_executor.execute_code(
            code=code,
            user=user,
            language=language,
            timeout=timeout
        )
        
        execution_time = time.time() - start_time
        
        # Log audit trail
        audit_manager.log_action(
            user=user,
            action='sandbox_code_executed',
            details={
                'language': language,
                'execution_time': execution_time,
                'code_length': len(code),
                'success': result.get('success', False),
                'output_length': len(result.get('output', '')),
                'error': result.get('error', '')
            }
        )
        
        logger.info(f"Sandbox code execution completed", 
                   extra={'user_id': user_id, 'execution_time': execution_time, 'success': result.get('success', False)})
        
        return {
            'status': 'success',
            'result': result,
            'execution_time': execution_time
        }
        
    except Exception as exc:
        logger.error(f"Sandbox code execution failed: {str(exc)}", 
                    extra={'user_id': user_id, 'language': language})
        
        # Log audit trail for failure
        try:
            user = User.objects.get(id=user_id)
            audit_manager.log_action(
                user=user,
                action='sandbox_execution_failed',
                details={
                    'language': language,
                    'error': str(exc),
                    'retry_count': self.request.retries
                }
            )
        except:
            pass
        
        # Retry if not max retries reached
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying sandbox execution (attempt {self.request.retries + 1})")
            raise self.retry(countdown=60 * (self.request.retries + 1))
        
        return {
            'status': 'error',
            'error': str(exc),
            'message': 'Sandbox code execution failed after maximum retries'
        }


@shared_task(bind=True, max_retries=1)
def execute_data_analysis_code(self, code: str, dataset_id: int, user_id: int) -> Dict[str, Any]:
    """
    Execute data analysis code with dataset context
    
    Args:
        code: Analysis code to execute
        dataset_id: ID of dataset
        user_id: ID of user
        
    Returns:
        Dict with execution results
    """
    try:
        logger.info(f"Executing data analysis code for user {user_id}", 
                   extra={'user_id': user_id, 'dataset_id': dataset_id, 'code_length': len(code)})
        
        # Get user
        user = User.objects.get(id=user_id)
        
        # Initialize services
        sandbox_executor = SandboxExecutor()
        
        # Execute analysis code
        result = sandbox_executor.execute_data_analysis(
            code=code,
            dataset_id=dataset_id,
            user=user
        )
        
        logger.info(f"Data analysis code execution completed", 
                   extra={'user_id': user_id, 'dataset_id': dataset_id, 'success': result.get('success', False)})
        
        return {
            'status': 'success',
            'result': result
        }
        
    except Exception as exc:
        logger.error(f"Data analysis code execution failed: {str(exc)}", 
                    extra={'user_id': user_id, 'dataset_id': dataset_id})
        
        return {
            'status': 'error',
            'error': str(exc),
            'message': 'Data analysis code execution failed'
        }


@shared_task(bind=True, max_retries=1)
def execute_visualization_code(self, code: str, dataset_id: int, user_id: int) -> Dict[str, Any]:
    """
    Execute visualization code
    
    Args:
        code: Visualization code to execute
        dataset_id: ID of dataset
        user_id: ID of user
        
    Returns:
        Dict with execution results
    """
    try:
        logger.info(f"Executing visualization code for user {user_id}", 
                   extra={'user_id': user_id, 'dataset_id': dataset_id, 'code_length': len(code)})
        
        # Get user
        user = User.objects.get(id=user_id)
        
        # Initialize services
        sandbox_executor = SandboxExecutor()
        
        # Execute visualization code
        result = sandbox_executor.execute_visualization(
            code=code,
            dataset_id=dataset_id,
            user=user
        )
        
        logger.info(f"Visualization code execution completed", 
                   extra={'user_id': user_id, 'dataset_id': dataset_id, 'success': result.get('success', False)})
        
        return {
            'status': 'success',
            'result': result
        }
        
    except Exception as exc:
        logger.error(f"Visualization code execution failed: {str(exc)}", 
                    extra={'user_id': user_id, 'dataset_id': dataset_id})
        
        return {
            'status': 'error',
            'error': str(exc),
            'message': 'Visualization code execution failed'
        }


@shared_task
def validate_code_safety(code: str, user_id: int, language: str = 'python') -> Dict[str, Any]:
    """
    Validate code for safety and security
    
    Args:
        code: Code to validate
        user_id: ID of user
        language: Programming language
        
    Returns:
        Dict with validation results
    """
    try:
        logger.info(f"Validating code safety for user {user_id}", 
                   extra={'user_id': user_id, 'language': language, 'code_length': len(code)})
        
        # Get user
        user = User.objects.get(id=user_id)
        
        # Initialize services
        sandbox_executor = SandboxExecutor()
        
        # Validate code
        validation_result = sandbox_executor.validate_code_safety(
            code=code,
            user=user,
            language=language
        )
        
        logger.info(f"Code safety validation completed", 
                   extra={'user_id': user_id, 'safe': validation_result.get('safe', False)})
        
        return {
            'status': 'success',
            'validation': validation_result
        }
        
    except Exception as exc:
        logger.error(f"Code safety validation failed: {str(exc)}", 
                    extra={'user_id': user_id, 'language': language})
        
        return {
            'status': 'error',
            'error': str(exc),
            'message': 'Code safety validation failed'
        }


@shared_task
def cleanup_sandbox_environment():
    """
    Clean up sandbox environment and temporary files
    """
    try:
        logger.info("Starting sandbox environment cleanup")
        
        # This would clean up sandbox temporary files
        # Implementation depends on your sandbox setup
        
        logger.info("Sandbox environment cleanup completed")
        
    except Exception as exc:
        logger.error(f"Sandbox environment cleanup error: {str(exc)}")


@shared_task
def monitor_sandbox_resources():
    """
    Monitor sandbox resource usage
    """
    try:
        logger.info("Monitoring sandbox resources")
        
        # This would monitor sandbox resource usage
        # Implementation depends on your monitoring setup
        
        logger.info("Sandbox resource monitoring completed")
        
    except Exception as exc:
        logger.error(f"Sandbox resource monitoring error: {str(exc)}")


@shared_task
def execute_batch_code(code_blocks: list, user_id: int, language: str = 'python') -> Dict[str, Any]:
    """
    Execute multiple code blocks in batch
    
    Args:
        code_blocks: List of code blocks [{'code': str, 'name': str}]
        user_id: ID of user
        language: Programming language
        
    Returns:
        Dict with batch execution results
    """
    try:
        logger.info(f"Executing batch code for user {user_id}", 
                   extra={'user_id': user_id, 'language': language, 'block_count': len(code_blocks)})
        
        # Get user
        user = User.objects.get(id=user_id)
        
        # Initialize services
        sandbox_executor = SandboxExecutor()
        
        # Execute code blocks
        results = []
        for i, block in enumerate(code_blocks):
            code = block['code']
            name = block.get('name', f'Block {i+1}')
            
            logger.info(f"Executing code block {i+1}/{len(code_blocks)}: {name}")
            
            result = sandbox_executor.execute_code(
                code=code,
                user=user,
                language=language
            )
            
            results.append({
                'name': name,
                'code': code,
                'result': result
            })
        
        logger.info(f"Batch code execution completed", 
                   extra={'user_id': user_id, 'executed_count': len(results)})
        
        return {
            'status': 'success',
            'results': results,
            'executed_count': len(results)
        }
        
    except Exception as exc:
        logger.error(f"Batch code execution failed: {str(exc)}", 
                    extra={'user_id': user_id, 'block_count': len(code_blocks)})
        
        return {
            'status': 'error',
            'error': str(exc),
            'message': 'Batch code execution failed'
        }


@shared_task
def generate_code_snippet(tool_name: str, parameters: Dict[str, Any], user_id: int) -> Dict[str, Any]:
    """
    Generate code snippet for analysis tool
    
    Args:
        tool_name: Name of analysis tool
        parameters: Tool parameters
        user_id: ID of user
        
    Returns:
        Dict with generated code snippet
    """
    try:
        logger.info(f"Generating code snippet for tool {tool_name}", 
                   extra={'user_id': user_id, 'tool_name': tool_name})
        
        # Get user
        user = User.objects.get(id=user_id)
        
        # Initialize services
        sandbox_executor = SandboxExecutor()
        
        # Generate code snippet
        snippet = sandbox_executor.generate_code_snippet(
            tool_name=tool_name,
            parameters=parameters,
            user=user
        )
        
        logger.info(f"Code snippet generated", 
                   extra={'user_id': user_id, 'tool_name': tool_name, 'snippet_length': len(snippet.get('code', ''))})
        
        return {
            'status': 'success',
            'snippet': snippet
        }
        
    except Exception as exc:
        logger.error(f"Code snippet generation failed: {str(exc)}", 
                    extra={'user_id': user_id, 'tool_name': tool_name})
        
        return {
            'status': 'error',
            'error': str(exc),
            'message': 'Code snippet generation failed'
        }
