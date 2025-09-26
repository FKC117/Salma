"""
Agentic AI Controller for Autonomous Analysis

This service orchestrates autonomous AI agent workflows for end-to-end data analysis,
including planning, execution, monitoring, and human feedback integration.
"""

import json
import logging
import time
import uuid
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
from django.db import transaction
from django.core.cache import cache
from django.contrib.auth import get_user_model

from analytics.models import (
    AgentRun, AgentStep, Dataset, AnalysisTool, AnalysisResult,
    AnalysisSession, User, AuditTrail
)
from analytics.services.audit_trail_manager import AuditTrailManager
from analytics.services.llm_processor import LLMProcessor
from analytics.services.analysis_executor import AnalysisExecutor
from analytics.services.session_manager import SessionManager
from analytics.services.rag_service import RAGService

logger = logging.getLogger(__name__)
User = get_user_model()


class AgenticAIController:
    """
    Service for orchestrating autonomous AI agent workflows
    """
    
    def __init__(self):
        self.audit_manager = AuditTrailManager()
        self.llm_processor = LLMProcessor()
        self.analysis_executor = AnalysisExecutor()
        self.session_manager = SessionManager()
        self.rag_service = RAGService()
        
        # Agent configuration
        self.agent_version = getattr(settings, 'AGENT_VERSION', '1.0')
        self.max_steps = getattr(settings, 'AGENT_MAX_STEPS', 20)
        self.max_cost = getattr(settings, 'AGENT_MAX_COST', 10000)
        self.max_time = getattr(settings, 'AGENT_MAX_TIME', 1800)  # 30 minutes
        
        # Cache settings
        self.agent_cache_timeout = 3600  # 1 hour
        
    def start_agent_run(self, user: User, dataset: Dataset, goal: str,
                       constraints: Optional[Dict[str, Any]] = None,
                       agent_config: Optional[Dict[str, Any]] = None) -> AgentRun:
        """
        Start an autonomous AI agent analysis session
        
        Args:
            user: User starting the agent
            dataset: Dataset to analyze
            goal: Analysis goal or question
            constraints: Resource constraints (max_steps, max_cost, max_time)
            agent_config: Agent configuration options
            
        Returns:
            AgentRun object
        """
        correlation_id = str(uuid.uuid4())
        
        try:
            # Set up constraints
            max_steps = constraints.get('max_steps', self.max_steps) if constraints else self.max_steps
            max_cost = constraints.get('max_cost', self.max_cost) if constraints else self.max_cost
            max_time = constraints.get('max_time', self.max_time) if constraints else self.max_time
            
            # Create or get analysis session
            session = self._get_or_create_session(user, dataset)
            
            # Generate analysis plan
            plan = self._generate_analysis_plan(dataset, goal, user)
            
            # Create agent run
            with transaction.atomic():
                agent_run = AgentRun.objects.create(
                    user=user,
                    dataset=dataset,
                    session=session,
                    goal=goal,
                    plan_json=plan,
                    status='planning',
                    current_step=0,
                    total_steps=len(plan.get('steps', [])),
                    max_steps=max_steps,
                    max_cost=max_cost,
                    max_time=max_time,
                    total_cost=0,
                    total_time=0,
                    progress_percentage=0,
                    agent_version=self.agent_version,
                    llm_model=self.llm_processor.model_name,
                    started_at=timezone.now(),
                    correlation_id=correlation_id
                )
                
                # Cache agent run data
                self._cache_agent_run(agent_run)
                
                # Log audit trail
                self.audit_manager.log_user_action(
                    user_id=user.id,
                    action_type='start_agent',
                    resource_type='agent_run',
                    resource_id=agent_run.id,
                    resource_name=f"Agent Run: {goal}",
                    action_description=f"Started autonomous AI agent for goal: {goal}",
                    success=True,
                    correlation_id=correlation_id,
                    data_changed=True
                )
                
                logger.info(f"Started agent run {agent_run.id} for user {user.id}")
                
                # Start execution (async)
                self._execute_agent_run_async(agent_run.id)
                
                return agent_run
                
        except Exception as e:
            logger.error(f"Failed to start agent run: {str(e)}", exc_info=True)
            raise ValueError(f"Failed to start agent run: {str(e)}")
    
    def execute_agent_run(self, agent_run_id: int) -> bool:
        """
        Execute an agent run step by step
        
        Args:
            agent_run_id: ID of the agent run to execute
            
        Returns:
            True if execution completed successfully
        """
        try:
            agent_run = AgentRun.objects.get(id=agent_run_id)
            
            # Update status to running
            agent_run.status = 'running'
            agent_run.save(update_fields=['status'])
            
            # Execute each step in the plan
            plan = agent_run.plan_json
            steps = plan.get('steps', [])
            
            for step_index, step_config in enumerate(steps):
                if agent_run.status != 'running':
                    break
                
                # Check constraints
                if not self._check_constraints(agent_run):
                    agent_run.status = 'cancelled'
                    agent_run.error_message = "Resource constraints exceeded"
                    agent_run.save(update_fields=['status', 'error_message'])
                    break
                
                # Execute step
                step_result = self._execute_agent_step(agent_run, step_index, step_config)
                
                # Update agent run progress
                self._update_agent_progress(agent_run, step_index + 1, step_result)
                
                # Check if step failed critically
                if step_result.get('status') == 'failed' and step_result.get('critical', False):
                    agent_run.status = 'failed'
                    agent_run.error_message = step_result.get('error_message', 'Critical step failed')
                    agent_run.save(update_fields=['status', 'error_message'])
                    break
            
            # Mark as completed if all steps executed successfully
            if agent_run.status == 'running':
                agent_run.status = 'completed'
                agent_run.finished_at = timezone.now()
                agent_run.progress_percentage = 100
                agent_run.save(update_fields=['status', 'finished_at', 'progress_percentage'])
                
                # Log completion
                self.audit_manager.log_user_action(
                    user_id=agent_run.user.id,
                    action_type='complete_agent',
                    resource_type='agent_run',
                    resource_id=agent_run.id,
                    resource_name=f"Agent Run: {agent_run.goal}",
                    action_description="Agent run completed successfully",
                    success=True,
                    data_changed=True
                )
            
            logger.info(f"Agent run {agent_run_id} execution completed with status: {agent_run.status}")
            return True
            
        except AgentRun.DoesNotExist:
            logger.error(f"Agent run {agent_run_id} not found")
            return False
        except Exception as e:
            logger.error(f"Agent run execution failed: {str(e)}", exc_info=True)
            
            # Update agent run status
            try:
                agent_run = AgentRun.objects.get(id=agent_run_id)
                agent_run.status = 'failed'
                agent_run.error_message = str(e)
                agent_run.finished_at = timezone.now()
                agent_run.save(update_fields=['status', 'error_message', 'finished_at'])
            except:
                pass
            
            return False
    
    def pause_agent_run(self, agent_run_id: int, user: User) -> bool:
        """Pause an active agent run"""
        try:
            agent_run = AgentRun.objects.get(id=agent_run_id, user=user)
            
            if agent_run.status == 'running':
                agent_run.status = 'paused'
                agent_run.save(update_fields=['status'])
                
                # Log pause action
                self.audit_manager.log_user_action(
                    user_id=user.id,
                    action_type='pause_agent',
                    resource_type='agent_run',
                    resource_id=agent_run.id,
                    resource_name=f"Agent Run: {agent_run.goal}",
                    action_description="Agent run paused by user",
                    success=True
                )
                
                logger.info(f"Agent run {agent_run_id} paused by user {user.id}")
                return True
            
            return False
            
        except AgentRun.DoesNotExist:
            return False
        except Exception as e:
            logger.error(f"Failed to pause agent run: {str(e)}")
            return False
    
    def resume_agent_run(self, agent_run_id: int, user: User) -> bool:
        """Resume a paused agent run"""
        try:
            agent_run = AgentRun.objects.get(id=agent_run_id, user=user)
            
            if agent_run.status == 'paused':
                agent_run.status = 'running'
                agent_run.save(update_fields=['status'])
                
                # Log resume action
                self.audit_manager.log_user_action(
                    user_id=user.id,
                    action_type='resume_agent',
                    resource_type='agent_run',
                    resource_id=agent_run.id,
                    resource_name=f"Agent Run: {agent_run.goal}",
                    action_description="Agent run resumed by user",
                    success=True
                )
                
                logger.info(f"Agent run {agent_run_id} resumed by user {user.id}")
                
                # Continue execution
                self._execute_agent_run_async(agent_run_id)
                return True
            
            return False
            
        except AgentRun.DoesNotExist:
            return False
        except Exception as e:
            logger.error(f"Failed to resume agent run: {str(e)}")
            return False
    
    def cancel_agent_run(self, agent_run_id: int, user: User) -> bool:
        """Cancel an active or paused agent run"""
        try:
            agent_run = AgentRun.objects.get(id=agent_run_id, user=user)
            
            if agent_run.status in ['running', 'paused']:
                agent_run.status = 'cancelled'
                agent_run.finished_at = timezone.now()
                agent_run.save(update_fields=['status', 'finished_at'])
                
                # Log cancel action
                self.audit_manager.log_user_action(
                    user_id=user.id,
                    action_type='cancel_agent',
                    resource_type='agent_run',
                    resource_id=agent_run.id,
                    resource_name=f"Agent Run: {agent_run.goal}",
                    action_description="Agent run cancelled by user",
                    success=True
                )
                
                logger.info(f"Agent run {agent_run_id} cancelled by user {user.id}")
                return True
            
            return False
            
        except AgentRun.DoesNotExist:
            return False
        except Exception as e:
            logger.error(f"Failed to cancel agent run: {str(e)}")
            return False
    
    def provide_human_feedback(self, agent_run_id: int, user: User, 
                             feedback: str, step_number: Optional[int] = None) -> bool:
        """Provide human feedback to an agent run"""
        try:
            agent_run = AgentRun.objects.get(id=agent_run_id, user=user)
            
            # Create feedback step
            feedback_step = AgentStep.objects.create(
                agent_run=agent_run,
                step_number=step_number or agent_run.current_step,
                thought="Human feedback received",
                tool_name="human_feedback",
                parameters_json={'feedback': feedback},
                observation_json={'feedback_type': 'human_input'},
                status='completed',
                token_usage=0,
                execution_time_ms=0,
                confidence_score=1.0,
                reasoning="Human feedback incorporated",
                started_at=timezone.now(),
                finished_at=timezone.now()
            )
            
            # Update agent run with feedback
            agent_data = agent_run.plan_json or {}
            feedback_history = agent_data.get('human_feedback', [])
            feedback_history.append({
                'step_number': step_number or agent_run.current_step,
                'feedback': feedback,
                'timestamp': timezone.now().isoformat()
            })
            agent_data['human_feedback'] = feedback_history
            agent_run.plan_json = agent_data
            agent_run.save(update_fields=['plan_json'])
            
            # Log feedback
            self.audit_manager.log_user_action(
                user_id=user.id,
                action_type='provide_feedback',
                resource_type='agent_run',
                resource_id=agent_run.id,
                resource_name=f"Agent Run: {agent_run.goal}",
                action_description=f"Provided human feedback: {feedback[:100]}...",
                success=True
            )
            
            logger.info(f"Human feedback provided for agent run {agent_run_id}")
            return True
            
        except AgentRun.DoesNotExist:
            return False
        except Exception as e:
            logger.error(f"Failed to provide human feedback: {str(e)}")
            return False
    
    def get_agent_run_status(self, agent_run_id: int, user: User) -> Optional[Dict[str, Any]]:
        """Get detailed status of an agent run"""
        try:
            agent_run = AgentRun.objects.get(id=agent_run_id, user=user)
            
            # Get recent steps
            recent_steps = AgentStep.objects.filter(
                agent_run=agent_run
            ).order_by('-step_number')[:5]
            
            # Calculate time remaining
            time_remaining = None
            if agent_run.status == 'running' and agent_run.max_time:
                elapsed = (timezone.now() - agent_run.started_at).total_seconds()
                time_remaining = max(0, agent_run.max_time - elapsed)
            
            return {
                'agent_run': {
                    'id': agent_run.id,
                    'goal': agent_run.goal,
                    'status': agent_run.status,
                    'current_step': agent_run.current_step,
                    'total_steps': agent_run.total_steps,
                    'progress_percentage': agent_run.progress_percentage,
                    'total_cost': agent_run.total_cost,
                    'total_time': agent_run.total_time,
                    'started_at': agent_run.started_at.isoformat(),
                    'finished_at': agent_run.finished_at.isoformat() if agent_run.finished_at else None,
                    'error_message': agent_run.error_message
                },
                'recent_steps': [
                    {
                        'step_number': step.step_number,
                        'tool_name': step.tool_name,
                        'status': step.status,
                        'confidence_score': step.confidence_score,
                        'reasoning': step.reasoning,
                        'execution_time_ms': step.execution_time_ms
                    }
                    for step in recent_steps
                ],
                'constraints': {
                    'max_steps': agent_run.max_steps,
                    'max_cost': agent_run.max_cost,
                    'max_time': agent_run.max_time,
                    'time_remaining': time_remaining
                },
                'next_action': self._get_next_action(agent_run)
            }
            
        except AgentRun.DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Failed to get agent run status: {str(e)}")
            return None
    
    def list_agent_runs(self, user: User, status: Optional[str] = None, 
                       limit: int = 20) -> List[AgentRun]:
        """List agent runs for a user"""
        try:
            queryset = AgentRun.objects.filter(user=user)
            
            if status:
                queryset = queryset.filter(status=status)
            
            return queryset.order_by('-created_at')[:limit]
            
        except Exception as e:
            logger.error(f"Failed to list agent runs: {str(e)}")
            return []
    
    def _get_or_create_session(self, user: User, dataset: Dataset) -> AnalysisSession:
        """Get or create analysis session for agent run"""
        try:
            # Try to find existing active session
            session = AnalysisSession.objects.filter(
                user=user,
                primary_dataset=dataset,
                is_active=True
            ).first()
            
            if session:
                return session
            
            # Create new session
            return self.session_manager.create_session(
                user=user,
                dataset=dataset,
                session_name=f"Agent Session - {dataset.name}",
                description=f"Autonomous analysis session for {dataset.name}"
            )
            
        except Exception as e:
            logger.error(f"Failed to get or create session: {str(e)}")
            raise
    
    def _generate_analysis_plan(self, dataset: Dataset, goal: str, user: User) -> Dict[str, Any]:
        """Generate analysis plan using LLM with RAG context"""
        try:
            dataset_info = {
                'name': dataset.name,
                'row_count': dataset.row_count,
                'column_count': dataset.column_count,
                'column_types': {col.name: col.confirmed_type for col in dataset.columns.all()}
            }
            
            # RAG Retrieval: Get relevant context for planning
            rag_context = self._get_rag_context_for_planning(dataset, goal, user)
            
            plan = self.llm_processor.generate_analysis_plan(dataset_info, goal, user, rag_context)
            return plan
            
        except Exception as e:
            logger.error(f"Failed to generate analysis plan: {str(e)}")
            # Return fallback plan
            return {
                'plan_name': 'Basic Analysis Plan',
                'steps': [
                    {
                        'step_number': 1,
                        'tool_name': 'descriptive_statistics',
                        'description': 'Generate basic descriptive statistics',
                        'parameters': {},
                        'expected_output': 'Summary statistics for all columns'
                    }
                ],
                'estimated_duration': '15 minutes',
                'complexity': 'low',
                'confidence': 0.5
            }
    
    def _execute_agent_step(self, agent_run: AgentRun, step_index: int, 
                           step_config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single agent step"""
        try:
            step_number = step_index + 1
            tool_name = step_config.get('tool_name')
            parameters = step_config.get('parameters', {})
            
            # Create step record
            step = AgentStep.objects.create(
                agent_run=agent_run,
                step_number=step_number,
                thought=step_config.get('description', ''),
                tool_name=tool_name,
                parameters_json=parameters,
                status='running',
                started_at=timezone.now()
            )
            
            # Execute the step
            if tool_name == 'human_feedback':
                # Handle human feedback
                step.status = 'completed'
                step.observation_json = {'feedback': 'Human feedback processed'}
                step.confidence_score = 1.0
                
            elif tool_name in ['descriptive_statistics', 'correlation_analysis', 'regression_analysis']:
                # RAG Retrieval: Get relevant context for execution
                execution_context = self._get_rag_context_for_execution(
                    agent_run, step_config, tool_name, parameters
                )
                
                # Execute analysis tool with context
                result = self.analysis_executor.execute_analysis(
                    tool_name=tool_name,
                    parameters=parameters,
                    session=agent_run.session,
                    user=agent_run.user
                )
                
                step.status = 'completed'
                step.observation_json = {
                    'result_id': result['analysis_id'],
                    'output_type': result['result_data'].get('output_type'),
                    'execution_time': result['execution_time']
                }
                step.confidence_score = 0.8
                
            else:
                # Unknown tool
                step.status = 'failed'
                step.observation_json = {'error': f'Unknown tool: {tool_name}'}
                step.confidence_score = 0.0
            
            # Update step
            step.finished_at = timezone.now()
            step.execution_time_ms = int((step.finished_at - step.started_at).total_seconds() * 1000)
            step.save()
            
            return {
                'status': step.status,
                'confidence_score': step.confidence_score,
                'execution_time_ms': step.execution_time_ms,
                'observation': step.observation_json
            }
            
        except Exception as e:
            logger.error(f"Agent step execution failed: {str(e)}")
            return {
                'status': 'failed',
                'error_message': str(e),
                'critical': True
            }
    
    def _update_agent_progress(self, agent_run: AgentRun, current_step: int, 
                              step_result: Dict[str, Any]) -> None:
        """Update agent run progress"""
        try:
            agent_run.current_step = current_step
            agent_run.progress_percentage = (current_step / agent_run.total_steps) * 100
            
            # Update costs and time
            if step_result.get('token_usage'):
                agent_run.total_cost += step_result['token_usage']
            
            if step_result.get('execution_time_ms'):
                agent_run.total_time += step_result['execution_time_ms'] / 1000
            
            agent_run.save(update_fields=[
                'current_step', 'progress_percentage', 'total_cost', 'total_time'
            ])
            
        except Exception as e:
            logger.error(f"Failed to update agent progress: {str(e)}")
    
    def _check_constraints(self, agent_run: AgentRun) -> bool:
        """Check if agent run is within resource constraints"""
        try:
            # Check step limit
            if agent_run.current_step >= agent_run.max_steps:
                return False
            
            # Check cost limit
            if agent_run.total_cost >= agent_run.max_cost:
                return False
            
            # Check time limit
            if agent_run.max_time:
                elapsed = (timezone.now() - agent_run.started_at).total_seconds()
                if elapsed >= agent_run.max_time:
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to check constraints: {str(e)}")
            return True  # Allow continuation if check fails
    
    def _get_next_action(self, agent_run: AgentRun) -> str:
        """Get description of next action for agent run"""
        try:
            if agent_run.status != 'running':
                return "Agent is not running"
            
            plan = agent_run.plan_json or {}
            steps = plan.get('steps', [])
            
            if agent_run.current_step < len(steps):
                next_step = steps[agent_run.current_step]
                return f"Next: {next_step.get('description', 'Execute next step')}"
            else:
                return "All steps completed"
                
        except Exception as e:
            logger.error(f"Failed to get next action: {str(e)}")
            return "Unknown"
    
    def _cache_agent_run(self, agent_run: AgentRun) -> None:
        """Cache agent run data for quick access"""
        try:
            cache_key = f"agent_run_{agent_run.id}"
            cache_data = {
                'id': agent_run.id,
                'goal': agent_run.goal,
                'status': agent_run.status,
                'progress_percentage': agent_run.progress_percentage,
                'current_step': agent_run.current_step,
                'total_steps': agent_run.total_steps
            }
            cache.set(cache_key, cache_data, self.agent_cache_timeout)
        except Exception as e:
            logger.warning(f"Failed to cache agent run: {str(e)}")
    
    def _execute_agent_run_async(self, agent_run_id: int) -> None:
        """Execute agent run asynchronously (placeholder for Celery integration)"""
        try:
            # For now, execute synchronously
            # In production, this would be a Celery task
            self.execute_agent_run(agent_run_id)
        except Exception as e:
            logger.error(f"Async agent execution failed: {str(e)}")
    
    def _get_rag_context_for_planning(self, dataset: Dataset, goal: str, user: User) -> str:
        """
        Retrieve relevant RAG context for analysis planning
        
        Args:
            dataset: Dataset to analyze
            goal: Analysis goal
            user: User requesting the analysis
            
        Returns:
            Formatted context string for LLM planning
        """
        try:
            # Search for relevant vector notes
            search_queries = [
                f"dataset {dataset.name} analysis",
                f"analysis plan {goal}",
                f"statistical analysis {dataset.name}",
                f"data exploration {goal}",
                f"visualization {dataset.name}"
            ]
            
            context_parts = []
            
            for query in search_queries:
                # Search for dataset-scoped notes
                dataset_results = self.rag_service.search_vectors(
                    query=query,
                    user=user,
                    dataset=dataset,
                    top_k=3,
                    similarity_threshold=0.7
                )
                
                # Search for global notes
                global_results = self.rag_service.search_vectors(
                    query=query,
                    user=user,
                    dataset=None,
                    top_k=2,
                    similarity_threshold=0.7
                )
                
                # Combine and format results
                for result in dataset_results + global_results:
                    context_parts.append(f"""
                    Relevant Context:
                    Title: {result.get('title', 'Unknown')}
                    Content: {result.get('text', '')[:300]}...
                    Confidence: {result.get('confidence_score', 0)}
                    """)
            
            # Add dataset-specific context
            dataset_context = f"""
            Dataset Context:
            Name: {dataset.name}
            Description: {dataset.description or 'No description available'}
            Rows: {dataset.row_count}
            Columns: {dataset.column_count}
            Column Types: {', '.join([f'{col.name}: {col.confirmed_type}' for col in dataset.columns.all()])}
            """
            context_parts.insert(0, dataset_context)
            
            # Combine all context
            full_context = "\n".join(context_parts[:10])  # Limit to 10 context items
            
            logger.info(f"Retrieved RAG context for planning: {len(context_parts)} items")
            return full_context
            
        except Exception as e:
            logger.error(f"Failed to retrieve RAG context for planning: {str(e)}")
            # Return basic dataset context as fallback
            return f"""
            Dataset Context:
            Name: {dataset.name}
            Rows: {dataset.row_count}
            Columns: {dataset.column_count}
            Analysis Goal: {goal}
            """
    
    def _get_rag_context_for_execution(self, agent_run: AgentRun, step_config: Dict[str, Any],
                                      tool_name: str, parameters: Dict[str, Any]) -> str:
        """
        Retrieve relevant RAG context for agent step execution
        
        Args:
            agent_run: Current agent run
            step_config: Step configuration
            tool_name: Name of the tool being executed
            parameters: Tool parameters
            
        Returns:
            Formatted context string for execution
        """
        try:
            dataset = agent_run.session.primary_dataset
            user = agent_run.user
            
            # Search for relevant context based on tool and step
            search_queries = [
                f"{tool_name} analysis {dataset.name}",
                f"{step_config.get('description', '')} {dataset.name}",
                f"analysis result {tool_name}",
                f"statistical analysis {dataset.name}",
                f"data insights {dataset.name}"
            ]
            
            context_parts = []
            
            for query in search_queries:
                if not query.strip():
                    continue
                    
                # Search for dataset-scoped notes
                dataset_results = self.rag_service.search_vectors(
                    query=query,
                    user=user,
                    dataset=dataset,
                    top_k=2,
                    similarity_threshold=0.6
                )
                
                # Search for global notes
                global_results = self.rag_service.search_vectors(
                    query=query,
                    user=user,
                    dataset=None,
                    top_k=1,
                    similarity_threshold=0.6
                )
                
                # Combine and format results
                for result in dataset_results + global_results:
                    context_parts.append(f"""
                    Execution Context:
                    Title: {result.get('title', 'Unknown')}
                    Content: {result.get('text', '')[:200]}...
                    Confidence: {result.get('confidence_score', 0)}
                    """)
            
            # Add step-specific context
            step_context = f"""
            Step Context:
            Tool: {tool_name}
            Description: {step_config.get('description', 'No description')}
            Parameters: {parameters}
            Expected Output: {step_config.get('expected_output', 'Unknown')}
            Dataset: {dataset.name}
            """
            context_parts.insert(0, step_context)
            
            # Combine all context
            full_context = "\n".join(context_parts[:5])  # Limit to 5 context items
            
            logger.info(f"Retrieved RAG context for execution: {len(context_parts)} items")
            return full_context
            
        except Exception as e:
            logger.error(f"Failed to retrieve RAG context for execution: {str(e)}")
            # Return basic step context as fallback
            return f"""
            Step Context:
            Tool: {tool_name}
            Description: {step_config.get('description', 'No description')}
            Dataset: {agent_run.session.primary_dataset.name}
            """
