"""
Query Optimization Service

This service provides comprehensive database query optimization using Django's
select_related and prefetch_related to minimize database queries and improve
performance across the analytical system.
"""

import logging
from typing import Dict, List, Any, Optional, Union, Type
from django.db import models
from django.db.models import QuerySet, Prefetch
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from collections import defaultdict
import time

from analytics.models import (
    User, Dataset, DatasetColumn, AnalysisSession, AnalysisResult,
    ChatMessage, AgentRun, GeneratedImage, AuditTrail, VectorNote
)

logger = logging.getLogger(__name__)


class QueryOptimizer:
    """
    Comprehensive query optimization service for the analytical system
    """
    
    def __init__(self):
        self.optimization_cache = {}
        self.query_stats = defaultdict(int)
        self.performance_metrics = {
            'optimizations_applied': 0,
            'queries_saved': 0,
            'cache_hits': 0,
            'cache_misses': 0
        }
        
        # Define optimization patterns for each model
        self.optimization_patterns = self._define_optimization_patterns()
        
        # Cache timeout for optimization results
        self.cache_timeout = getattr(settings, 'QUERY_OPTIMIZATION_CACHE_TTL', 300)
    
    def _define_optimization_patterns(self) -> Dict[str, Dict[str, Any]]:
        """
        Define optimization patterns for each model
        
        Returns:
            Dict mapping model names to their optimization patterns
        """
        return {
            'User': {
                'select_related': [],
                'prefetch_related': [
                    'datasets',
                    'analysis_sessions',
                    'audit_trails'
                ],
                'common_queries': [
                    'user_with_datasets',
                    'user_with_sessions',
                    'user_with_usage_stats'
                ]
            },
            'Dataset': {
                'select_related': ['user'],
                'prefetch_related': [
                    'columns',
                    'analysis_sessions',
                    'analysis_results'
                ],
                'common_queries': [
                    'dataset_with_columns',
                    'dataset_with_user',
                    'dataset_with_analysis_history'
                ]
            },
            'DatasetColumn': {
                'select_related': ['dataset', 'dataset__user'],
                'prefetch_related': [],
                'common_queries': [
                    'columns_with_dataset',
                    'columns_with_user'
                ]
            },
            'AnalysisSession': {
                'select_related': ['user', 'dataset'],
                'prefetch_related': [
                    'results',
                    'chat_messages',
                    'agent_runs'
                ],
                'common_queries': [
                    'session_with_user_dataset',
                    'session_with_results',
                    'session_with_chat_history'
                ]
            },
            'AnalysisResult': {
                'select_related': ['session', 'session__user', 'session__dataset'],
                'prefetch_related': ['generated_images'],
                'common_queries': [
                    'result_with_session',
                    'result_with_user_dataset',
                    'result_with_images'
                ]
            },
            'ChatMessage': {
                'select_related': ['session', 'session__user', 'session__dataset'],
                'prefetch_related': [],
                'common_queries': [
                    'message_with_session',
                    'message_with_user_dataset'
                ]
            },
            'AgentRun': {
                'select_related': ['session', 'session__user', 'session__dataset'],
                'prefetch_related': ['results'],
                'common_queries': [
                    'agent_run_with_session',
                    'agent_run_with_results'
                ]
            },
            'GeneratedImage': {
                'select_related': ['result', 'result__session', 'result__session__user'],
                'prefetch_related': [],
                'common_queries': [
                    'image_with_result',
                    'image_with_user_session'
                ]
            },
            'AuditTrail': {
                'select_related': ['user'],
                'prefetch_related': [],
                'common_queries': [
                    'audit_with_user'
                ]
            },
            'VectorNote': {
                'select_related': ['user'],
                'prefetch_related': [],
                'common_queries': [
                    'vector_note_with_user'
                ]
            }
        }
    
    def optimize_queryset(self, queryset: QuerySet, optimization_type: str = 'auto') -> QuerySet:
        """
        Optimize a queryset based on the model and optimization type
        
        Args:
            queryset: Django QuerySet to optimize
            optimization_type: Type of optimization ('auto', 'minimal', 'comprehensive')
            
        Returns:
            Optimized QuerySet
        """
        try:
            model_name = queryset.model.__name__
            
            if model_name not in self.optimization_patterns:
                logger.warning(f"No optimization patterns defined for model: {model_name}")
                return queryset
            
            patterns = self.optimization_patterns[model_name]
            
            # Apply select_related optimizations
            if patterns.get('select_related'):
                queryset = queryset.select_related(*patterns['select_related'])
                self.performance_metrics['optimizations_applied'] += 1
            
            # Apply prefetch_related optimizations
            if patterns.get('prefetch_related'):
                queryset = queryset.prefetch_related(*patterns['prefetch_related'])
                self.performance_metrics['optimizations_applied'] += 1
            
            # Log optimization
            logger.debug(f"Optimized queryset for {model_name}: {optimization_type}")
            
            return queryset
            
        except Exception as e:
            logger.error(f"Query optimization failed: {str(e)}")
            return queryset
    
    def get_user_with_datasets(self, user_id: int) -> Optional[User]:
        """
        Get user with all related datasets optimized
        
        Args:
            user_id: User ID
            
        Returns:
            User instance with datasets prefetched
        """
        try:
            cache_key = f"user_datasets_{user_id}"
            cached_result = cache.get(cache_key)
            
            if cached_result:
                self.performance_metrics['cache_hits'] += 1
                return cached_result
            
            user = User.objects.select_related().prefetch_related(
                'datasets',
                'datasets__columns'
            ).get(id=user_id)
            
            # Cache the result
            cache.set(cache_key, user, self.cache_timeout)
            self.performance_metrics['cache_misses'] += 1
            
            return user
            
        except User.DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Failed to get user with datasets: {str(e)}")
            return None
    
    def get_dataset_with_columns(self, dataset_id: int) -> Optional[Dataset]:
        """
        Get dataset with all columns optimized
        
        Args:
            dataset_id: Dataset ID
            
        Returns:
            Dataset instance with columns prefetched
        """
        try:
            cache_key = f"dataset_columns_{dataset_id}"
            cached_result = cache.get(cache_key)
            
            if cached_result:
                self.performance_metrics['cache_hits'] += 1
                return cached_result
            
            dataset = Dataset.objects.select_related(
                'user'
            ).prefetch_related(
                'columns'
            ).get(id=dataset_id)
            
            # Cache the result
            cache.set(cache_key, dataset, self.cache_timeout)
            self.performance_metrics['cache_misses'] += 1
            
            return dataset
            
        except Dataset.DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Failed to get dataset with columns: {str(e)}")
            return None
    
    def get_analysis_session_with_results(self, session_id: int) -> Optional[AnalysisSession]:
        """
        Get analysis session with all results optimized
        
        Args:
            session_id: Session ID
            
        Returns:
            AnalysisSession instance with results prefetched
        """
        try:
            cache_key = f"session_results_{session_id}"
            cached_result = cache.get(cache_key)
            
            if cached_result:
                self.performance_metrics['cache_hits'] += 1
                return cached_result
            
            session = AnalysisSession.objects.select_related(
                'user',
                'dataset'
            ).prefetch_related(
                'results',
                'results__generated_images',
                'chat_messages',
                'agent_runs'
            ).get(id=session_id)
            
            # Cache the result
            cache.set(cache_key, session, self.cache_timeout)
            self.performance_metrics['cache_misses'] += 1
            
            return session
            
        except AnalysisSession.DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Failed to get session with results: {str(e)}")
            return None
    
    def get_user_datasets_optimized(self, user_id: int) -> QuerySet:
        """
        Get user's datasets with optimized queries
        
        Args:
            user_id: User ID
            
        Returns:
            Optimized QuerySet of datasets
        """
        try:
            datasets = Dataset.objects.filter(user_id=user_id)
            return self.optimize_queryset(datasets)
            
        except Exception as e:
            logger.error(f"Failed to get user datasets: {str(e)}")
            return Dataset.objects.none()
    
    def get_dataset_columns_optimized(self, dataset_id: int) -> QuerySet:
        """
        Get dataset columns with optimized queries
        
        Args:
            dataset_id: Dataset ID
            
        Returns:
            Optimized QuerySet of columns
        """
        try:
            columns = DatasetColumn.objects.filter(dataset_id=dataset_id)
            return self.optimize_queryset(columns)
            
        except Exception as e:
            logger.error(f"Failed to get dataset columns: {str(e)}")
            return DatasetColumn.objects.none()
    
    def get_analysis_results_optimized(self, session_id: int) -> QuerySet:
        """
        Get analysis results with optimized queries
        
        Args:
            session_id: Session ID
            
        Returns:
            Optimized QuerySet of results
        """
        try:
            results = AnalysisResult.objects.filter(session_id=session_id)
            return self.optimize_queryset(results)
            
        except Exception as e:
            logger.error(f"Failed to get analysis results: {str(e)}")
            return AnalysisResult.objects.none()
    
    def get_chat_messages_optimized(self, session_id: int) -> QuerySet:
        """
        Get chat messages with optimized queries
        
        Args:
            session_id: Session ID
            
        Returns:
            Optimized QuerySet of chat messages
        """
        try:
            messages = ChatMessage.objects.filter(session_id=session_id)
            return self.optimize_queryset(messages)
            
        except Exception as e:
            logger.error(f"Failed to get chat messages: {str(e)}")
            return ChatMessage.objects.none()
    
    def get_agent_runs_optimized(self, session_id: int) -> QuerySet:
        """
        Get agent runs with optimized queries
        
        Args:
            session_id: Session ID
            
        Returns:
            Optimized QuerySet of agent runs
        """
        try:
            agent_runs = AgentRun.objects.filter(session_id=session_id)
            return self.optimize_queryset(agent_runs)
            
        except Exception as e:
            logger.error(f"Failed to get agent runs: {str(e)}")
            return AgentRun.objects.none()
    
    def get_audit_trails_optimized(self, user_id: int, limit: int = 100) -> QuerySet:
        """
        Get audit trails with optimized queries
        
        Args:
            user_id: User ID
            limit: Maximum number of records
            
        Returns:
            Optimized QuerySet of audit trails
        """
        try:
            audit_trails = AuditTrail.objects.filter(user_id=user_id)[:limit]
            return self.optimize_queryset(audit_trails)
            
        except Exception as e:
            logger.error(f"Failed to get audit trails: {str(e)}")
            return AuditTrail.objects.none()
    
    def bulk_optimize_querysets(self, querysets: Dict[str, QuerySet]) -> Dict[str, QuerySet]:
        """
        Optimize multiple querysets at once
        
        Args:
            querysets: Dict mapping names to QuerySets
            
        Returns:
            Dict with optimized QuerySets
        """
        try:
            optimized = {}
            
            for name, queryset in querysets.items():
                optimized[name] = self.optimize_queryset(queryset)
            
            logger.info(f"Bulk optimized {len(querysets)} querysets")
            return optimized
            
        except Exception as e:
            logger.error(f"Bulk optimization failed: {str(e)}")
            return querysets
    
    def create_optimized_prefetch(self, model_class: Type[models.Model], 
                                 related_field: str, 
                                 queryset: Optional[QuerySet] = None) -> Prefetch:
        """
        Create an optimized Prefetch object
        
        Args:
            model_class: Model class for the related field
            related_field: Name of the related field
            queryset: Optional queryset to use for prefetching
            
        Returns:
            Optimized Prefetch object
        """
        try:
            if queryset is None:
                queryset = model_class.objects.all()
            
            # Apply optimizations to the queryset
            queryset = self.optimize_queryset(queryset)
            
            return Prefetch(related_field, queryset)
            
        except Exception as e:
            logger.error(f"Failed to create optimized prefetch: {str(e)}")
            return Prefetch(related_field)
    
    def get_dashboard_data_optimized(self, user_id: int) -> Dict[str, Any]:
        """
        Get all dashboard data with optimized queries
        
        Args:
            user_id: User ID
            
        Returns:
            Dict with optimized dashboard data
        """
        try:
            start_time = time.time()
            
            # Get user with all related data
            user = self.get_user_with_datasets(user_id)
            if not user:
                return {}
            
            # Get datasets with columns
            datasets = self.get_user_datasets_optimized(user_id)
            
            # Get recent sessions
            recent_sessions = AnalysisSession.objects.filter(
                user_id=user_id
            ).select_related('dataset').prefetch_related('results')[:10]
            
            # Get recent audit trails
            recent_audits = self.get_audit_trails_optimized(user_id, 20)
            
            execution_time = time.time() - start_time
            
            return {
                'user': user,
                'datasets': datasets,
                'recent_sessions': recent_sessions,
                'recent_audits': recent_audits,
                'execution_time': execution_time,
                'optimization_applied': True
            }
            
        except Exception as e:
            logger.error(f"Failed to get dashboard data: {str(e)}")
            return {}
    
    def clear_optimization_cache(self, pattern: Optional[str] = None) -> bool:
        """
        Clear optimization cache
        
        Args:
            pattern: Optional pattern to match cache keys
            
        Returns:
            True if successful
        """
        try:
            if pattern:
                # Clear specific pattern
                cache.delete_many([key for key in cache._cache.keys() if pattern in key])
            else:
                # Clear all optimization cache
                cache.delete_many([key for key in cache._cache.keys() if 'user_' in key or 'dataset_' in key or 'session_' in key])
            
            logger.info(f"Optimization cache cleared: {pattern or 'all'}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear optimization cache: {str(e)}")
            return False
    
    def get_optimization_stats(self) -> Dict[str, Any]:
        """
        Get optimization statistics
        
        Returns:
            Dict with optimization statistics
        """
        return {
            'performance_metrics': self.performance_metrics.copy(),
            'query_stats': dict(self.query_stats),
            'optimization_patterns': len(self.optimization_patterns),
            'cache_timeout': self.cache_timeout,
            'timestamp': timezone.now().isoformat()
        }
    
    def analyze_query_performance(self, queryset: QuerySet) -> Dict[str, Any]:
        """
        Analyze query performance and provide recommendations
        
        Args:
            queryset: QuerySet to analyze
            
        Returns:
            Dict with performance analysis
        """
        try:
            start_time = time.time()
            
            # Execute query to get timing
            list(queryset)
            
            execution_time = time.time() - start_time
            
            # Analyze query
            analysis = {
                'model': queryset.model.__name__,
                'execution_time': execution_time,
                'query_count': len(queryset.query.get_compiler().execute_sql()),
                'optimization_recommendations': []
            }
            
            # Provide recommendations
            if execution_time > 1.0:  # More than 1 second
                analysis['optimization_recommendations'].append(
                    "Consider using select_related or prefetch_related"
                )
            
            if queryset.query.select_related:
                analysis['optimization_recommendations'].append(
                    "select_related is already applied"
                )
            
            if queryset.query.prefetch_related:
                analysis['optimization_recommendations'].append(
                    "prefetch_related is already applied"
                )
            
            return analysis
            
        except Exception as e:
            logger.error(f"Query performance analysis failed: {str(e)}")
            return {'error': str(e)}


# Global instance for easy access
query_optimizer = QueryOptimizer()


# Convenience functions for easy integration
def optimize_queryset(queryset: QuerySet, optimization_type: str = 'auto') -> QuerySet:
    """
    Convenience function to optimize a queryset
    
    Args:
        queryset: Django QuerySet to optimize
        optimization_type: Type of optimization
        
    Returns:
        Optimized QuerySet
    """
    return query_optimizer.optimize_queryset(queryset, optimization_type)


def get_user_with_datasets(user_id: int) -> Optional[User]:
    """
    Convenience function to get user with datasets
    
    Args:
        user_id: User ID
        
    Returns:
        User instance with datasets prefetched
    """
    return query_optimizer.get_user_with_datasets(user_id)


def get_dataset_with_columns(dataset_id: int) -> Optional[Dataset]:
    """
    Convenience function to get dataset with columns
    
    Args:
        dataset_id: Dataset ID
        
    Returns:
        Dataset instance with columns prefetched
    """
    return query_optimizer.get_dataset_with_columns(dataset_id)


def get_analysis_session_with_results(session_id: int) -> Optional[AnalysisSession]:
    """
    Convenience function to get analysis session with results
    
    Args:
        session_id: Session ID
        
    Returns:
        AnalysisSession instance with results prefetched
    """
    return query_optimizer.get_analysis_session_with_results(session_id)


def clear_optimization_cache(pattern: Optional[str] = None) -> bool:
    """
    Convenience function to clear optimization cache
    
    Args:
        pattern: Optional pattern to match cache keys
        
    Returns:
        True if successful
    """
    return query_optimizer.clear_optimization_cache(pattern)
