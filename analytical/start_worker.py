#!/usr/bin/env python
"""
Simple Celery Worker Startup Script
Starts a single Celery worker for development/testing
"""

import os
import sys
from pathlib import Path

# Add the project directory to Python path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

if __name__ == '__main__':
    # Set Django settings module
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'analytical.settings')
    
    # Import Django
    import django
    django.setup()
    
    # Start Celery worker
    from celery import current_app
    from celery.__main__ import main
    
    # Set up command line arguments
    sys.argv = [
        'celery',
        '-A', 'analytical',
        'worker',
        '--loglevel=info',
        '--concurrency=2',
        '--queues=file_processing,analysis,llm,agent,reports,images,sandbox,maintenance'
    ]
    
    main()
