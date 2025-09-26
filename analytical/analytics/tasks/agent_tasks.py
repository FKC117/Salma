"""
Agent Execution Celery Tasks
Handles background agentic AI operations and autonomous analysis
"""

from celery import shared_task
from django.conf import settings
import json
import logging
from typing import Dict, Any, Optional, List
import time
import asyncio

from analytics.models import Dataset, User
from analytics.services.agentic_ai_controller import AgenticAIController
from analytics.services.analysis_executor import AnalysisExecutor
from analytics.services.llm_processor import LLMProcessor
from analytics.services.audit_trail_manager import AuditTrailManager
from analytics.services.logging_service import StructuredLogger
from analytics.tools.tool_registry import ToolRegistry

logger = StructuredLogger(__name__)


@shared_task(bind=True, max_retries=1, default_retry_delay=60)
def execute_agent_run(self, dataset_id: int, objective: str, user_id: int, max_steps: int = 10) -> Dict[str, Any]:
    """
    Execute agentic AI run in background
    
    Args:
        dataset_id: ID of dataset to analyze
        objective: Analysis objective
        user_id: ID of user
        max_steps: Maximum number of steps
        
    Returns:
        Dict with agent execution results
    """
    try:
        logger.info(f"Starting agent run for dataset {dataset_id}", 
                   extra={'user_id': user_id, 'dataset_id': dataset_id, 'objective': objective})
        
        # Get dataset and user
        dataset = Dataset.objects.get(id=dataset_id)
        user = User.objects.get(id=user_id)
        
        # Initialize services
        agent_controller = AgenticAIController()
        audit_manager = AuditTrailManager()
        
        # Execute agent run
        start_time = time.time()
        
        result = agent_controller.run_agent(
            dataset=dataset,
            objective=objective,
            user=user,
            max_steps=max_steps
        )
        
        execution_time = time.time() - start_time
        
        # Log audit trail
        audit_manager.log_action(
            user=user,
            action='agent_run_executed',
            details={
                'dataset_id': dataset_id,
                'objective': objective,
                'max_steps': max_steps,
                'steps_executed': result.get('steps_executed', 0),
                'execution_time': execution_time,
                'status': result.get('status', 'unknown')
            }
        )
        
        logger.info(f"Agent run completed", 
                   extra={'user_id': user_id, 'dataset_id': dataset_id, 'execution_time': execution_time})
        
        return {
            'status': 'success',
            'result': result,
            'execution_time': execution_time
        }
        
    except Exception as exc:
        logger.error(f"Agent run failed: {str(exc)}", 
                    extra={'user_id': user_id, 'dataset_id': dataset_id})
        
        # Log audit trail for failure
        try:
            user = User.objects.get(id=user_id)
            audit_manager.log_action(
                user=user,
                action='agent_run_failed',
                details={
                    'dataset_id': dataset_id,
                    'objective': objective,
                    'error': str(exc),
                    'retry_count': self.request.retries
                }
            )
        except:
            pass
        
        # Retry if not max retries reached
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying agent run (attempt {self.request.retries + 1})")
            raise self.retry(countdown=60 * (self.request.retries + 1))
        
        return {
            'status': 'error',
            'error': str(exc),
            'message': 'Agent run failed after maximum retries'
        }


@shared_task(bind=True, max_retries=1)
def execute_agent_step(self, agent_state: Dict[str, Any], user_id: int) -> Dict[str, Any]:
    """
    Execute single agent step
    
    Args:
        agent_state: Current agent state
        user_id: ID of user
        
    Returns:
        Dict with step results
    """
    try:
        logger.info(f"Executing agent step", 
                   extra={'user_id': user_id, 'step': agent_state.get('current_step', 0)})
        
        # Get user
        user = User.objects.get(id=user_id)
        
        # Initialize services
        agent_controller = AgenticAIController()
        
        # Execute step
        result = agent_controller.execute_step(
            agent_state=agent_state,
            user=user
        )
        
        logger.info(f"Agent step completed", 
                   extra={'user_id': user_id, 'step': agent_state.get('current_step', 0)})
        
        return {
            'status': 'success',
            'result': result
        }
        
    except Exception as exc:
        logger.error(f"Agent step failed: {str(exc)}", 
                    extra={'user_id': user_id})
        
        return {
            'status': 'error',
            'error': str(exc),
            'message': 'Agent step failed'
        }


@shared_task(bind=True, max_retries=1)
def generate_agent_plan(self, dataset_id: int, objective: str, user_id: int) -> Dict[str, Any]:
    """
    Generate agent execution plan
    
    Args:
        dataset_id: ID of dataset
        objective: Analysis objective
        user_id: ID of user
        
    Returns:
        Dict with execution plan
    """
    try:
        logger.info(f"Generating agent plan for dataset {dataset_id}", 
                   extra={'user_id': user_id, 'dataset_id': dataset_id, 'objective': objective})
        
        # Get dataset and user
        dataset = Dataset.objects.get(id=dataset_id)
        user = User.objects.get(id=user_id)
        
        # Initialize services
        agent_controller = AgenticAIController()
        llm_processor = LLMProcessor()
        
        # Generate plan
        plan = agent_controller.generate_execution_plan(
            dataset=dataset,
            objective=objective,
            user=user
        )
        
        logger.info(f"Agent plan generated", 
                   extra={'user_id': user_id, 'dataset_id': dataset_id, 'plan_steps': len(plan.get('steps', []))})
        
        return {
            'status': 'success',
            'plan': plan
        }
        
    except Exception as exc:
        logger.error(f"Agent plan generation failed: {str(exc)}", 
                    extra={'user_id': user_id, 'dataset_id': dataset_id})
        
        return {
            'status': 'error',
            'error': str(exc),
            'message': 'Agent plan generation failed'
        }


@shared_task(bind=True, max_retries=1)
def execute_autonomous_analysis(self, dataset_id: int, user_id: int, analysis_type: str = 'comprehensive') -> Dict[str, Any]:
    """
    Execute autonomous analysis without user guidance
    
    Args:
        dataset_id: ID of dataset
        user_id: ID of user
        analysis_type: Type of analysis (comprehensive, quick, deep)
        
    Returns:
        Dict with analysis results
    """
    try:
        logger.info(f"Starting autonomous analysis for dataset {dataset_id}", 
                   extra={'user_id': user_id, 'dataset_id': dataset_id, 'analysis_type': analysis_type})
        
        # Get dataset and user
        dataset = Dataset.objects.get(id=dataset_id)
        user = User.objects.get(id=user_id)
        
        # Initialize services
        agent_controller = AgenticAIController()
        audit_manager = AuditTrailManager()
        
        # Define analysis objectives based on type
        objectives = {
            'comprehensive': 'Perform comprehensive data analysis including descriptive statistics, correlations, and visualizations',
            'quick': 'Perform quick data overview with basic statistics and key insights',
            'deep': 'Perform deep analysis with advanced statistical methods and machine learning'
        }
        
        objective = objectives.get(analysis_type, objectives['comprehensive'])
        
        # Execute autonomous analysis
        start_time = time.time()
        
        result = agent_controller.run_autonomous_analysis(
            dataset=dataset,
            objective=objective,
            user=user,
            analysis_type=analysis_type
        )
        
        execution_time = time.time() - start_time
        
        # Log audit trail
        audit_manager.log_action(
            user=user,
            action='autonomous_analysis_executed',
            details={
                'dataset_id': dataset_id,
                'analysis_type': analysis_type,
                'execution_time': execution_time,
                'tools_used': result.get('tools_used', []),
                'insights_generated': len(result.get('insights', []))
            }
        )
        
        logger.info(f"Autonomous analysis completed", 
                   extra={'user_id': user_id, 'dataset_id': dataset_id, 'execution_time': execution_time})
        
        return {
            'status': 'success',
            'result': result,
            'execution_time': execution_time
        }
        
    except Exception as exc:
        logger.error(f"Autonomous analysis failed: {str(exc)}", 
                    extra={'user_id': user_id, 'dataset_id': dataset_id})
        
        # Log audit trail for failure
        try:
            user = User.objects.get(id=user_id)
            audit_manager.log_action(
                user=user,
                action='autonomous_analysis_failed',
                details={
                    'dataset_id': dataset_id,
                    'analysis_type': analysis_type,
                    'error': str(exc)
                }
            )
        except:
            pass
        
        return {
            'status': 'error',
            'error': str(exc),
            'message': 'Autonomous analysis failed'
        }


@shared_task
def monitor_agent_performance():
    """
    Monitor agent performance and log metrics
    """
    try:
        logger.info("Monitoring agent performance")
        
        # This would collect agent performance metrics
        # Implementation depends on your monitoring setup
        
        logger.info("Agent performance monitoring completed")
        
    except Exception as exc:
        logger.error(f"Agent performance monitoring error: {str(exc)}")


@shared_task
def cleanup_agent_sessions():
    """
    Clean up old agent sessions and temporary data
    """
    try:
        logger.info("Starting agent session cleanup")
        
        # This would clean up old agent sessions
        # Implementation depends on your session management
        
        logger.info("Agent session cleanup completed")
        
    except Exception as exc:
        logger.error(f"Agent session cleanup error: {str(exc)}")


@shared_task
def generate_agent_report(agent_run_id: str, user_id: int) -> Dict[str, Any]:
    """
    Generate comprehensive agent execution report
    
    Args:
        agent_run_id: ID of agent run
        user_id: ID of user
        
    Returns:
        Dict with agent report
    """
    try:
        logger.info(f"Generating agent report for run {agent_run_id}", 
                   extra={'user_id': user_id, 'agent_run_id': agent_run_id})
        
        # Get user
        user = User.objects.get(id=user_id)
        
        # Initialize services
        agent_controller = AgenticAIController()
        
        # Generate report
        report = agent_controller.generate_execution_report(
            agent_run_id=agent_run_id,
            user=user
        )
        
        logger.info(f"Agent report generated", 
                   extra={'user_id': user_id, 'agent_run_id': agent_run_id})
        
        return {
            'status': 'success',
            'report': report
        }
        
    except Exception as exc:
        logger.error(f"Agent report generation failed: {str(exc)}", 
                    extra={'user_id': user_id, 'agent_run_id': agent_run_id})
        
        return {
            'status': 'error',
            'error': str(exc)
        }
