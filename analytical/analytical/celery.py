"""
Celery configuration for analytical project.

This module configures Celery for asynchronous task processing.
"""

import os
from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'analytical.settings')

app = Celery('analytical')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Celery Configuration
app.conf.update(
    # Task routing and prioritization
    task_routes={
        'analytics.tasks.file_processing_tasks.*': {'queue': 'file_processing'},
        'analytics.tasks.analysis_tasks.*': {'queue': 'analysis'},
        'analytics.tasks.llm_tasks.*': {'queue': 'llm'},
        'analytics.tasks.agent_tasks.*': {'queue': 'agent'},
        'analytics.tasks.report_tasks.*': {'queue': 'reports'},
        'analytics.tasks.image_tasks.*': {'queue': 'images'},
        'analytics.tasks.sandbox_tasks.*': {'queue': 'sandbox'},
        'analytics.tasks.maintenance_tasks.*': {'queue': 'maintenance'},
    },
    
    # Task time limits
    task_time_limit=300,  # 5 minutes
    task_soft_time_limit=240,  # 4 minutes
    
    # Worker configuration
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    
    # Result backend configuration
    result_expires=3600,  # 1 hour
    
    # Task serialization
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    
    # Timezone
    timezone='UTC',
    enable_utc=True,
)

# Celery Beat Schedule for periodic tasks
app.conf.beat_schedule = {
    # File processing maintenance
    'cleanup-failed-uploads': {
        'task': 'analytics.tasks.file_processing_tasks.cleanup_failed_uploads',
        'schedule': 3600.0,  # Run every hour
    },
    
    # Analysis maintenance
    'cleanup-analysis-cache': {
        'task': 'analytics.tasks.analysis_tasks.cleanup_analysis_cache',
        'schedule': 7200.0,  # Run every 2 hours
    },
    
    # LLM maintenance
    'cleanup-llm-cache': {
        'task': 'analytics.tasks.llm_tasks.cleanup_llm_cache',
        'schedule': 3600.0,  # Run every hour
    },
    'monitor-token-usage': {
        'task': 'analytics.tasks.llm_tasks.monitor_token_usage',
        'schedule': 300.0,  # Run every 5 minutes
    },
    
    # Agent maintenance
    'cleanup-agent-sessions': {
        'task': 'analytics.tasks.agent_tasks.cleanup_agent_sessions',
        'schedule': 3600.0,  # Run every hour
    },
    'monitor-agent-performance': {
        'task': 'analytics.tasks.agent_tasks.monitor_agent_performance',
        'schedule': 600.0,  # Run every 10 minutes
    },
    
    # Image maintenance
    'cleanup-image-cache': {
        'task': 'analytics.tasks.image_tasks.cleanup_image_cache',
        'schedule': 3600.0,  # Run every hour
    },
    'monitor-image-storage': {
        'task': 'analytics.tasks.image_tasks.monitor_image_storage',
        'schedule': 1800.0,  # Run every 30 minutes
    },
    
    # Sandbox maintenance
    'cleanup-sandbox-environment': {
        'task': 'analytics.tasks.sandbox_tasks.cleanup_sandbox_environment',
        'schedule': 3600.0,  # Run every hour
    },
    'monitor-sandbox-resources': {
        'task': 'analytics.tasks.sandbox_tasks.monitor_sandbox_resources',
        'schedule': 300.0,  # Run every 5 minutes
    },
    
    # Report maintenance
    'cleanup-report-cache': {
        'task': 'analytics.tasks.report_tasks.cleanup_report_cache',
        'schedule': 7200.0,  # Run every 2 hours
    },
    
    # System maintenance
    'cleanup-old-files': {
        'task': 'analytics.tasks.maintenance_tasks.cleanup_old_files',
        'schedule': 86400.0,  # Run daily
    },
    'backup-database': {
        'task': 'analytics.tasks.maintenance_tasks.backup_database',
        'schedule': 86400.0,  # Run daily
    },
    'cleanup-old-backups': {
        'task': 'analytics.tasks.maintenance_tasks.cleanup_old_backups',
        'schedule': 86400.0,  # Run daily
    },
    'cleanup-unused-datasets': {
        'task': 'analytics.tasks.maintenance_tasks.cleanup_unused_datasets',
        'schedule': 604800.0,  # Run weekly
    },
    'optimize-database': {
        'task': 'analytics.tasks.maintenance_tasks.optimize_database',
        'schedule': 604800.0,  # Run weekly
    },
    'monitor-system-resources': {
        'task': 'analytics.tasks.maintenance_tasks.monitor_system_resources',
        'schedule': 300.0,  # Run every 5 minutes
    },
    'health-check': {
        'task': 'analytics.tasks.maintenance_tasks.health_check',
        'schedule': 60.0,  # Run every minute
    },
}

@app.task(bind=True)
def debug_task(self):
    """Debug task to test Celery configuration."""
    print(f'Request: {self.request!r}')
