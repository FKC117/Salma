"""
Background Monitoring and Cleanup Service

This service provides comprehensive background monitoring, cleanup, and maintenance
for the analytical system. It handles automated cleanup tasks, performance monitoring,
resource management, and system health checks.
"""

import os
import time
import logging
import threading
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
from django.db import connection, transaction
from django.core.cache import cache
from django.core.management import call_command
from pathlib import Path
import psutil
import gc

from analytics.models import (
    User, Dataset, AnalysisSession, AnalysisResult, ChatMessage,
    AgentRun, GeneratedImage, AuditTrail, VectorNote
)
from analytics.services.memory_optimizer import memory_optimizer
from analytics.services.image_compression import image_compression_service
from analytics.services.caching_strategy import caching_strategy_service

logger = logging.getLogger(__name__)


class BackgroundMonitoringService:
    """
    Comprehensive background monitoring and cleanup service
    """
    
    def __init__(self):
        self.monitoring_active = False
        self.monitor_thread = None
        self.cleanup_thread = None
        
        # Monitoring intervals (in seconds)
        self.intervals = {
            'system_monitoring': getattr(settings, 'SYSTEM_MONITORING_INTERVAL', 60),
            'cleanup_tasks': getattr(settings, 'CLEANUP_TASKS_INTERVAL', 3600),  # 1 hour
            'performance_check': getattr(settings, 'PERFORMANCE_CHECK_INTERVAL', 300),  # 5 minutes
            'health_check': getattr(settings, 'HEALTH_CHECK_INTERVAL', 1800),  # 30 minutes
        }
        
        # Cleanup thresholds
        self.cleanup_thresholds = {
            'old_sessions_days': getattr(settings, 'OLD_SESSIONS_CLEANUP_DAYS', 90),
            'old_audit_trails_days': getattr(settings, 'OLD_AUDIT_TRAILS_CLEANUP_DAYS', 365),
            'old_images_days': getattr(settings, 'OLD_IMAGES_CLEANUP_DAYS', 180),
            'old_vector_notes_days': getattr(settings, 'OLD_VECTOR_NOTES_CLEANUP_DAYS', 365),
            'max_file_size_mb': getattr(settings, 'MAX_FILE_SIZE_MB', 100),
            'max_cache_size_mb': getattr(settings, 'MAX_CACHE_SIZE_MB', 500),
        }
        
        # Performance thresholds
        self.performance_thresholds = {
            'memory_usage_percent': 85,
            'cpu_usage_percent': 80,
            'disk_usage_percent': 90,
            'response_time_ms': 5000,
            'database_query_time_ms': 1000,
        }
        
        # Monitoring metrics
        self.metrics = {
            'monitoring_cycles': 0,
            'cleanup_operations': 0,
            'performance_alerts': 0,
            'health_checks': 0,
            'errors_detected': 0,
            'last_monitoring_time': None,
            'last_cleanup_time': None,
            'last_health_check': None,
        }
        
        # Alert handlers
        self.alert_handlers = []
        
        # Start monitoring if enabled
        if getattr(settings, 'ENABLE_BACKGROUND_MONITORING', True):
            self.start_monitoring()
    
    def start_monitoring(self) -> bool:
        """Start background monitoring"""
        try:
            if self.monitoring_active:
                logger.warning("Background monitoring is already active")
                return False
            
            self.monitoring_active = True
            
            # Start system monitoring thread
            self.monitor_thread = threading.Thread(
                target=self._monitoring_loop,
                daemon=True,
                name="BackgroundMonitoring"
            )
            self.monitor_thread.start()
            
            # Start cleanup thread
            self.cleanup_thread = threading.Thread(
                target=self._cleanup_loop,
                daemon=True,
                name="BackgroundCleanup"
            )
            self.cleanup_thread.start()
            
            logger.info("Background monitoring started")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start background monitoring: {str(e)}")
            return False
    
    def stop_monitoring(self) -> bool:
        """Stop background monitoring"""
        try:
            self.monitoring_active = False
            
            if self.monitor_thread:
                self.monitor_thread.join(timeout=10)
            
            if self.cleanup_thread:
                self.cleanup_thread.join(timeout=10)
            
            logger.info("Background monitoring stopped")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop background monitoring: {str(e)}")
            return False
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                start_time = time.time()
                
                # System monitoring
                self._monitor_system_resources()
                
                # Performance monitoring
                self._monitor_performance()
                
                # Health checks
                self._perform_health_checks()
                
                self.metrics['monitoring_cycles'] += 1
                self.metrics['last_monitoring_time'] = timezone.now()
                
                cycle_time = time.time() - start_time
                logger.debug(f"Monitoring cycle completed in {cycle_time:.2f}s")
                
                # Sleep until next monitoring cycle
                time.sleep(self.intervals['system_monitoring'])
                
            except Exception as e:
                logger.error(f"Monitoring loop error: {str(e)}")
                self.metrics['errors_detected'] += 1
                time.sleep(60)  # Wait longer on error
    
    def _cleanup_loop(self):
        """Main cleanup loop"""
        while self.monitoring_active:
            try:
                start_time = time.time()
                
                # Database cleanup
                self._cleanup_old_data()
                
                # File cleanup
                self._cleanup_old_files()
                
                # Cache cleanup
                self._cleanup_cache()
                
                # Image cleanup
                self._cleanup_images()
                
                self.metrics['cleanup_operations'] += 1
                self.metrics['last_cleanup_time'] = timezone.now()
                
                cleanup_time = time.time() - start_time
                logger.info(f"Cleanup cycle completed in {cleanup_time:.2f}s")
                
                # Sleep until next cleanup cycle
                time.sleep(self.intervals['cleanup_tasks'])
                
            except Exception as e:
                logger.error(f"Cleanup loop error: {str(e)}")
                self.metrics['errors_detected'] += 1
                time.sleep(300)  # Wait 5 minutes on error
    
    def _monitor_system_resources(self):
        """Monitor system resource usage"""
        try:
            # Memory usage
            memory_usage = memory_optimizer.get_memory_usage()
            memory_percent = memory_usage.get('system_memory_percent', 0)
            
            if memory_percent > self.performance_thresholds['memory_usage_percent']:
                self._trigger_alert('high_memory_usage', {
                    'memory_percent': memory_percent,
                    'threshold': self.performance_thresholds['memory_usage_percent']
                })
                
                # Auto-optimize memory
                memory_optimizer.optimize_memory(force=True)
            
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > self.performance_thresholds['cpu_usage_percent']:
                self._trigger_alert('high_cpu_usage', {
                    'cpu_percent': cpu_percent,
                    'threshold': self.performance_thresholds['cpu_usage_percent']
                })
            
            # Disk usage
            disk_usage = psutil.disk_usage('/')
            disk_percent = (disk_usage.used / disk_usage.total) * 100
            
            if disk_percent > self.performance_thresholds['disk_usage_percent']:
                self._trigger_alert('high_disk_usage', {
                    'disk_percent': disk_percent,
                    'threshold': self.performance_thresholds['disk_usage_percent']
                })
                
                # Trigger cleanup
                self._cleanup_old_files()
            
        except Exception as e:
            logger.error(f"System resource monitoring failed: {str(e)}")
    
    def _monitor_performance(self):
        """Monitor application performance"""
        try:
            # Database performance
            start_time = time.time()
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            db_response_time = (time.time() - start_time) * 1000
            
            if db_response_time > self.performance_thresholds['database_query_time_ms']:
                self._trigger_alert('slow_database', {
                    'response_time_ms': db_response_time,
                    'threshold': self.performance_thresholds['database_query_time_ms']
                })
            
            # Cache performance
            cache_stats = caching_strategy_service.get_cache_stats()
            cache_hit_rate = cache_stats.get('metrics', {}).get('cache_hits', 0) / max(
                cache_stats.get('metrics', {}).get('cache_hits', 0) + 
                cache_stats.get('metrics', {}).get('cache_misses', 1), 1
            )
            
            if cache_hit_rate < 0.7:  # Less than 70% hit rate
                self._trigger_alert('low_cache_hit_rate', {
                    'hit_rate': cache_hit_rate,
                    'threshold': 0.7
                })
            
        except Exception as e:
            logger.error(f"Performance monitoring failed: {str(e)}")
    
    def _perform_health_checks(self):
        """Perform system health checks"""
        try:
            health_status = {
                'timestamp': timezone.now().isoformat(),
                'checks': {}
            }
            
            # Database connectivity
            try:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
                health_status['checks']['database'] = 'healthy'
            except Exception as e:
                health_status['checks']['database'] = f'unhealthy: {str(e)}'
                self._trigger_alert('database_unhealthy', {'error': str(e)})
            
            # Cache connectivity
            try:
                cache.set('health_check', 'ok', 10)
                cache.get('health_check')
                health_status['checks']['cache'] = 'healthy'
            except Exception as e:
                health_status['checks']['cache'] = f'unhealthy: {str(e)}'
                self._trigger_alert('cache_unhealthy', {'error': str(e)})
            
            # File system
            try:
                media_root = Path(settings.MEDIA_ROOT)
                if media_root.exists() and media_root.is_dir():
                    health_status['checks']['filesystem'] = 'healthy'
                else:
                    health_status['checks']['filesystem'] = 'unhealthy: media root not accessible'
                    self._trigger_alert('filesystem_unhealthy', {'path': str(media_root)})
            except Exception as e:
                health_status['checks']['filesystem'] = f'unhealthy: {str(e)}'
                self._trigger_alert('filesystem_unhealthy', {'error': str(e)})
            
            # Model counts (basic data integrity check)
            try:
                model_counts = {
                    'users': User.objects.count(),
                    'datasets': Dataset.objects.count(),
                    'sessions': AnalysisSession.objects.count(),
                    'results': AnalysisResult.objects.count(),
                    'images': GeneratedImage.objects.count(),
                    'audits': AuditTrail.objects.count()
                }
                health_status['checks']['data_integrity'] = 'healthy'
                health_status['model_counts'] = model_counts
            except Exception as e:
                health_status['checks']['data_integrity'] = f'unhealthy: {str(e)}'
                self._trigger_alert('data_integrity_unhealthy', {'error': str(e)})
            
            self.metrics['health_checks'] += 1
            self.metrics['last_health_check'] = timezone.now()
            
            # Log health status
            unhealthy_checks = [k for k, v in health_status['checks'].items() if 'unhealthy' in v]
            if unhealthy_checks:
                logger.warning(f"Health check found issues: {unhealthy_checks}")
            else:
                logger.debug("Health check passed")
            
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            self._trigger_alert('health_check_failed', {'error': str(e)})
    
    def _cleanup_old_data(self):
        """Clean up old data from database"""
        try:
            cleanup_results = {}
            
            # Clean up old sessions
            cutoff_date = timezone.now() - timedelta(days=self.cleanup_thresholds['old_sessions_days'])
            old_sessions = AnalysisSession.objects.filter(created_at__lt=cutoff_date)
            old_sessions_count = old_sessions.count()
            
            if old_sessions_count > 0:
                # Delete related data first
                for session in old_sessions:
                    AnalysisResult.objects.filter(session=session).delete()
                    ChatMessage.objects.filter(session=session).delete()
                    AgentRun.objects.filter(session=session).delete()
                
                old_sessions.delete()
                cleanup_results['old_sessions'] = old_sessions_count
            
            # Clean up old audit trails
            cutoff_date = timezone.now() - timedelta(days=self.cleanup_thresholds['old_audit_trails_days'])
            old_audits = AuditTrail.objects.filter(created_at__lt=cutoff_date)
            old_audits_count = old_audits.count()
            
            if old_audits_count > 0:
                old_audits.delete()
                cleanup_results['old_audits'] = old_audits_count
            
            # Clean up old vector notes
            cutoff_date = timezone.now() - timedelta(days=self.cleanup_thresholds['old_vector_notes_days'])
            old_notes = VectorNote.objects.filter(created_at__lt=cutoff_date)
            old_notes_count = old_notes.count()
            
            if old_notes_count > 0:
                old_notes.delete()
                cleanup_results['old_vector_notes'] = old_notes_count
            
            if cleanup_results:
                logger.info(f"Database cleanup completed: {cleanup_results}")
            
        except Exception as e:
            logger.error(f"Database cleanup failed: {str(e)}")
    
    def _cleanup_old_files(self):
        """Clean up old files"""
        try:
            cleanup_results = {}
            
            # Clean up old images
            image_cleanup_result = image_compression_service.cleanup_old_compressed_images(
                self.cleanup_thresholds['old_images_days']
            )
            
            if image_cleanup_result['success']:
                cleanup_results['images'] = image_cleanup_result['cleaned_count']
            
            # Clean up old dataset files (if any)
            media_root = Path(settings.MEDIA_ROOT)
            datasets_dir = media_root / 'datasets'
            
            if datasets_dir.exists():
                cutoff_time = timezone.now() - timedelta(days=self.cleanup_thresholds['old_images_days'])
                cleaned_files = 0
                
                for file_path in datasets_dir.glob('*'):
                    if file_path.is_file():
                        file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                        if file_time.replace(tzinfo=timezone.get_current_timezone()) < cutoff_time:
                            file_path.unlink()
                            cleaned_files += 1
                
                if cleaned_files > 0:
                    cleanup_results['dataset_files'] = cleaned_files
            
            if cleanup_results:
                logger.info(f"File cleanup completed: {cleanup_results}")
            
        except Exception as e:
            logger.error(f"File cleanup failed: {str(e)}")
    
    def _cleanup_cache(self):
        """Clean up cache"""
        try:
            # Clear old cache entries
            cache_stats = caching_strategy_service.get_cache_stats()
            
            # If cache is getting too large, clear some entries
            if cache_stats.get('metrics', {}).get('total_bytes_cached', 0) > self.cleanup_thresholds['max_cache_size_mb'] * 1024 * 1024:
                logger.info("Cache size exceeded threshold, clearing old entries")
                cache.clear()
            
        except Exception as e:
            logger.error(f"Cache cleanup failed: {str(e)}")
    
    def _cleanup_images(self):
        """Clean up old images"""
        try:
            # Clean up old generated images
            cutoff_date = timezone.now() - timedelta(days=self.cleanup_thresholds['old_images_days'])
            old_images = GeneratedImage.objects.filter(created_at__lt=cutoff_date)
            
            for image in old_images:
                # Delete file if it exists
                if os.path.exists(image.file_path):
                    os.unlink(image.file_path)
                
                # Delete database record
                image.delete()
            
            if old_images.count() > 0:
                logger.info(f"Cleaned up {old_images.count()} old images")
            
        except Exception as e:
            logger.error(f"Image cleanup failed: {str(e)}")
    
    def _trigger_alert(self, alert_type: str, data: Dict[str, Any]):
        """Trigger an alert"""
        try:
            self.metrics['performance_alerts'] += 1
            
            alert_data = {
                'type': alert_type,
                'timestamp': timezone.now().isoformat(),
                'data': data
            }
            
            logger.warning(f"Alert triggered: {alert_type} - {data}")
            
            # Call registered alert handlers
            for handler in self.alert_handlers:
                try:
                    handler(alert_data)
                except Exception as e:
                    logger.error(f"Alert handler failed: {str(e)}")
            
        except Exception as e:
            logger.error(f"Alert triggering failed: {str(e)}")
    
    def register_alert_handler(self, handler: Callable[[Dict[str, Any]], None]):
        """Register an alert handler"""
        self.alert_handlers.append(handler)
        logger.info(f"Alert handler registered: {handler.__name__}")
    
    def get_monitoring_stats(self) -> Dict[str, Any]:
        """Get comprehensive monitoring statistics"""
        try:
            # Get system metrics
            memory_usage = memory_optimizer.get_memory_usage()
            cache_stats = caching_strategy_service.get_cache_stats()
            
            return {
                'monitoring_active': self.monitoring_active,
                'metrics': self.metrics.copy(),
                'intervals': self.intervals,
                'thresholds': self.performance_thresholds,
                'cleanup_thresholds': self.cleanup_thresholds,
                'system_resources': {
                    'memory': memory_usage,
                    'cpu_percent': psutil.cpu_percent(),
                    'disk_usage': psutil.disk_usage('/').percent
                },
                'cache_stats': cache_stats,
                'alert_handlers_count': len(self.alert_handlers),
                'timestamp': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get monitoring stats: {str(e)}")
            return {'error': str(e)}
    
    def run_manual_cleanup(self) -> Dict[str, Any]:
        """Run manual cleanup operations"""
        try:
            start_time = time.time()
            results = {}
            
            # Database cleanup
            self._cleanup_old_data()
            results['database_cleanup'] = 'completed'
            
            # File cleanup
            self._cleanup_old_files()
            results['file_cleanup'] = 'completed'
            
            # Cache cleanup
            self._cleanup_cache()
            results['cache_cleanup'] = 'completed'
            
            # Image cleanup
            self._cleanup_images()
            results['image_cleanup'] = 'completed'
            
            # Memory optimization
            memory_optimizer.optimize_memory(force=True)
            results['memory_optimization'] = 'completed'
            
            execution_time = time.time() - start_time
            
            logger.info(f"Manual cleanup completed in {execution_time:.2f}s")
            
            return {
                'success': True,
                'results': results,
                'execution_time': execution_time,
                'timestamp': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Manual cleanup failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }


# Global instance for easy access
background_monitoring_service = BackgroundMonitoringService()


# Convenience functions for easy integration
def start_background_monitoring() -> bool:
    """
    Convenience function to start background monitoring
    
    Returns:
        True if successful
    """
    return background_monitoring_service.start_monitoring()


def stop_background_monitoring() -> bool:
    """
    Convenience function to stop background monitoring
    
    Returns:
        True if successful
    """
    return background_monitoring_service.stop_monitoring()


def get_monitoring_stats() -> Dict[str, Any]:
    """
    Convenience function to get monitoring statistics
    
    Returns:
        Dict with monitoring statistics
    """
    return background_monitoring_service.get_monitoring_stats()


def run_manual_cleanup() -> Dict[str, Any]:
    """
    Convenience function to run manual cleanup
    
    Returns:
        Dict with cleanup results
    """
    return background_monitoring_service.run_manual_cleanup()


def register_alert_handler(handler: Callable[[Dict[str, Any]], None]):
    """
    Convenience function to register an alert handler
    
    Args:
        handler: Alert handler function
    """
    background_monitoring_service.register_alert_handler(handler)
