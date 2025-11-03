"""
Celery Configuration for Audio Transcription Processing

This module configures Celery for handling background tasks, specifically
audio transcription using Whisper models. Tasks are distributed across
worker processes to handle CPU-intensive transcription operations.

Key Features:
- Redis broker for task distribution
- Django integration for database access
- Auto-discovery of tasks across Django apps
- Proper task routing and error handling
"""

import os
from celery import Celery
from django.conf import settings

# Set the default Django settings module for the 'celery' program
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Create the Celery app
app = Celery('atenas_backend')

# Configure Celery using Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Celery Configuration
app.conf.update(
    # Redis broker configuration
    broker_url='redis://localhost:6379/0',
    result_backend='redis://localhost:6379/0',
    
    # Task configuration
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    
    # Task execution settings
    task_acks_late=True,
    worker_prefetch_multiplier=1,  # Process one task at a time per worker
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes max per task
    task_soft_time_limit=25 * 60,  # 25 minutes soft limit
    
    # Result backend settings
    result_expires=3600,  # Results expire after 1 hour
)

# Auto-discover tasks from all Django apps
app.autodiscover_tasks()