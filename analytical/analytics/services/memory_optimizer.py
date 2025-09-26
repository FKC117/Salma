"""
Memory Optimization Service

This service provides comprehensive memory management and optimization for the analytical system.
It monitors memory usage, implements lazy loading strategies, manages garbage collection,
and provides memory-efficient data processing for large datasets.
"""

import gc
import psutil
import logging
import threading
import time
from typing import Dict, List, Any, Optional, Tuple, Callable
from datetime import datetime, timedelta
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from django.db import connection
import pandas as pd
import numpy as np
from contextlib import contextmanager
import weakref
from collections import defaultdict

logger = logging.getLogger(__name__)


class MemoryOptimizer:
    """
    Comprehensive memory optimization service for the analytical system
    """
    
    def __init__(self):
        self.memory_thresholds = {
            'critical': 0.90,  # 90% memory usage
            'warning': 0.80,    # 80% memory usage
            'optimal': 0.70    # 70% memory usage
        }
        
        self.cache_cleanup_threshold = 0.75  # Clean cache at 75% memory
        self.gc_threshold = 0.85  # Force garbage collection at 85%
        
        # Memory monitoring
        self.memory_history = []
        self.max_history_size = 100
        self.monitoring_active = False
        self.monitor_thread = None
        
        # Lazy loading registry
        self.lazy_loaders = {}
        self.weak_refs = weakref.WeakValueDictionary()
        
        # Performance metrics
        self.metrics = {
            'memory_cleanups': 0,
            'cache_cleanups': 0,
            'gc_runs': 0,
            'lazy_loads': 0,
            'memory_saves': 0
        }
        
        # Start monitoring if enabled
        if getattr(settings, 'ENABLE_MEMORY_MONITORING', True):
            self.start_monitoring()
    
    def get_memory_usage(self) -> Dict[str, Any]:
        """
        Get current memory usage statistics
        
        Returns:
            Dict with memory usage information
        """
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            system_memory = psutil.virtual_memory()
            
            # Calculate memory usage percentages
            process_memory_percent = memory_info.rss / system_memory.total
            system_memory_percent = system_memory.percent / 100
            
            return {
                'timestamp': timezone.now().isoformat(),
                'process_memory_mb': memory_info.rss / 1024 / 1024,
                'process_memory_percent': process_memory_percent,
                'system_memory_percent': system_memory_percent,
                'available_memory_mb': system_memory.available / 1024 / 1024,
                'total_memory_mb': system_memory.total / 1024 / 1024,
                'memory_status': self._get_memory_status(system_memory_percent),
                'gc_counts': gc.get_count(),
                'cache_size': self._get_cache_size()
            }
            
        except Exception as e:
            logger.error(f"Failed to get memory usage: {str(e)}")
            return {
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }
    
    def _get_memory_status(self, memory_percent: float) -> str:
        """Determine memory status based on usage percentage"""
        if memory_percent >= self.memory_thresholds['critical']:
            return 'CRITICAL'
        elif memory_percent >= self.memory_thresholds['warning']:
            return 'WARNING'
        elif memory_percent >= self.memory_thresholds['optimal']:
            return 'OPTIMAL'
        else:
            return 'LOW'
    
    def _get_cache_size(self) -> Dict[str, Any]:
        """Get cache size information"""
        try:
            # This is a simplified cache size estimation
            # In production, you might want to implement more sophisticated cache monitoring
            return {
                'estimated_size_mb': 0,  # Placeholder
                'key_count': 0,  # Placeholder
                'hit_rate': 0.0  # Placeholder
            }
        except Exception as e:
            logger.warning(f"Failed to get cache size: {str(e)}")
            return {'error': str(e)}
    
    def optimize_memory(self, force: bool = False) -> Dict[str, Any]:
        """
        Perform comprehensive memory optimization
        
        Args:
            force: Force optimization even if memory usage is low
            
        Returns:
            Dict with optimization results
        """
        try:
            memory_usage = self.get_memory_usage()
            current_percent = memory_usage.get('system_memory_percent', 0)
            
            if not force and current_percent < self.memory_thresholds['optimal']:
                return {
                    'optimized': False,
                    'reason': 'Memory usage is optimal',
                    'current_percent': current_percent
                }
            
            optimization_results = {
                'timestamp': timezone.now().isoformat(),
                'before_memory': memory_usage,
                'optimizations_applied': [],
                'memory_saved_mb': 0
            }
            
            # 1. Clean up cache if needed
            if current_percent >= self.cache_cleanup_threshold:
                cache_result = self._cleanup_cache()
                optimization_results['optimizations_applied'].append('cache_cleanup')
                optimization_results['memory_saved_mb'] += cache_result.get('memory_saved_mb', 0)
            
            # 2. Force garbage collection
            if current_percent >= self.gc_threshold:
                gc_result = self._force_garbage_collection()
                optimization_results['optimizations_applied'].append('garbage_collection')
                optimization_results['memory_saved_mb'] += gc_result.get('memory_saved_mb', 0)
            
            # 3. Clean up database connections
            db_result = self._cleanup_database_connections()
            optimization_results['optimizations_applied'].append('database_cleanup')
            
            # 4. Clean up lazy loaders
            lazy_result = self._cleanup_lazy_loaders()
            optimization_results['optimizations_applied'].append('lazy_loader_cleanup')
            
            # Get memory usage after optimization
            optimization_results['after_memory'] = self.get_memory_usage()
            
            # Update metrics
            self.metrics['memory_cleanups'] += 1
            
            logger.info(f"Memory optimization completed: {len(optimization_results['optimizations_applied'])} optimizations applied")
            
            return optimization_results
            
        except Exception as e:
            logger.error(f"Memory optimization failed: {str(e)}")
            return {
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }
    
    def _cleanup_cache(self) -> Dict[str, Any]:
        """Clean up cache to free memory"""
        try:
            # Clear old cache entries
            cache.clear()
            self.metrics['cache_cleanups'] += 1
            
            logger.info("Cache cleanup completed")
            return {
                'memory_saved_mb': 0,  # Placeholder - would need actual measurement
                'cache_cleared': True
            }
            
        except Exception as e:
            logger.error(f"Cache cleanup failed: {str(e)}")
            return {'error': str(e)}
    
    def _force_garbage_collection(self) -> Dict[str, Any]:
        """Force garbage collection to free memory"""
        try:
            before_count = gc.get_count()
            collected = gc.collect()
            after_count = gc.get_count()
            
            self.metrics['gc_runs'] += 1
            
            logger.info(f"Garbage collection completed: {collected} objects collected")
            return {
                'memory_saved_mb': 0,  # Placeholder - would need actual measurement
                'objects_collected': collected,
                'before_count': before_count,
                'after_count': after_count
            }
            
        except Exception as e:
            logger.error(f"Garbage collection failed: {str(e)}")
            return {'error': str(e)}
    
    def _cleanup_database_connections(self) -> Dict[str, Any]:
        """Clean up database connections"""
        try:
            # Close idle database connections
            connection.close()
            
            logger.info("Database connections cleaned up")
            return {'connections_closed': True}
            
        except Exception as e:
            logger.error(f"Database cleanup failed: {str(e)}")
            return {'error': str(e)}
    
    def _cleanup_lazy_loaders(self) -> Dict[str, Any]:
        """Clean up unused lazy loaders"""
        try:
            cleaned_count = 0
            
            # Remove unused lazy loaders
            unused_keys = []
            for key, loader in self.lazy_loaders.items():
                if not self.weak_refs.get(key):
                    unused_keys.append(key)
                    cleaned_count += 1
            
            for key in unused_keys:
                del self.lazy_loaders[key]
            
            logger.info(f"Lazy loader cleanup completed: {cleaned_count} loaders removed")
            return {
                'loaders_removed': cleaned_count,
                'remaining_loaders': len(self.lazy_loaders)
            }
            
        except Exception as e:
            logger.error(f"Lazy loader cleanup failed: {str(e)}")
            return {'error': str(e)}
    
    def register_lazy_loader(self, key: str, loader_func: Callable, *args, **kwargs) -> str:
        """
        Register a lazy loader for memory-efficient data loading
        
        Args:
            key: Unique identifier for the loader
            loader_func: Function to call when data is needed
            *args: Arguments for the loader function
            **kwargs: Keyword arguments for the loader function
            
        Returns:
            Loader key for later retrieval
        """
        try:
            self.lazy_loaders[key] = {
                'func': loader_func,
                'args': args,
                'kwargs': kwargs,
                'created_at': timezone.now(),
                'access_count': 0
            }
            
            logger.debug(f"Lazy loader registered: {key}")
            return key
            
        except Exception as e:
            logger.error(f"Failed to register lazy loader: {str(e)}")
            return ""
    
    def load_lazy_data(self, key: str) -> Any:
        """
        Load data using a registered lazy loader
        
        Args:
            key: Loader key
            
        Returns:
            Loaded data or None if loader not found
        """
        try:
            if key not in self.lazy_loaders:
                logger.warning(f"Lazy loader not found: {key}")
                return None
            
            loader = self.lazy_loaders[key]
            loader['access_count'] += 1
            
            # Execute the loader function
            data = loader['func'](*loader['args'], **loader['kwargs'])
            
            self.metrics['lazy_loads'] += 1
            logger.debug(f"Lazy data loaded: {key}")
            
            return data
            
        except Exception as e:
            logger.error(f"Failed to load lazy data: {str(e)}")
            return None
    
    def unregister_lazy_loader(self, key: str) -> bool:
        """
        Unregister a lazy loader
        
        Args:
            key: Loader key
            
        Returns:
            True if successfully removed, False otherwise
        """
        try:
            if key in self.lazy_loaders:
                del self.lazy_loaders[key]
                logger.debug(f"Lazy loader unregistered: {key}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to unregister lazy loader: {str(e)}")
            return False
    
    @contextmanager
    def memory_efficient_context(self, context_name: str = "default"):
        """
        Context manager for memory-efficient operations
        
        Args:
            context_name: Name for the context (for logging)
        """
        start_memory = self.get_memory_usage()
        
        try:
            logger.debug(f"Starting memory-efficient context: {context_name}")
            yield self
            
        finally:
            end_memory = self.get_memory_usage()
            memory_diff = end_memory.get('process_memory_mb', 0) - start_memory.get('process_memory_mb', 0)
            
            if memory_diff > 10:  # More than 10MB increase
                logger.warning(f"Memory increase in context '{context_name}': {memory_diff:.2f}MB")
                # Auto-optimize if memory increased significantly
                self.optimize_memory()
    
    def process_large_dataset(self, dataset_path: str, chunk_size: int = 10000) -> pd.DataFrame:
        """
        Process large datasets in memory-efficient chunks
        
        Args:
            dataset_path: Path to the dataset file
            chunk_size: Size of each chunk to process
            
        Returns:
            Processed DataFrame
        """
        try:
            logger.info(f"Processing large dataset: {dataset_path}")
            
            # Read dataset in chunks
            chunks = []
            for chunk in pd.read_csv(dataset_path, chunksize=chunk_size):
                # Process chunk
                processed_chunk = self._process_chunk(chunk)
                chunks.append(processed_chunk)
                
                # Optimize memory after each chunk
                if len(chunks) % 10 == 0:  # Every 10 chunks
                    self.optimize_memory()
            
            # Combine chunks
            result = pd.concat(chunks, ignore_index=True)
            
            logger.info(f"Dataset processing completed: {len(result)} rows")
            return result
            
        except Exception as e:
            logger.error(f"Large dataset processing failed: {str(e)}")
            raise
    
    def _process_chunk(self, chunk: pd.DataFrame) -> pd.DataFrame:
        """
        Process a single chunk of data
        
        Args:
            chunk: DataFrame chunk to process
            
        Returns:
            Processed chunk
        """
        try:
            # Basic processing - remove nulls, optimize dtypes
            chunk = chunk.dropna()
            
            # Optimize data types
            for col in chunk.select_dtypes(include=['object']).columns:
                chunk[col] = chunk[col].astype('category')
            
            return chunk
            
        except Exception as e:
            logger.error(f"Chunk processing failed: {str(e)}")
            return chunk
    
    def start_monitoring(self) -> bool:
        """Start memory monitoring in background thread"""
        try:
            if self.monitoring_active:
                logger.warning("Memory monitoring is already active")
                return False
            
            self.monitoring_active = True
            self.monitor_thread = threading.Thread(target=self._monitor_memory, daemon=True)
            self.monitor_thread.start()
            
            logger.info("Memory monitoring started")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start memory monitoring: {str(e)}")
            return False
    
    def stop_monitoring(self) -> bool:
        """Stop memory monitoring"""
        try:
            self.monitoring_active = False
            if self.monitor_thread:
                self.monitor_thread.join(timeout=5)
            
            logger.info("Memory monitoring stopped")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop memory monitoring: {str(e)}")
            return False
    
    def _monitor_memory(self):
        """Background memory monitoring thread"""
        while self.monitoring_active:
            try:
                memory_usage = self.get_memory_usage()
                self.memory_history.append(memory_usage)
                
                # Keep only recent history
                if len(self.memory_history) > self.max_history_size:
                    self.memory_history = self.memory_history[-self.max_history_size:]
                
                # Auto-optimize if memory usage is high
                memory_percent = memory_usage.get('system_memory_percent', 0)
                if memory_percent >= self.memory_thresholds['warning']:
                    logger.warning(f"High memory usage detected: {memory_percent:.2%}")
                    self.optimize_memory()
                
                # Sleep for monitoring interval
                time.sleep(getattr(settings, 'MEMORY_MONITORING_INTERVAL', 30))
                
            except Exception as e:
                logger.error(f"Memory monitoring error: {str(e)}")
                time.sleep(60)  # Wait longer on error
    
    def get_memory_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive memory usage report
        
        Returns:
            Dict with memory report
        """
        try:
            current_usage = self.get_memory_usage()
            
            return {
                'timestamp': timezone.now().isoformat(),
                'current_usage': current_usage,
                'memory_history': self.memory_history[-10:],  # Last 10 measurements
                'metrics': self.metrics.copy(),
                'lazy_loaders_count': len(self.lazy_loaders),
                'memory_thresholds': self.memory_thresholds,
                'monitoring_active': self.monitoring_active,
                'recommendations': self._get_memory_recommendations(current_usage)
            }
            
        except Exception as e:
            logger.error(f"Failed to generate memory report: {str(e)}")
            return {'error': str(e)}
    
    def _get_memory_recommendations(self, memory_usage: Dict[str, Any]) -> List[str]:
        """Generate memory optimization recommendations"""
        recommendations = []
        
        memory_percent = memory_usage.get('system_memory_percent', 0)
        
        if memory_percent >= self.memory_thresholds['critical']:
            recommendations.append("CRITICAL: Immediate memory optimization required")
            recommendations.append("Consider reducing dataset size or processing in smaller chunks")
        
        elif memory_percent >= self.memory_thresholds['warning']:
            recommendations.append("WARNING: Memory usage is high, consider optimization")
            recommendations.append("Enable lazy loading for large datasets")
        
        elif memory_percent >= self.memory_thresholds['optimal']:
            recommendations.append("Memory usage is approaching optimal levels")
            recommendations.append("Consider proactive optimization")
        
        else:
            recommendations.append("Memory usage is optimal")
        
        # Check lazy loader count
        if len(self.lazy_loaders) > 100:
            recommendations.append("Consider cleaning up unused lazy loaders")
        
        return recommendations
    
    def cleanup_on_exit(self):
        """Cleanup method to call on application exit"""
        try:
            self.stop_monitoring()
            self.lazy_loaders.clear()
            self.weak_refs.clear()
            
            logger.info("Memory optimizer cleanup completed")
            
        except Exception as e:
            logger.error(f"Memory optimizer cleanup failed: {str(e)}")


# Global instance for easy access
memory_optimizer = MemoryOptimizer()


# Convenience functions for easy integration
def optimize_memory(force: bool = False) -> Dict[str, Any]:
    """
    Convenience function to optimize memory
    
    Args:
        force: Force optimization even if memory usage is low
        
    Returns:
        Optimization results
    """
    return memory_optimizer.optimize_memory(force)


def get_memory_usage() -> Dict[str, Any]:
    """
    Convenience function to get memory usage
    
    Returns:
        Memory usage information
    """
    return memory_optimizer.get_memory_usage()


def register_lazy_loader(key: str, loader_func: Callable, *args, **kwargs) -> str:
    """
    Convenience function to register a lazy loader
    
    Args:
        key: Unique identifier for the loader
        loader_func: Function to call when data is needed
        *args: Arguments for the loader function
        **kwargs: Keyword arguments for the loader function
        
    Returns:
        Loader key for later retrieval
    """
    return memory_optimizer.register_lazy_loader(key, loader_func, *args, **kwargs)


def load_lazy_data(key: str) -> Any:
    """
    Convenience function to load lazy data
    
    Args:
        key: Loader key
        
    Returns:
        Loaded data or None if loader not found
    """
    return memory_optimizer.load_lazy_data(key)
