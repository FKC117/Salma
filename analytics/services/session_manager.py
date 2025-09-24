"""
Session Manager for Dataset-Tagged Sessions

This service manages analysis sessions with dataset tagging, user preferences,
and comprehensive session state management for the analytical system.
"""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
from django.db import transaction
from django.core.cache import cache
from django.contrib.auth import get_user_model

from analytics.models import (
    AnalysisSession, Dataset, AnalysisResult, ChatMessage, 
    AgentRun, User, AuditTrail
)
from django.db import models
from analytics.services.audit_trail_manager import AuditTrailManager

logger = logging.getLogger(__name__)
User = get_user_model()


class SessionManager:
    """
    Service for managing analysis sessions with dataset tagging and user preferences
    """
    
    def __init__(self):
        self.audit_manager = AuditTrailManager()
        self.session_cache_timeout = getattr(settings, 'SESSION_CACHE_TTL', 3600)  # 1 hour
        self.max_sessions_per_user = getattr(settings, 'MAX_SESSIONS_PER_USER', 50)
        self.session_cleanup_days = getattr(settings, 'SESSION_CLEANUP_DAYS', 30)
    
    def create_session(self, user: User, dataset: Dataset, session_name: Optional[str] = None,
                      description: Optional[str] = None, auto_save: bool = True) -> AnalysisSession:
        """
        Create a new analysis session for a user with a specific dataset
        
        Args:
            user: User creating the session
            dataset: Primary dataset for the session
            session_name: Optional custom name for the session
            description: Optional description for the session
            auto_save: Whether to enable auto-save for this session
            
        Returns:
            AnalysisSession object
        """
        try:
            # Check if user has reached session limit
            active_sessions = AnalysisSession.objects.filter(
                user=user, is_active=True
            ).count()
            
            if active_sessions >= self.max_sessions_per_user:
                # Deactivate oldest session
                oldest_session = AnalysisSession.objects.filter(
                    user=user, is_active=True
                ).order_by('created_at').first()
                
                if oldest_session:
                    self.deactivate_session(oldest_session.id, user)
            
            # Create new session
            with transaction.atomic():
                session = AnalysisSession.objects.create(
                    name=session_name or f"Analysis Session - {dataset.name}",
                    description=description or f"Analysis session for dataset: {dataset.name}",
                    is_active=True,
                    auto_save=auto_save,
                    primary_dataset=dataset,
                    user=user,
                    session_data={
                        'created_at': timezone.now().isoformat(),
                        'dataset_info': {
                            'id': dataset.id,
                            'name': dataset.name,
                            'row_count': dataset.row_count,
                            'column_count': dataset.column_count
                        },
                        'preferences': {
                            'theme': 'dark',
                            'auto_save': auto_save,
                            'notifications': True
                        }
                    }
                )
                
                # Add dataset to additional datasets
                session.additional_datasets.add(dataset)
                
                # Cache session data
                self._cache_session_data(session)
                
                # Log audit trail
                self.audit_manager.log_user_action(
                    user_id=user.id,
                    action_type='create_session',
                    resource_type='session',
                    resource_id=session.id,
                    resource_name=session.name,
                    action_description=f"Created analysis session for dataset: {dataset.name}",
                    data_changed=True
                )
                
                logger.info(f"Created analysis session {session.id} for user {user.id}")
                return session
                
        except Exception as e:
            logger.error(f"Failed to create session: {str(e)}", exc_info=True)
            raise ValueError(f"Failed to create analysis session: {str(e)}")
    
    def get_session(self, session_id: int, user: User) -> Optional[AnalysisSession]:
        """Get analysis session by ID for a specific user"""
        try:
            return AnalysisSession.objects.get(id=session_id, user=user)
        except AnalysisSession.DoesNotExist:
            return None
    
    def get_active_sessions(self, user: User) -> List[AnalysisSession]:
        """Get all active sessions for a user"""
        return AnalysisSession.objects.filter(
            user=user, is_active=True
        ).order_by('-last_analysis_at', '-created_at')
    
    def switch_primary_dataset(self, session_id: int, dataset_id: int, user: User) -> bool:
        """
        Switch the primary dataset for a session
        
        Args:
            session_id: ID of the session
            dataset_id: ID of the new primary dataset
            user: User making the change
            
        Returns:
            True if successful, False otherwise
        """
        try:
            session = self.get_session(session_id, user)
            if not session:
                return False
            
            dataset = Dataset.objects.get(id=dataset_id, user=user)
            
            with transaction.atomic():
                # Update session
                old_dataset = session.primary_dataset
                session.primary_dataset = dataset
                session.last_analysis_at = timezone.now()
                
                # Update session data
                session_data = session.session_data or {}
                session_data['dataset_info'] = {
                    'id': dataset.id,
                    'name': dataset.name,
                    'row_count': dataset.row_count,
                    'column_count': dataset.column_count
                }
                session_data['last_dataset_switch'] = timezone.now().isoformat()
                session.session_data = session_data
                
                session.save()
                
                # Add new dataset to additional datasets if not already present
                if dataset not in session.additional_datasets.all():
                    session.additional_datasets.add(dataset)
                
                # Update cache
                self._cache_session_data(session)
                
                # Log audit trail
                self.audit_manager.log_user_action(
                    user_id=user.id,
                    action_type='switch_dataset',
                    resource_type='session',
                    resource_id=session.id,
                    resource_name=session.name,
                    action_description=f"Switched primary dataset from {old_dataset.name} to {dataset.name}",
                    data_changed=True
                )
                
                logger.info(f"Switched primary dataset for session {session_id} to {dataset_id}")
                return True
                
        except Dataset.DoesNotExist:
            logger.warning(f"Dataset {dataset_id} not found for user {user.id}")
            return False
        except Exception as e:
            logger.error(f"Failed to switch primary dataset: {str(e)}")
            return False
    
    def add_dataset_to_session(self, session_id: int, dataset_id: int, user: User) -> bool:
        """Add a dataset to the session's additional datasets"""
        try:
            session = self.get_session(session_id, user)
            if not session:
                return False
            
            dataset = Dataset.objects.get(id=dataset_id, user=user)
            
            # Add to additional datasets
            session.additional_datasets.add(dataset)
            
            # Update session data
            session_data = session.session_data or {}
            additional_datasets = session_data.get('additional_datasets', [])
            additional_datasets.append({
                'id': dataset.id,
                'name': dataset.name,
                'added_at': timezone.now().isoformat()
            })
            session_data['additional_datasets'] = additional_datasets
            session.session_data = session_data
            session.save()
            
            # Log audit trail
            self.audit_manager.log_user_action(
                user_id=user.id,
                action_type='add_dataset',
                resource_type='session',
                resource_id=session.id,
                resource_name=session.name,
                action_description=f"Added dataset {dataset.name} to session",
                data_changed=True
            )
            
            return True
            
        except Dataset.DoesNotExist:
            return False
        except Exception as e:
            logger.error(f"Failed to add dataset to session: {str(e)}")
            return False
    
    def remove_dataset_from_session(self, session_id: int, dataset_id: int, user: User) -> bool:
        """Remove a dataset from the session's additional datasets"""
        try:
            session = self.get_session(session_id, user)
            if not session:
                return False
            
            dataset = Dataset.objects.get(id=dataset_id, user=user)
            
            # Remove from additional datasets
            session.additional_datasets.remove(dataset)
            
            # Update session data
            session_data = session.session_data or {}
            additional_datasets = session_data.get('additional_datasets', [])
            additional_datasets = [d for d in additional_datasets if d['id'] != dataset_id]
            session_data['additional_datasets'] = additional_datasets
            session.session_data = session_data
            session.save()
            
            # Log audit trail
            self.audit_manager.log_user_action(
                user_id=user.id,
                action_type='remove_dataset',
                resource_type='session',
                resource_id=session.id,
                resource_name=session.name,
                action_description=f"Removed dataset {dataset.name} from session",
                data_changed=True
            )
            
            return True
            
        except Dataset.DoesNotExist:
            return False
        except Exception as e:
            logger.error(f"Failed to remove dataset from session: {str(e)}")
            return False
    
    def update_session_preferences(self, session_id: int, preferences: Dict[str, Any], 
                                  user: User) -> bool:
        """Update user preferences for a session"""
        try:
            session = self.get_session(session_id, user)
            if not session:
                return False
            
            # Update preferences in session data
            session_data = session.session_data or {}
            current_preferences = session_data.get('preferences', {})
            current_preferences.update(preferences)
            session_data['preferences'] = current_preferences
            session.session_data = session_data
            session.save()
            
            # Update cache
            self._cache_session_data(session)
            
            # Log audit trail
            self.audit_manager.log_user_action(
                user_id=user.id,
                action_type='update_preferences',
                resource_type='session',
                resource_id=session.id,
                resource_name=session.name,
                action_description="Updated session preferences",
                data_changed=True
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update session preferences: {str(e)}")
            return False
    
    def get_session_analysis_history(self, session_id: int, user: User, 
                                   limit: int = 50) -> List[AnalysisResult]:
        """Get analysis history for a session"""
        try:
            session = self.get_session(session_id, user)
            if not session:
                return []
            
            return AnalysisResult.objects.filter(
                session=session, user=user
            ).order_by('-created_at')[:limit]
            
        except Exception as e:
            logger.error(f"Failed to get session analysis history: {str(e)}")
            return []
    
    def get_session_chat_history(self, session_id: int, user: User, 
                               limit: int = 100) -> List[ChatMessage]:
        """Get chat history for a session"""
        try:
            session = self.get_session(session_id, user)
            if not session:
                return []
            
            return ChatMessage.objects.filter(
                session=session, user=user
            ).order_by('-created_at')[:limit]
            
        except Exception as e:
            logger.error(f"Failed to get session chat history: {str(e)}")
            return []
    
    def get_session_agent_runs(self, session_id: int, user: User, 
                              limit: int = 20) -> List[AgentRun]:
        """Get agent runs for a session"""
        try:
            session = self.get_session(session_id, user)
            if not session:
                return []
            
            return AgentRun.objects.filter(
                session=session, user=user
            ).order_by('-created_at')[:limit]
            
        except Exception as e:
            logger.error(f"Failed to get session agent runs: {str(e)}")
            return []
    
    def deactivate_session(self, session_id: int, user: User) -> bool:
        """Deactivate a session (soft delete)"""
        try:
            session = self.get_session(session_id, user)
            if not session:
                return False
            
            session.is_active = False
            session.save()
            
            # Clear cache
            self._clear_session_cache(session_id)
            
            # Log audit trail
            self.audit_manager.log_user_action(
                user_id=user.id,
                action_type='deactivate_session',
                resource_type='session',
                resource_id=session.id,
                resource_name=session.name,
                action_description="Deactivated analysis session",
                data_changed=True
            )
            
            logger.info(f"Deactivated session {session_id} for user {user.id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to deactivate session: {str(e)}")
            return False
    
    def delete_session(self, session_id: int, user: User) -> bool:
        """Permanently delete a session and all associated data"""
        try:
            session = self.get_session(session_id, user)
            if not session:
                return False
            
            with transaction.atomic():
                # Delete associated data
                AnalysisResult.objects.filter(session=session).delete()
                ChatMessage.objects.filter(session=session).delete()
                AgentRun.objects.filter(session=session).delete()
                
                # Delete session
                session.delete()
                
                # Clear cache
                self._clear_session_cache(session_id)
                
                # Log audit trail
                self.audit_manager.log_user_action(
                    user_id=user.id,
                    action_type='delete_session',
                    resource_type='session',
                    resource_id=session_id,
                    resource_name=session.name,
                    action_description="Permanently deleted analysis session",
                    data_changed=True
                )
                
                logger.info(f"Deleted session {session_id} for user {user.id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to delete session: {str(e)}")
            return False
    
    def get_session_statistics(self, session_id: int, user: User) -> Dict[str, Any]:
        """Get comprehensive statistics for a session"""
        try:
            session = self.get_session(session_id, user)
            if not session:
                return {}
            
            # Get analysis results
            analysis_results = AnalysisResult.objects.filter(session=session)
            
            # Get chat messages
            chat_messages = ChatMessage.objects.filter(session=session)
            
            # Get agent runs
            agent_runs = AgentRun.objects.filter(session=session)
            
            # Calculate statistics
            stats = {
                'session_info': {
                    'id': session.id,
                    'name': session.name,
                    'created_at': session.created_at.isoformat(),
                    'last_analysis_at': session.last_analysis_at.isoformat() if session.last_analysis_at else None,
                    'is_active': session.is_active
                },
                'dataset_info': {
                    'primary_dataset': {
                        'id': session.primary_dataset.id,
                        'name': session.primary_dataset.name,
                        'row_count': session.primary_dataset.row_count,
                        'column_count': session.primary_dataset.column_count
                    },
                    'additional_datasets_count': session.additional_datasets.count()
                },
                'analysis_stats': {
                    'total_analyses': analysis_results.count(),
                    'successful_analyses': analysis_results.filter(confidence_score__gte=0.7).count(),
                    'average_execution_time': analysis_results.aggregate(
                        avg_time=models.Avg('execution_time_ms')
                    )['avg_time'] or 0,
                    'tools_used': list(analysis_results.values_list('tool_used__name', flat=True).distinct())
                },
                'chat_stats': {
                    'total_messages': chat_messages.count(),
                    'user_messages': chat_messages.filter(message_type='user').count(),
                    'ai_messages': chat_messages.filter(message_type='ai').count(),
                    'total_tokens': sum(msg.token_count or 0 for msg in chat_messages)
                },
                'agent_stats': {
                    'total_runs': agent_runs.count(),
                    'completed_runs': agent_runs.filter(status='completed').count(),
                    'failed_runs': agent_runs.filter(status='failed').count(),
                    'average_steps': agent_runs.aggregate(
                        avg_steps=models.Avg('total_steps')
                    )['avg_steps'] or 0
                }
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get session statistics: {str(e)}")
            return {}
    
    def cleanup_old_sessions(self) -> int:
        """Clean up old inactive sessions"""
        try:
            cutoff_date = timezone.now() - timedelta(days=self.session_cleanup_days)
            
            old_sessions = AnalysisSession.objects.filter(
                is_active=False,
                last_analysis_at__lt=cutoff_date
            )
            
            count = old_sessions.count()
            old_sessions.delete()
            
            logger.info(f"Cleaned up {count} old sessions")
            return count
            
        except Exception as e:
            logger.error(f"Failed to cleanup old sessions: {str(e)}")
            return 0
    
    def _cache_session_data(self, session: AnalysisSession) -> None:
        """Cache session data for quick access"""
        try:
            cache_key = f"session_{session.id}"
            session_data = {
                'id': session.id,
                'name': session.name,
                'is_active': session.is_active,
                'primary_dataset_id': session.primary_dataset.id,
                'additional_datasets': list(session.additional_datasets.values_list('id', flat=True)),
                'session_data': session.session_data,
                'user_preferences': session.user_preferences,
                'analysis_count': session.analysis_count,
                'last_analysis_at': session.last_analysis_at.isoformat() if session.last_analysis_at else None
            }
            
            cache.set(cache_key, session_data, self.session_cache_timeout)
            
        except Exception as e:
            logger.warning(f"Failed to cache session data: {str(e)}")
    
    def _clear_session_cache(self, session_id: int) -> None:
        """Clear cached session data"""
        try:
            cache_key = f"session_{session_id}"
            cache.delete(cache_key)
        except Exception as e:
            logger.warning(f"Failed to clear session cache: {str(e)}")
    
    def get_cached_session_data(self, session_id: int) -> Optional[Dict[str, Any]]:
        """Get cached session data"""
        try:
            cache_key = f"session_{session_id}"
            return cache.get(cache_key)
        except Exception as e:
            logger.warning(f"Failed to get cached session data: {str(e)}")
            return None
    
    def export_session_data(self, session_id: int, user: User, 
                          include_analyses: bool = True, include_chat: bool = True) -> Dict[str, Any]:
        """Export session data for backup or migration"""
        try:
            session = self.get_session(session_id, user)
            if not session:
                return {}
            
            export_data = {
                'session_info': {
                    'id': session.id,
                    'name': session.name,
                    'description': session.description,
                    'created_at': session.created_at.isoformat(),
                    'last_analysis_at': session.last_analysis_at.isoformat() if session.last_analysis_at else None,
                    'is_active': session.is_active,
                    'auto_save': session.auto_save
                },
                'dataset_info': {
                    'primary_dataset': {
                        'id': session.primary_dataset.id,
                        'name': session.primary_dataset.name,
                        'description': session.primary_dataset.description
                    },
                    'additional_datasets': [
                        {
                            'id': dataset.id,
                            'name': dataset.name,
                            'description': dataset.description
                        }
                        for dataset in session.additional_datasets.all()
                    ]
                },
                'session_data': session.session_data,
                'user_preferences': session.user_preferences
            }
            
            if include_analyses:
                export_data['analyses'] = [
                    {
                        'id': result.id,
                        'name': result.name,
                        'tool_used': result.tool_used.name,
                        'parameters': result.parameters_used,
                        'output_type': result.output_type,
                        'execution_time': result.execution_time_ms,
                        'created_at': result.created_at.isoformat()
                    }
                    for result in AnalysisResult.objects.filter(session=session)
                ]
            
            if include_chat:
                export_data['chat_messages'] = [
                    {
                        'id': msg.id,
                        'content': msg.content,
                        'message_type': msg.message_type,
                        'llm_model': msg.llm_model,
                        'token_count': msg.token_count,
                        'created_at': msg.created_at.isoformat()
                    }
                    for msg in ChatMessage.objects.filter(session=session)
                ]
            
            return export_data
            
        except Exception as e:
            logger.error(f"Failed to export session data: {str(e)}")
            return {}
