#!/usr/bin/env python
"""
Celery Worker Startup Script
Starts multiple Celery workers for different task queues
"""

import os
import sys
import subprocess
import time
from pathlib import Path

# Add the project directory to Python path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

def start_celery_worker(queue_name, concurrency=2, loglevel='info'):
    """Start a Celery worker for a specific queue"""
    cmd = [
        'celery',
        '-A', 'analytical',
        'worker',
        '--loglevel', loglevel,
        '--concurrency', str(concurrency),
        '--queues', queue_name,
        '--hostname', f'{queue_name}@%h',
        '--without-gossip',
        '--without-mingle',
        '--without-heartbeat'
    ]
    
    print(f"Starting Celery worker for queue: {queue_name}")
    print(f"Command: {' '.join(cmd)}")
    
    return subprocess.Popen(cmd, cwd=project_dir)

def start_celery_beat():
    """Start Celery Beat scheduler"""
    cmd = [
        'celery',
        '-A', 'analytical',
        'beat',
        '--loglevel', 'info',
        '--scheduler', 'django_celery_beat.schedulers:DatabaseScheduler'
    ]
    
    print("Starting Celery Beat scheduler")
    print(f"Command: {' '.join(cmd)}")
    
    return subprocess.Popen(cmd, cwd=project_dir)

def start_celery_flower():
    """Start Celery Flower monitoring"""
    cmd = [
        'celery',
        '-A', 'analytical',
        'flower',
        '--port', '5555',
        '--broker', 'redis://localhost:6379/0'
    ]
    
    print("Starting Celery Flower monitoring")
    print(f"Command: {' '.join(cmd)}")
    
    return subprocess.Popen(cmd, cwd=project_dir)

def main():
    """Main function to start all Celery workers"""
    print("=" * 60)
    print("Starting Celery Workers for Analytical System")
    print("=" * 60)
    
    # Check if virtual environment is activated
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("WARNING: Virtual environment not detected!")
        print("Please activate the virtual environment before running this script.")
        return
    
    # Define worker queues and their concurrency
    workers = {
        'file_processing': 2,  # File uploads and processing
        'analysis': 4,        # Data analysis tasks
        'llm': 2,            # LLM processing tasks
        'agent': 2,          # Agentic AI tasks
        'reports': 2,        # Report generation
        'images': 2,         # Image processing
        'sandbox': 3,        # Code execution
        'maintenance': 1,    # System maintenance
    }
    
    processes = []
    
    try:
        # Start Celery Beat scheduler
        beat_process = start_celery_beat()
        processes.append(('Celery Beat', beat_process))
        time.sleep(2)
        
        # Start Celery Flower monitoring
        flower_process = start_celery_flower()
        processes.append(('Celery Flower', flower_process))
        time.sleep(2)
        
        # Start workers for each queue
        for queue_name, concurrency in workers.items():
            worker_process = start_celery_worker(queue_name, concurrency)
            processes.append((f'Worker-{queue_name}', worker_process))
            time.sleep(1)
        
        print("\n" + "=" * 60)
        print("All Celery workers started successfully!")
        print("=" * 60)
        print(f"Celery Beat: Running")
        print(f"Celery Flower: http://localhost:5555")
        print("\nWorker Queues:")
        for queue_name, concurrency in workers.items():
            print(f"  - {queue_name}: {concurrency} workers")
        
        print("\nPress Ctrl+C to stop all workers...")
        
        # Wait for processes
        while True:
            time.sleep(1)
            
            # Check if any process has died
            for name, process in processes:
                if process.poll() is not None:
                    print(f"\nWARNING: {name} process has stopped!")
                    print(f"Exit code: {process.returncode}")
    
    except KeyboardInterrupt:
        print("\n" + "=" * 60)
        print("Stopping all Celery workers...")
        print("=" * 60)
        
        # Stop all processes
        for name, process in processes:
            print(f"Stopping {name}...")
            process.terminate()
            try:
                process.wait(timeout=10)
                print(f"{name} stopped gracefully")
            except subprocess.TimeoutExpired:
                print(f"{name} did not stop gracefully, killing...")
                process.kill()
                process.wait()
        
        print("All workers stopped successfully!")

if __name__ == '__main__':
    main()
