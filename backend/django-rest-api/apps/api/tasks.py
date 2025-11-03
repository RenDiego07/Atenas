"""
Celery Tasks for Audio Transcription Processing

This module contains background tasks for transcribing audio chunks using
OpenAI's Whisper model. Tasks run in separate worker processes to handle
the CPU-intensive transcription operations without blocking the web server.

Key Features:
- Whisper model integration for high-quality transcription
- Progress tracking with database status updates
- Error handling and retry logic
- Automatic parent transcription status management
- Support for multiple Whisper model sizes and languages

Dependencies:
- openai-whisper: pip install openai-whisper
- Redis: For Celery broker (must be running)
- torch: For Whisper model inference (CPU or GPU)
"""

import os
import logging
import traceback
from typing import Optional
from celery import shared_task
from django.db import transaction
from django.conf import settings
import whisper

# Configure logging
logger = logging.getLogger(__name__)

# Cache for loaded Whisper models to avoid reloading
_whisper_models = {}


def get_whisper_model(model_name: str = "base"):
    """
    Get or load a Whisper model with caching to avoid reloading.
    
    Available models: tiny, base, small, medium, large
    - tiny: ~39 MB, fastest but least accurate
    - base: ~74 MB, good balance of speed and accuracy  
    - small: ~244 MB, better accuracy
    - medium: ~769 MB, high accuracy (recommended)
    - large: ~1550 MB, highest accuracy but slowest
    
    Args:
        model_name: Name of the Whisper model to load
        
    Returns:
        Loaded Whisper model instance
    """
    global _whisper_models
    
    if model_name not in _whisper_models:
        logger.info(f"Loading Whisper model: {model_name}")
        try:
            _whisper_models[model_name] = whisper.load_model(model_name)
            logger.info(f"Successfully loaded Whisper model: {model_name}")
        except Exception as e:
            logger.error(f"Failed to load Whisper model {model_name}: {e}")
            raise
    
    return _whisper_models[model_name]




@shared_task(bind=True, max_retries=3, default_retry_delay=60) 
def transcribe_chunk(self, chunk_id: int, model_name: str = "base", language: str = "es"):
    """
    Transcribe a single audio chunk using Whisper.
    
    Args:
        chunk_id: ID of the TranscriptionChunk to process
        model_name: Whisper model to use ('tiny', 'base', 'small', 'medium', 'large')
        language: Language code for transcription (e.g., 'es', 'en')
        
    Returns:
        dict: Transcription result with status and metadata
    """
    from apps.api.models import TranscriptionChunk
    
    logger.info(f"Starting transcription for chunk {chunk_id} (model: {model_name}, language: {language})")
    
    try:
        # Get and validate chunk
        with transaction.atomic():
            chunk = TranscriptionChunk.objects.select_for_update().get(id=chunk_id)
            
            # Validate chunk file exists
            if not chunk.file or not os.path.exists(chunk.file.path):
                raise Exception(f"Chunk file not found: {chunk.file.name if chunk.file else 'None'}")
            
            # Update status to transcribing
            chunk.status = "transcribing"
            chunk.save(update_fields=['status'])
        
        # Load Whisper model and transcribe
        model = get_whisper_model(model_name)
        result = model.transcribe(chunk.file.path, language=language, verbose=False)
        transcribed_text = result.get("text", "").strip()
        
        # Update chunk with results
        with transaction.atomic():
            chunk.refresh_from_db()
            chunk.text = transcribed_text
            chunk.status = "done"
            chunk.save(update_fields=['text', 'status'])
        
        logger.info(f"Successfully transcribed chunk {chunk_id} ({len(transcribed_text)} chars)")
        
        # Check if all chunks are complete and update parent transcription
        _check_transcription_completion(chunk.transcription_id)
        
        return {
            "status": "success",
            "chunk_id": chunk_id,
            "transcription_id": chunk.transcription_id,
            "text_length": len(transcribed_text),
            "model_used": model_name,
            "language": language
        }
        
    except Exception as exc:
        logger.error(f"Error transcribing chunk {chunk_id}: {str(exc)}")
        
        # Update chunk status to failed
        try:
            with transaction.atomic():
                chunk = TranscriptionChunk.objects.get(id=chunk_id)
                chunk.status = "failed"
                chunk.save(update_fields=['status'])
                
            # Check transcription status even if this chunk failed
            _check_transcription_completion(chunk.transcription_id)
            
        except Exception as db_error:
            logger.error(f"Failed to update chunk status to failed: {db_error}")
        
        # Retry the task if we haven't exceeded max retries
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying chunk {chunk_id} (attempt {self.request.retries + 1}/{self.max_retries})")
            raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))
        
        # Max retries exceeded
        logger.error(f"Max retries exceeded for chunk {chunk_id}")
        raise exc


def _check_transcription_completion(transcription_id: int):
    """
    Check if all chunks of a transcription are complete and update parent status.
    
    This function checks the status of all chunks belonging to a transcription
    and updates the parent Transcription status accordingly:
    - If all chunks are "done": status = "transcribed"  
    - If any chunks are "failed" and none are pending: status = "failed"
    - If any chunks are still processing: status remains "transcribing"
    
    Args:
        transcription_id: ID of the Transcription to check
    """
    from apps.api.models import Transcription, TranscriptionChunk
    from django.db.models import Q, Count
    
    try:
        with transaction.atomic():
            transcription = Transcription.objects.select_for_update().get(id=transcription_id)
            
            # Get chunk status counts
            chunk_stats = TranscriptionChunk.objects.filter(
                transcription=transcription
            ).aggregate(
                total=Count('id'),
                done=Count('id', filter=Q(status='done')),
                failed=Count('id', filter=Q(status='failed')),
                transcribing=Count('id', filter=Q(status='transcribing')),
                ready=Count('id', filter=Q(status='ready'))
            )
            
            total_chunks = chunk_stats['total']
            done_chunks = chunk_stats['done']
            failed_chunks = chunk_stats['failed'] 
            processing_chunks = chunk_stats['transcribing'] + chunk_stats['ready']
            
            # Determine new status
            if done_chunks == total_chunks:
                new_status = "transcribed"
                logger.info(f"Transcription {transcription_id} completed successfully")
                
            elif processing_chunks == 0 and failed_chunks > 0:
                new_status = "failed"
                logger.warning(f"Transcription {transcription_id} failed ({failed_chunks} chunks failed)")
                
            else:
                new_status = "transcribing"
            
            # Update transcription status if changed
            if transcription.status != new_status:
                transcription.status = new_status
                transcription.save(update_fields=['status'])
                logger.info(f"Transcription {transcription_id} status updated to {new_status}")
        
    except Exception as e:
        logger.error(f"Error checking transcription completion for {transcription_id}: {e}")


