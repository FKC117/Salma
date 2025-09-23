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

# Celery Beat Schedule for periodic tasks
app.conf.beat_schedule = {
    'cleanup-expired-sessions': {
        'task': 'analytics.tasks.cleanup_expired_sessions',
        'schedule': 3600.0,  # Run every hour
    },
    'cleanup-old-analysis-results': {
        'task': 'analytics.tasks.cleanup_old_analysis_results',
        'schedule': 86400.0,  # Run daily
    },
    'backup-database': {
        'task': 'analytics.tasks.backup_database',
        'schedule': 86400.0,  # Run daily
    },
    'monitor-system-performance': {
        'task': 'analytics.tasks.monitor_system_performance',
        'schedule': 300.0,  # Run every 5 minutes
    },
}

@app.task(bind=True)
def debug_task(self):
    """Debug task to test Celery configuration."""
    print(f'Request: {self.request!r}')
