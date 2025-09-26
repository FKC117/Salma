"""
Caching Strategy Service

This service provides comprehensive caching strategies for the analytical system,
including intelligent cache management, cache warming, invalidation patterns,
and performance optimization through strategic caching.
"""

import json
import time
import logging
from typing import Dict, List, Any, Optional, Union, Callable
from datetime import datetime, timedelta
from django.conf import settings
from django.core.cache import cache, caches
from django.utils import timezone
from django.db import models
from django.db.models import QuerySet
import hashlib
import pickle
from functools import wraps

from analytics.models import (
    User, Dataset, DatasetColumn, AnalysisSession, AnalysisResult,
    ChatMessage, AgentRun, GeneratedImage, AuditTrail, VectorNote
)

logger = logging.getLogger(__name__)


class CachingStrategyService:
    """
    Comprehensive caching strategy service for the analytical system
    """
    
    def __init__(self):
        # Cache configurations
        self.cache_aliases = {
            'default': 'default',
            'sessions': 'sessions',
            'analysis': 'analysis'
        }
        
        # Cache TTL configurations (in seconds)
        self.cache_ttls = {
            'user_data': 3600,  # 1 hour
            'dataset_info': 1800,  # 30 minutes
            'analysis_results': 7200,  # 2 hours
            'session_data': 1800,  # 30 minutes
            'query_results': 300,  # 5 minutes
            'dashboard_data': 600,  # 10 minutes
            'image_metadata': 3600,  # 1 hour
            'audit_trails': 900,  # 15 minutes
            'vector_notes': 1800,  # 30 minutes
            'static_data': 86400,  # 24 hours
        }
        
        # Cache key patterns
        self.key_patterns = {
            'user': 'user:{user_id}',
            'user_datasets': 'user:{user_id}:datasets',
            'user_sessions': 'user:{user_id}:sessions',
            'dataset': 'dataset:{dataset_id}',
            'dataset_columns': 'dataset:{dataset_id}:columns',
            'session': 'session:{session_id}',
            'session_results': 'session:{session_id}:results',
            'analysis_result': 'analysis:{result_id}',
            'dashboard': 'dashboard:{user_id}',
            'query': 'query:{query_hash}',
            'image': 'image:{image_id}',
            'audit': 'audit:{user_id}:{limit}',
            'vector_note': 'vector_note:{note_id}',
        }
        
        # Cache warming strategies
        self.warming_strategies = {
            'user_on_login': ['user_data', 'user_datasets', 'dashboard_data'],
            'dataset_on_upload': ['dataset_info', 'dataset_columns'],
            'session_on_create': ['session_data', 'user_sessions'],
            'analysis_on_complete': ['analysis_results', 'session_results']
        }
        
        # Performance metrics
        self.metrics = {
            'cache_hits': 0,
            'cache_misses': 0,
            'cache_sets': 0,
            'cache_deletes': 0,
            'cache_warming_operations': 0,
            'cache_invalidations': 0,
            'total_bytes_cached': 0,
            'average_cache_size': 0
        }
        
        # Cache invalidation patterns
        self.invalidation_patterns = {
            'user_update': ['user:{user_id}', 'user:{user_id}:*', 'dashboard:{user_id}'],
            'dataset_update': ['dataset:{dataset_id}', 'dataset:{dataset_id}:*', 'user:{user_id}:datasets'],
            'session_update': ['session:{session_id}', 'session:{session_id}:*', 'user:{user_id}:sessions'],
            'analysis_complete': ['analysis:{result_id}', 'session:{session_id}:results']
        }
    
    def get_cache(self, alias: str = 'default'):
        """Get cache instance by alias"""
        return caches[self.cache_aliases.get(alias, 'default')]
    
    def generate_cache_key(self, pattern: str, **kwargs) -> str:
        """Generate cache key from pattern and parameters"""
        try:
            return pattern.format(**kwargs)
        except KeyError as e:
            logger.error(f"Missing parameter for cache key pattern {pattern}: {e}")
            return f"{pattern}:{hash(str(kwargs))}"
    
    def cache_function_result(self, ttl: int = 300, cache_alias: str = 'default',
                            key_prefix: str = '', include_args: bool = True):
        """
        Decorator to cache function results
        
        Args:
            ttl: Time to live in seconds
            cache_alias: Cache alias to use
            key_prefix: Prefix for cache key
            include_args: Whether to include function arguments in key
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Generate cache key
                if include_args:
                    key_data = f"{func.__name__}:{str(args)}:{str(sorted(kwargs.items()))}"
                else:
                    key_data = func.__name__
                
                cache_key = f"{key_prefix}:{hashlib.md5(key_data.encode()).hexdigest()}"
                
                # Try to get from cache
                cache_instance = self.get_cache(cache_alias)
                cached_result = cache_instance.get(cache_key)
                
                if cached_result is not None:
                    self.metrics['cache_hits'] += 1
                    logger.debug(f"Cache hit for {func.__name__}: {cache_key}")
                    return cached_result
                
                # Execute function and cache result
                result = func(*args, **kwargs)
                cache_instance.set(cache_key, result, ttl)
                self.metrics['cache_misses'] += 1
                self.metrics['cache_sets'] += 1
                
                logger.debug(f"Cached result for {func.__name__}: {cache_key}")
                return result
            
            return wrapper
        return decorator
    
    def cache_user_data(self, user_id: int, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Cache comprehensive user data
        
        Args:
            user_id: User ID
            force_refresh: Force refresh even if cached
            
        Returns:
            Dict with cached user data
        """
        try:
            cache_key = self.generate_cache_key(self.key_patterns['user'], user_id=user_id)
            cache_instance = self.get_cache('default')
            
            if not force_refresh:
                cached_data = cache_instance.get(cache_key)
                if cached_data:
                    self.metrics['cache_hits'] += 1
                    return cached_data
            
            # Fetch fresh data
            user = User.objects.select_related().prefetch_related(
                'datasets', 'analysis_sessions', 'audit_trails'
            ).get(id=user_id)
            
            user_data = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_premium': user.is_premium,
                'account_suspended': user.account_suspended,
                'token_usage_current_month': user.token_usage_current_month,
                'max_tokens_per_month': user.max_tokens_per_month,
                'storage_used_bytes': user.storage_used_bytes,
                'max_storage_bytes': user.max_storage_bytes,
                'preferred_theme': user.preferred_theme,
                'auto_save_analysis': user.auto_save_analysis,
                'last_activity': user.last_activity,
                'datasets_count': user.datasets.count(),
                'sessions_count': user.analysis_sessions.count(),
                'usage_summary': user.get_usage_summary()
            }
            
            # Cache the data
            cache_instance.set(cache_key, user_data, self.cache_ttls['user_data'])
            self.metrics['cache_misses'] += 1
            self.metrics['cache_sets'] += 1
            
            logger.info(f"Cached user data for user {user_id}")
            return user_data
            
        except User.DoesNotExist:
            return {}
        except Exception as e:
            logger.error(f"Failed to cache user data: {str(e)}")
            return {}
    
    def cache_dataset_info(self, dataset_id: int, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Cache dataset information with columns
        
        Args:
            dataset_id: Dataset ID
            force_refresh: Force refresh even if cached
            
        Returns:
            Dict with cached dataset data
        """
        try:
            cache_key = self.generate_cache_key(self.key_patterns['dataset'], dataset_id=dataset_id)
            cache_instance = self.get_cache('default')
            
            if not force_refresh:
                cached_data = cache_instance.get(cache_key)
                if cached_data:
                    self.metrics['cache_hits'] += 1
                    return cached_data
            
            # Fetch fresh data
            dataset = Dataset.objects.select_related('user').prefetch_related('columns').get(id=dataset_id)
            
            dataset_data = {
                'id': dataset.id,
                'name': dataset.name,
                'description': dataset.description,
                'original_filename': dataset.original_filename,
                'file_size_bytes': dataset.file_size_bytes,
                'file_size_mb': dataset.file_size_mb,
                'original_format': dataset.original_format,
                'row_count': dataset.row_count,
                'column_count': dataset.column_count,
                'data_types': dataset.data_types,
                'processing_status': dataset.processing_status,
                'data_quality_score': dataset.data_quality_score,
                'completeness_score': dataset.completeness_score,
                'consistency_score': dataset.consistency_score,
                'security_scan_passed': dataset.security_scan_passed,
                'sanitized': dataset.sanitized,
                'is_public': dataset.is_public,
                'access_level': dataset.access_level,
                'created_at': dataset.created_at,
                'updated_at': dataset.updated_at,
                'last_accessed': dataset.last_accessed,
                'user_id': dataset.user.id,
                'user_username': dataset.user.username,
                'columns': [
                    {
                        'id': col.id,
                        'name': col.name,
                        'display_name': col.display_name,
                        'detected_type': col.detected_type,
                        'confirmed_type': col.confirmed_type,
                        'confidence_score': col.confidence_score,
                        'null_count': col.null_count,
                        'null_percentage': col.null_percentage,
                        'unique_count': col.unique_count,
                        'unique_percentage': col.unique_percentage
                    }
                    for col in dataset.columns.all()
                ]
            }
            
            # Cache the data
            cache_instance.set(cache_key, dataset_data, self.cache_ttls['dataset_info'])
            self.metrics['cache_misses'] += 1
            self.metrics['cache_sets'] += 1
            
            logger.info(f"Cached dataset info for dataset {dataset_id}")
            return dataset_data
            
        except Dataset.DoesNotExist:
            return {}
        except Exception as e:
            logger.error(f"Failed to cache dataset info: {str(e)}")
            return {}
    
    def cache_analysis_results(self, session_id: int, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Cache analysis results for a session
        
        Args:
            session_id: Session ID
            force_refresh: Force refresh even if cached
            
        Returns:
            List of cached analysis results
        """
        try:
            cache_key = self.generate_cache_key(self.key_patterns['session_results'], session_id=session_id)
            cache_instance = self.get_cache('analysis')
            
            if not force_refresh:
                cached_data = cache_instance.get(cache_key)
                if cached_data:
                    self.metrics['cache_hits'] += 1
                    return cached_data
            
            # Fetch fresh data
            results = AnalysisResult.objects.filter(session_id=session_id).select_related(
                'session', 'session__user', 'session__dataset'
            ).prefetch_related('generated_images')
            
            results_data = []
            for result in results:
                result_data = {
                    'id': result.id,
                    'tool_name': result.tool_name,
                    'tool_category': result.tool_category,
                    'parameters': result.parameters,
                    'result_data': result.result_data,
                    'result_type': result.result_type,
                    'execution_time': result.execution_time,
                    'status': result.status,
                    'error_message': result.error_message,
                    'created_at': result.created_at,
                    'session_id': result.session.id,
                    'session_name': result.session.name,
                    'user_id': result.session.user.id,
                    'user_username': result.session.user.username,
                    'dataset_id': result.session.dataset.id,
                    'dataset_name': result.session.dataset.name,
                    'images': [
                        {
                            'id': img.id,
                            'name': img.name,
                            'file_path': img.file_path,
                            'file_size_bytes': img.file_size_bytes,
                            'image_format': img.image_format,
                            'width': img.width,
                            'height': img.height
                        }
                        for img in result.generated_images.all()
                    ]
                }
                results_data.append(result_data)
            
            # Cache the data
            cache_instance.set(cache_key, results_data, self.cache_ttls['analysis_results'])
            self.metrics['cache_misses'] += 1
            self.metrics['cache_sets'] += 1
            
            logger.info(f"Cached analysis results for session {session_id}")
            return results_data
            
        except Exception as e:
            logger.error(f"Failed to cache analysis results: {str(e)}")
            return []
    
    def cache_dashboard_data(self, user_id: int, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Cache comprehensive dashboard data for a user
        
        Args:
            user_id: User ID
            force_refresh: Force refresh even if cached
            
        Returns:
            Dict with cached dashboard data
        """
        try:
            cache_key = self.generate_cache_key(self.key_patterns['dashboard'], user_id=user_id)
            cache_instance = self.get_cache('default')
            
            if not force_refresh:
                cached_data = cache_instance.get(cache_key)
                if cached_data:
                    self.metrics['cache_hits'] += 1
                    return cached_data
            
            # Fetch fresh data
            user = User.objects.select_related().prefetch_related(
                'datasets', 'analysis_sessions', 'audit_trails'
            ).get(id=user_id)
            
            # Get recent datasets
            recent_datasets = user.datasets.order_by('-created_at')[:5]
            
            # Get recent sessions
            recent_sessions = user.analysis_sessions.select_related('dataset').order_by('-created_at')[:10]
            
            # Get recent audit trails
            recent_audits = user.audit_trails.order_by('-created_at')[:20]
            
            dashboard_data = {
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'is_premium': user.is_premium,
                    'usage_summary': user.get_usage_summary()
                },
                'recent_datasets': [
                    {
                        'id': ds.id,
                        'name': ds.name,
                        'original_filename': ds.original_filename,
                        'row_count': ds.row_count,
                        'column_count': ds.column_count,
                        'data_quality_score': ds.data_quality_score,
                        'created_at': ds.created_at
                    }
                    for ds in recent_datasets
                ],
                'recent_sessions': [
                    {
                        'id': sess.id,
                        'name': sess.name,
                        'dataset_name': sess.dataset.name,
                        'status': sess.status,
                        'created_at': sess.created_at,
                        'last_activity': sess.last_activity
                    }
                    for sess in recent_sessions
                ],
                'recent_audits': [
                    {
                        'id': audit.id,
                        'action_type': audit.action_type,
                        'resource_type': audit.resource_type,
                        'resource_name': audit.resource_name,
                        'action_description': audit.action_description,
                        'created_at': audit.created_at
                    }
                    for audit in recent_audits
                ],
                'statistics': {
                    'total_datasets': user.datasets.count(),
                    'total_sessions': user.analysis_sessions.count(),
                    'total_audits': user.audit_trails.count(),
                    'storage_used_mb': user.storage_used_mb,
                    'storage_max_mb': user.max_storage_mb,
                    'token_usage_percentage': user.token_usage_percentage
                }
            }
            
            # Cache the data
            cache_instance.set(cache_key, dashboard_data, self.cache_ttls['dashboard_data'])
            self.metrics['cache_misses'] += 1
            self.metrics['cache_sets'] += 1
            
            logger.info(f"Cached dashboard data for user {user_id}")
            return dashboard_data
            
        except User.DoesNotExist:
            return {}
        except Exception as e:
            logger.error(f"Failed to cache dashboard data: {str(e)}")
            return {}
    
    def warm_cache(self, strategy: str, **kwargs) -> Dict[str, Any]:
        """
        Warm cache using predefined strategies
        
        Args:
            strategy: Warming strategy name
            **kwargs: Strategy-specific parameters
            
        Returns:
            Dict with warming results
        """
        try:
            if strategy not in self.warming_strategies:
                return {'success': False, 'error': f'Unknown warming strategy: {strategy}'}
            
            warming_operations = self.warming_strategies[strategy]
            results = {}
            
            for operation in warming_operations:
                if operation == 'user_data' and 'user_id' in kwargs:
                    results[operation] = self.cache_user_data(kwargs['user_id'])
                elif operation == 'user_datasets' and 'user_id' in kwargs:
                    # Cache user datasets
                    user_datasets = User.objects.get(id=kwargs['user_id']).datasets.all()
                    for dataset in user_datasets:
                        self.cache_dataset_info(dataset.id)
                    results[operation] = f"Cached {user_datasets.count()} datasets"
                elif operation == 'dashboard_data' and 'user_id' in kwargs:
                    results[operation] = self.cache_dashboard_data(kwargs['user_id'])
                elif operation == 'dataset_info' and 'dataset_id' in kwargs:
                    results[operation] = self.cache_dataset_info(kwargs['dataset_id'])
                elif operation == 'dataset_columns' and 'dataset_id' in kwargs:
                    # Dataset columns are included in dataset_info
                    results[operation] = "Included in dataset_info"
                elif operation == 'session_data' and 'session_id' in kwargs:
                    # Cache session data
                    session = AnalysisSession.objects.select_related('user', 'dataset').get(id=kwargs['session_id'])
                    session_data = {
                        'id': session.id,
                        'name': session.name,
                        'description': session.description,
                        'status': session.status,
                        'user_id': session.user.id,
                        'dataset_id': session.dataset.id,
                        'created_at': session.created_at
                    }
                    cache_key = self.generate_cache_key(self.key_patterns['session'], session_id=kwargs['session_id'])
                    self.get_cache('sessions').set(cache_key, session_data, self.cache_ttls['session_data'])
                    results[operation] = session_data
                elif operation == 'analysis_results' and 'session_id' in kwargs:
                    results[operation] = self.cache_analysis_results(kwargs['session_id'])
                elif operation == 'session_results' and 'session_id' in kwargs:
                    results[operation] = self.cache_analysis_results(kwargs['session_id'])
            
            self.metrics['cache_warming_operations'] += 1
            
            logger.info(f"Cache warming completed for strategy '{strategy}': {len(results)} operations")
            return {
                'success': True,
                'strategy': strategy,
                'operations': results,
                'operations_count': len(results)
            }
            
        except Exception as e:
            logger.error(f"Cache warming failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'strategy': strategy
            }
    
    def invalidate_cache(self, pattern: str, **kwargs) -> Dict[str, Any]:
        """
        Invalidate cache entries matching pattern
        
        Args:
            pattern: Invalidation pattern name
            **kwargs: Pattern-specific parameters
            
        Returns:
            Dict with invalidation results
        """
        try:
            if pattern not in self.invalidation_patterns:
                return {'success': False, 'error': f'Unknown invalidation pattern: {pattern}'}
            
            patterns = self.invalidation_patterns[pattern]
            invalidated_keys = []
            
            for key_pattern in patterns:
                cache_key = self.generate_cache_key(key_pattern, **kwargs)
                
                # Try to delete from all caches
                for alias in self.cache_aliases.values():
                    cache_instance = self.get_cache(alias)
                    if cache_instance.delete(cache_key):
                        invalidated_keys.append(f"{alias}:{cache_key}")
                
                # Also try wildcard patterns (Redis-specific)
                if '*' in key_pattern:
                    # This would require Redis-specific implementation
                    # For now, we'll log the pattern
                    logger.info(f"Wildcard invalidation pattern: {key_pattern}")
            
            self.metrics['cache_invalidations'] += len(invalidated_keys)
            
            logger.info(f"Cache invalidation completed for pattern '{pattern}': {len(invalidated_keys)} keys")
            return {
                'success': True,
                'pattern': pattern,
                'invalidated_keys': invalidated_keys,
                'keys_count': len(invalidated_keys)
            }
            
        except Exception as e:
            logger.error(f"Cache invalidation failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'pattern': pattern
            }
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive cache statistics
        
        Returns:
            Dict with cache statistics
        """
        try:
            stats = {
                'metrics': self.metrics.copy(),
                'cache_ttls': self.cache_ttls,
                'warming_strategies': list(self.warming_strategies.keys()),
                'invalidation_patterns': list(self.invalidation_patterns.keys()),
                'cache_aliases': list(self.cache_aliases.keys()),
                'timestamp': timezone.now().isoformat()
            }
            
            # Try to get Redis-specific stats if available
            try:
                redis_stats = {}
                for alias in self.cache_aliases.values():
                    cache_instance = self.get_cache(alias)
                    # This would require Redis-specific implementation
                    # For now, we'll add placeholder
                    redis_stats[alias] = {'status': 'connected'}
                
                stats['redis_stats'] = redis_stats
            except Exception as e:
                stats['redis_stats'] = {'error': str(e)}
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get cache stats: {str(e)}")
            return {'error': str(e)}
    
    def clear_all_caches(self) -> Dict[str, Any]:
        """
        Clear all caches
        
        Returns:
            Dict with clearing results
        """
        try:
            cleared_caches = []
            
            for alias in self.cache_aliases.values():
                cache_instance = self.get_cache(alias)
                cache_instance.clear()
                cleared_caches.append(alias)
            
            logger.info(f"Cleared all caches: {cleared_caches}")
            return {
                'success': True,
                'cleared_caches': cleared_caches,
                'caches_count': len(cleared_caches)
            }
            
        except Exception as e:
            logger.error(f"Failed to clear caches: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }


# Global instance for easy access
caching_strategy_service = CachingStrategyService()


# Convenience functions for easy integration
def cache_function_result(ttl: int = 300, cache_alias: str = 'default', key_prefix: str = ''):
    """
    Convenience decorator to cache function results
    
    Args:
        ttl: Time to live in seconds
        cache_alias: Cache alias to use
        key_prefix: Prefix for cache key
        
    Returns:
        Decorator function
    """
    return caching_strategy_service.cache_function_result(ttl, cache_alias, key_prefix)


def warm_cache(strategy: str, **kwargs) -> Dict[str, Any]:
    """
    Convenience function to warm cache
    
    Args:
        strategy: Warming strategy name
        **kwargs: Strategy-specific parameters
        
    Returns:
        Dict with warming results
    """
    return caching_strategy_service.warm_cache(strategy, **kwargs)


def invalidate_cache(pattern: str, **kwargs) -> Dict[str, Any]:
    """
    Convenience function to invalidate cache
    
    Args:
        pattern: Invalidation pattern name
        **kwargs: Pattern-specific parameters
        
    Returns:
        Dict with invalidation results
    """
    return caching_strategy_service.invalidate_cache(pattern, **kwargs)


def cache_user_data(user_id: int, force_refresh: bool = False) -> Dict[str, Any]:
    """
    Convenience function to cache user data
    
    Args:
        user_id: User ID
        force_refresh: Force refresh even if cached
        
    Returns:
        Dict with cached user data
    """
    return caching_strategy_service.cache_user_data(user_id, force_refresh)


def cache_dashboard_data(user_id: int, force_refresh: bool = False) -> Dict[str, Any]:
    """
    Convenience function to cache dashboard data
    
    Args:
        user_id: User ID
        force_refresh: Force refresh even if cached
        
    Returns:
        Dict with cached dashboard data
    """
    return caching_strategy_service.cache_dashboard_data(user_id, force_refresh)
