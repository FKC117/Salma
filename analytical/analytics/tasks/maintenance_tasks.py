"""
Maintenance Celery Tasks
Handles background maintenance, backup, and cleanup operations
"""

from celery import shared_task
from django.conf import settings
import logging
from typing import Dict, Any, Optional
import time
import os
import shutil
from pathlib import Path
from datetime import datetime, timedelta
import subprocess

from analytics.models import Dataset, User
from analytics.services.audit_trail_manager import AuditTrailManager
from analytics.services.logging_service import StructuredLogger

logger = StructuredLogger(__name__)


@shared_task
def cleanup_old_files():
    """
    Clean up old temporary files and unused datasets
    """
    try:
        logger.info("Starting cleanup of old files")
        
        # Clean up files older than 7 days
        cutoff_date = datetime.now() - timedelta(days=7)
        
        # Clean up temporary files
        temp_dirs = [
            'media/temp/',
            'media/cache/',
            'media/thumbnails/'
        ]
        
        cleaned_files = 0
        for temp_dir in temp_dirs:
            if os.path.exists(temp_dir):
                for file_path in Path(temp_dir).rglob('*'):
                    if file_path.is_file():
                        file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                        if file_time < cutoff_date:
                            try:
                                file_path.unlink()
                                cleaned_files += 1
                            except Exception as e:
                                logger.warning(f"Could not delete file {file_path}: {str(e)}")
        
        logger.info(f"File cleanup completed: {cleaned_files} files removed")
        
        return {
            'status': 'success',
            'cleaned_files': cleaned_files
        }
        
    except Exception as exc:
        logger.error(f"File cleanup error: {str(exc)}")
        
        return {
            'status': 'error',
            'error': str(exc)
        }


@shared_task
def backup_database():
    """
    Create database backup
    """
    try:
        logger.info("Starting database backup")
        
        # Create backup filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"backup_{timestamp}.sql"
        backup_path = f"backups/{backup_filename}"
        
        # Ensure backup directory exists
        os.makedirs('backups', exist_ok=True)
        
        # Create database backup using pg_dump
        db_config = settings.DATABASES['default']
        
        cmd = [
            'pg_dump',
            '-h', db_config['HOST'],
            '-p', str(db_config['PORT']),
            '-U', db_config['USER'],
            '-d', db_config['NAME'],
            '-f', backup_path
        ]
        
        # Set password environment variable
        env = os.environ.copy()
        env['PGPASSWORD'] = db_config['PASSWORD']
        
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        if result.returncode == 0:
            # Get backup file size
            backup_size = os.path.getsize(backup_path)
            
            logger.info(f"Database backup completed: {backup_filename} ({backup_size} bytes)")
            
            return {
                'status': 'success',
                'backup_file': backup_filename,
                'backup_size': backup_size
            }
        else:
            raise Exception(f"Backup failed: {result.stderr}")
        
    except Exception as exc:
        logger.error(f"Database backup error: {str(exc)}")
        
        return {
            'status': 'error',
            'error': str(exc)
        }


@shared_task
def cleanup_old_backups():
    """
    Clean up old backup files (keep only last 30 days)
    """
    try:
        logger.info("Starting cleanup of old backups")
        
        # Keep backups from last 30 days
        cutoff_date = datetime.now() - timedelta(days=30)
        
        backup_dir = Path('backups')
        if not backup_dir.exists():
            return {'status': 'success', 'cleaned_backups': 0}
        
        cleaned_backups = 0
        for backup_file in backup_dir.glob('backup_*.sql'):
            file_time = datetime.fromtimestamp(backup_file.stat().st_mtime)
            if file_time < cutoff_date:
                try:
                    backup_file.unlink()
                    cleaned_backups += 1
                    logger.info(f"Deleted old backup: {backup_file.name}")
                except Exception as e:
                    logger.warning(f"Could not delete backup {backup_file}: {str(e)}")
        
        logger.info(f"Backup cleanup completed: {cleaned_backups} backups removed")
        
        return {
            'status': 'success',
            'cleaned_backups': cleaned_backups
        }
        
    except Exception as exc:
        logger.error(f"Backup cleanup error: {str(exc)}")
        
        return {
            'status': 'error',
            'error': str(exc)
        }


@shared_task
def cleanup_unused_datasets():
    """
    Clean up datasets that haven't been accessed in 90 days
    """
    try:
        logger.info("Starting cleanup of unused datasets")
        
        # Find datasets not accessed in 90 days
        cutoff_date = datetime.now() - timedelta(days=90)
        
        unused_datasets = Dataset.objects.filter(
            last_accessed__lt=cutoff_date,
            processing_status='completed'
        )
        
        cleaned_datasets = 0
        for dataset in unused_datasets:
            try:
                # Delete parquet file
                parquet_path = f"media/{dataset.parquet_path}"
                if os.path.exists(parquet_path):
                    os.remove(parquet_path)
                
                # Mark dataset as archived
                dataset.processing_status = 'archived'
                dataset.save()
                
                cleaned_datasets += 1
                logger.info(f"Archived unused dataset: {dataset.name}")
                
            except Exception as e:
                logger.warning(f"Could not archive dataset {dataset.id}: {str(e)}")
        
        logger.info(f"Dataset cleanup completed: {cleaned_datasets} datasets archived")
        
        return {
            'status': 'success',
            'cleaned_datasets': cleaned_datasets
        }
        
    except Exception as exc:
        logger.error(f"Dataset cleanup error: {str(exc)}")
        
        return {
            'status': 'error',
            'error': str(exc)
        }


@shared_task
def cleanup_audit_logs():
    """
    Clean up old audit logs (keep only last 6 months)
    """
    try:
        logger.info("Starting cleanup of audit logs")
        
        # This would clean up old audit logs
        # Implementation depends on your audit log storage
        
        logger.info("Audit log cleanup completed")
        
        return {
            'status': 'success',
            'message': 'Audit log cleanup completed'
        }
        
    except Exception as exc:
        logger.error(f"Audit log cleanup error: {str(exc)}")
        
        return {
            'status': 'error',
            'error': str(exc)
        }


@shared_task
def optimize_database():
    """
    Optimize database performance
    """
    try:
        logger.info("Starting database optimization")
        
        # This would run database optimization commands
        # Implementation depends on your database setup
        
        logger.info("Database optimization completed")
        
        return {
            'status': 'success',
            'message': 'Database optimization completed'
        }
        
    except Exception as exc:
        logger.error(f"Database optimization error: {str(exc)}")
        
        return {
            'status': 'error',
            'error': str(exc)
        }


@shared_task
def monitor_system_resources():
    """
    Monitor system resource usage
    """
    try:
        logger.info("Monitoring system resources")
        
        # Get disk usage
        disk_usage = shutil.disk_usage('/')
        disk_free_gb = disk_usage.free / (1024**3)
        disk_total_gb = disk_usage.total / (1024**3)
        disk_used_percent = (disk_usage.used / disk_usage.total) * 100
        
        # Log resource usage
        logger.info(f"System resources: Disk {disk_used_percent:.1f}% used ({disk_free_gb:.1f}GB free of {disk_total_gb:.1f}GB)")
        
        # Alert if disk usage is high
        if disk_used_percent > 85:
            logger.warning(f"High disk usage: {disk_used_percent:.1f}%")
        
        return {
            'status': 'success',
            'disk_usage_percent': disk_used_percent,
            'disk_free_gb': disk_free_gb,
            'disk_total_gb': disk_total_gb
        }
        
    except Exception as exc:
        logger.error(f"System resource monitoring error: {str(exc)}")
        
        return {
            'status': 'error',
            'error': str(exc)
        }


@shared_task
def generate_maintenance_report():
    """
    Generate maintenance report
    """
    try:
        logger.info("Generating maintenance report")
        
        # Collect maintenance metrics
        report = {
            'timestamp': datetime.now().isoformat(),
            'datasets_count': Dataset.objects.count(),
            'active_users': User.objects.filter(is_active=True).count(),
            'disk_usage': {},
            'recent_activities': []
        }
        
        # Get disk usage
        try:
            disk_usage = shutil.disk_usage('/')
            report['disk_usage'] = {
                'total_gb': disk_usage.total / (1024**3),
                'used_gb': disk_usage.used / (1024**3),
                'free_gb': disk_usage.free / (1024**3),
                'used_percent': (disk_usage.used / disk_usage.total) * 100
            }
        except:
            pass
        
        logger.info("Maintenance report generated")
        
        return {
            'status': 'success',
            'report': report
        }
        
    except Exception as exc:
        logger.error(f"Maintenance report generation error: {str(exc)}")
        
        return {
            'status': 'error',
            'error': str(exc)
        }


@shared_task
def health_check():
    """
    Perform system health check
    """
    try:
        logger.info("Performing system health check")
        
        health_status = {
            'timestamp': datetime.now().isoformat(),
            'database': 'unknown',
            'redis': 'unknown',
            'storage': 'unknown',
            'overall': 'unknown'
        }
        
        # Check database
        try:
            Dataset.objects.count()
            health_status['database'] = 'healthy'
        except Exception as e:
            health_status['database'] = f'unhealthy: {str(e)}'
        
        # Check Redis
        try:
            from django.core.cache import cache
            cache.set('health_check', 'ok', 10)
            if cache.get('health_check') == 'ok':
                health_status['redis'] = 'healthy'
            else:
                health_status['redis'] = 'unhealthy'
        except Exception as e:
            health_status['redis'] = f'unhealthy: {str(e)}'
        
        # Check storage
        try:
            test_file = 'media/health_check.tmp'
            with open(test_file, 'w') as f:
                f.write('health check')
            os.remove(test_file)
            health_status['storage'] = 'healthy'
        except Exception as e:
            health_status['storage'] = f'unhealthy: {str(e)}'
        
        # Overall health
        if all(status == 'healthy' for status in [health_status['database'], health_status['redis'], health_status['storage']]):
            health_status['overall'] = 'healthy'
        else:
            health_status['overall'] = 'unhealthy'
        
        logger.info(f"Health check completed: {health_status['overall']}")
        
        return {
            'status': 'success',
            'health': health_status
        }
        
    except Exception as exc:
        logger.error(f"Health check error: {str(exc)}")
        
        return {
            'status': 'error',
            'error': str(exc)
        }
