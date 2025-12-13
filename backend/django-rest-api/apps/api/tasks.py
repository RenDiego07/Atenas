"""
Celery Tasks for Audio Transcription Processing

This module contains background tasks for transcribing audio chunks using
OpenAI's Whisper model and generating summaries using Groq's language models.
Tasks run in separate worker processes to handle CPU-intensive transcription
and AI summarization operations without blocking the web server.

Key Features:
- Whisper model integration for high-quality transcription
- Groq API integration for fast cloud-based summarization
- Progress tracking with database status updates
- Error handling and retry logic
- Automatic parent transcription status management
- Support for multiple Whisper model sizes and languages
- Parallel processing for summaries (Groq handles concurrency well)

Dependencies:
- openai-whisper: pip install openai-whisper
- groq: pip install groq
- Redis: For Celery broker (must be running)
- torch: For Whisper model inference (CPU or GPU)
"""

import os
import logging
import traceback
from typing import Optional
from time import sleep
from celery import shared_task
from django.db import transaction
from django.conf import settings
import whisper
from groq import Groq
from redis import Redis

# Configure logging
logger = logging.getLogger(__name__)

# Redis client for rate limiting
try:
    redis_client = Redis(host='localhost', port=6379, decode_responses=True, socket_connect_timeout=2)
    redis_client.ping()  # Test connection
    logger.info("Redis connection established for rate limiting")
except Exception as e:
    logger.warning(f"Redis not available for rate limiting: {e}. Rate limiting will be disabled.")
    redis_client = None

# Groq rate limiting configuration
GROQ_TOKENS_PER_MINUTE = 12000  # Groq free tier limit
GROQ_SAFETY_MARGIN = 0.75  # Use only 75% of limit for safety
GROQ_MAX_TOKENS_PER_MINUTE = int(GROQ_TOKENS_PER_MINUTE * GROQ_SAFETY_MARGIN)

# Cache for loaded Whisper models to avoid reloading
_whisper_models = {}


def _wait_for_rate_limit(estimated_tokens: int, max_wait_time: int = 60) -> bool:
    """
    Wait if necessary to respect Groq rate limits using Redis.
    
    Args:
        estimated_tokens: Number of tokens the request will use
        max_wait_time: Maximum time to wait in seconds
        
    Returns:
        bool: True if rate limit OK, False if Redis unavailable
    """
    if not redis_client:
        # Redis not available, skip rate limiting
        return False
    
    key = "groq:tokens:minute"
    window = 60  # 1 minute window
    max_attempts = max_wait_time // 5
    
    for attempt in range(max_attempts):
        try:
            # Get current usage
            current_usage = redis_client.get(key)
            current_usage = int(current_usage) if current_usage else 0
            
            # Check if we have space
            if current_usage + estimated_tokens <= GROQ_MAX_TOKENS_PER_MINUTE:
                # Increment counter atomically
                pipe = redis_client.pipeline()
                pipe.incrby(key, estimated_tokens)
                pipe.expire(key, window)
                pipe.execute()
                
                logger.debug(f"Rate limit OK: {current_usage + estimated_tokens}/{GROQ_MAX_TOKENS_PER_MINUTE} tokens/min")
                return True
            else:
                # Need to wait
                wait_time = 5
                logger.warning(f"Rate limit approaching: {current_usage}/{GROQ_MAX_TOKENS_PER_MINUTE} tokens/min, waiting {wait_time}s (attempt {attempt+1}/{max_attempts})")
                sleep(wait_time)
        except Exception as e:
            logger.error(f"Error in rate limiting: {e}")
            return False
    
    logger.error(f"Max wait time ({max_wait_time}s) exceeded for rate limiting")
    return False


def get_whisper_model(model_name: str = "medium"):
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
        
        # ❌ REMOVED: Individual chunk summarization - now handled in bulk after all chunks complete
        
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
                summarized=Count('id', filter=Q(status='summarized')),
                failed=Count('id', filter=Q(status='failed')),
                transcribing=Count('id', filter=Q(status='transcribing')),
                ready=Count('id', filter=Q(status='ready'))
            )
            
            total_chunks = chunk_stats['total']
            done_chunks = chunk_stats['done']
            summarized_chunks = chunk_stats['summarized']
            failed_chunks = chunk_stats['failed'] 
            processing_chunks = chunk_stats['transcribing'] + chunk_stats['ready']
            
            # Determine new status
            if (done_chunks + summarized_chunks) == total_chunks:
                new_status = "transcribed"
                logger.info(f"Transcription {transcription_id} completed successfully")
                
                # 🎯 NUEVO: Si todos están transcritos pero no resumidos, iniciar resúmenes
                if done_chunks > 0 and summarized_chunks == 0:
                    logger.info(f"All chunks transcribed for transcription {transcription_id}, starting summarization process")
                    start_chunk_summarization.delay(transcription_id)
                
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


# =============================================================================
# SUMMARY GENERATION TASKS
# =============================================================================

@shared_task(bind=True, max_retries=5, default_retry_delay=90)
def generate_chunk_summary(self, chunk_id, model_name="llama-3.3-70b-versatile"):
    """
    Generate summary for a specific chunk using Groq cloud API.
    Includes automatic retry for rate limits and duplicate detection.
    """
    logger.info(f"Starting summary generation for chunk {chunk_id}")
    
    try:
        from apps.api.models import TranscriptionChunk
        
        chunk = TranscriptionChunk.objects.get(id=chunk_id)
        
        # 🛡️ Verificar si ya tiene resumen (prevenir duplicados)
        if chunk.summary and chunk.status == 'summarized':
            logger.info(f"Chunk {chunk_id} already has summary, skipping")
            return {'status': 'skipped', 'reason': 'already_summarized'}
        
        # Verificar que el chunk esté transcrito
        if not chunk.text or chunk.status != 'done':
            logger.warning(f"Chunk {chunk_id} not ready for summarization (status: {chunk.status})")
            return {'status': 'skipped', 'reason': 'chunk_not_transcribed'}
        
        logger.info(f"Starting summarization for chunk {chunk_id} (index: {chunk.index})")
        
        # Construir el prompt
        prompt = _build_summary_prompt(chunk)
        
        # ✅ AGREGAR LOGGING PARA DIAGNÓSTICO
        logger.info(f"Chunk {chunk_id} text length: {len(chunk.text)} chars")
        logger.info(f"Chunk {chunk_id} text preview: {chunk.text[:200]}...")
        logger.debug(f"Full prompt for chunk {chunk_id}: {prompt}")
        
        # Llamar a Groq
        groq_response = _call_groq_api(prompt, model_name)
        
        # ✅ LOGGING DETALLADO DE LA RESPUESTA
        logger.info(f"Groq response for chunk {chunk_id}: success={groq_response.get('success')}")
        if not groq_response.get('success'):
            logger.error(f"Groq failed for chunk {chunk_id}. Error: {groq_response.get('error')}")
            logger.error(f"Response details: {groq_response}")
        
        if groq_response.get('success'):
            # Guardar el resumen en el chunk y cambiar estado
            with transaction.atomic():
                chunk.refresh_from_db()
                chunk.summary = groq_response['summary']
                chunk.status = 'summarized'
                chunk.save(update_fields=['summary', 'status'])
            
            logger.info(f"Successfully generated summary for chunk {chunk_id} ({len(groq_response['summary'])} chars)")
            
            # Verificar si este es el último chunk y generar resumen final
            _check_and_generate_final_summary(chunk.transcription)
            
            return {
                'status': 'success',
                'chunk_id': chunk_id,
                'summary_length': len(groq_response['summary']),
                'model_used': model_name
            }
        else:
            error_msg = str(groq_response.get('error', ''))
            
            # 🔄 RETRY AUTOMÁTICO para rate limits
            if 'rate_limit' in error_msg.lower() or '429' in error_msg:
                retry_delay = 90
                logger.warning(f"Rate limit for chunk {chunk_id}, retrying in {retry_delay}s (attempt {self.request.retries + 1}/{self.max_retries})")
                raise self.retry(countdown=retry_delay, exc=Exception(error_msg))
            
            # RETRY para timeouts
            if 'timeout' in error_msg.lower() or 'timed out' in error_msg.lower():
                if self.request.retries < self.max_retries:
                    logger.warning(f"Timeout for chunk {chunk_id}, retrying in {self.default_retry_delay}s")
                    raise self.retry(countdown=self.default_retry_delay)
            
            logger.error(f"Groq API failed for chunk {chunk_id}: {error_msg}")
            return {'status': 'failed', 'error': error_msg}
            
    except TranscriptionChunk.DoesNotExist:
        logger.error(f"Chunk {chunk_id} not found")
        return {'status': 'failed', 'error': 'chunk_not_found'}
    except Exception as e:
        logger.error(f"Error generating summary for chunk {chunk_id}: {str(e)}")
        
        error_msg = str(e).lower()
        
        # Retry para rate limits
        if 'rate_limit' in error_msg or '429' in error_msg:
            if self.request.retries < self.max_retries:
                logger.warning(f"Rate limit exception for chunk {chunk_id}, retrying in 90s")
                raise self.retry(countdown=90, exc=e)
        
        # Retry para errores de red
        if any(keyword in error_msg for keyword in ['timeout', 'connection', 'network']):
            if self.request.retries < self.max_retries:
                logger.warning(f"Network error for chunk {chunk_id}, retrying in {self.default_retry_delay}s")
                raise self.retry(exc=e, countdown=self.default_retry_delay)
        
        return {'status': 'failed', 'error': str(e)}


def _build_summary_prompt(chunk):
    """
    Build prompt for independent chunk summary without previous context dependency
    """
    prompt = f"""GENERE UN RESUMEN CONCISO Y PRECISO DEL SIGUIENTE TEXTO.

INSTRUCCIONES CRÍTICAS:
- NO inventes datos, fechas, nombres o información que no esté en el texto
- Corrige errores obvios de transcripción automática
- Redacta en tercera persona
- EXTENSIÓN: 200-250 palabras (más detallado que antes)
- Un solo bloque de texto corrido, sin listas ni viñetas
- Incluye todos los puntos importantes y conceptos clave
- Mantén detalles relevantes para contexto posterior
- Usa un lenguaje claro y profesional

TEXTO A RESUMIR:
{chunk.text}

RESUMEN:"""
    
    return prompt


def _call_groq_api(prompt, model_name="llama-3.3-70b-versatile", max_tokens=1500):
    """
    Call Groq API with rate limiting protection using Redis.
    
    Args:
        prompt: The prompt to send to Groq
        model_name: Model to use
        max_tokens: Maximum tokens in response
        
    Returns:
        dict: Response with 'success' and 'summary' or 'error'
    """
    try:
        # Inicializar cliente Groq
        client = Groq(
            api_key=os.environ.get("GROQ_API_KEY")
        )
        
        if not client.api_key:
            logger.error("GROQ_API_KEY not found in environment variables")
            return {
                'success': False,
                'error': 'missing_groq_api_key'
            }
        
        # 🚦 RATE LIMITING: Estimar tokens y esperar si es necesario
        # Aproximación: 1 token ≈ 4 caracteres
        estimated_tokens = (len(prompt) + max_tokens) // 4
        
        if redis_client:
            rate_limit_ok = _wait_for_rate_limit(estimated_tokens, max_wait_time=60)
            if not rate_limit_ok:
                logger.warning("Rate limit wait timeout, proceeding anyway")
        
        # Crear chat completion
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model=model_name,
            temperature=0.1,
            top_p=0.9,
            max_tokens=max_tokens
        )
        
        summary = chat_completion.choices[0].message.content.strip()
        
        # ✅ LOGGING DETALLADO DE LA RESPUESTA
        logger.info(f"Groq API response successful, model: {model_name}")
        logger.debug(f"Groq response: {summary[:200]}...")
        
        # ✅ VERIFICAR SI GROQ RECHAZÓ EL CONTENIDO
        if "Lo siento" in summary or "no puedo cumplir" in summary or "cannot fulfill" in summary:
            logger.warning(f"Groq rejected content. Response: '{summary}'")
            return {
                'success': False,
                'error': 'content_rejected_by_model',
                'groq_response': summary
            }
        
        if summary:
            return {
                'success': True,
                'summary': summary,
                'model': model_name
            }
        else:
            return {
                'success': False,
                'error': 'empty_response_from_groq'
            }
            
    except Exception as e:
        logger.error(f"Error calling Groq API: {str(e)}")
        return {
            'success': False,
            'error': f'groq_api_error: {str(e)}'
        }


def _check_and_generate_final_summary(transcription):
    """
    Check if all chunks have summaries and generate final summary.
    Uses database-level locking to prevent duplicate final summary generation.
    """
    from apps.api.models import TranscriptionChunk, Summary, Transcription
    
    chunks_done = TranscriptionChunk.objects.filter(
        transcription=transcription,
        status__in=['done', 'summarized']
    )
    
    chunks_summarized = TranscriptionChunk.objects.filter(
        transcription=transcription,
        status='summarized'
    )
    
    # Verificar si todos los chunks transcritos están resumidos
    if chunks_done.count() > 0 and chunks_summarized.count() == chunks_done.count():
        logger.info(f"All chunks summarized for transcription {transcription.id}, checking for final summary generation")
        
        # 🔒 SOLUCIÓN 1: Database lock para prevenir duplicados
        with transaction.atomic():
            # Lock exclusivo en la transcripción
            transcription_locked = Transcription.objects.select_for_update().get(id=transcription.id)
            
            # Verificar si ya existe resumen
            if Summary.objects.filter(transcription=transcription_locked).exists():
                logger.info(f"Summary already exists for transcription {transcription_locked.id}, skipping")
                return
            
            # Verificar estado
            if transcription_locked.status in ['summarizing', 'done']:
                logger.info(f"Summary generation already in progress or complete for transcription {transcription_locked.id}")
                return
            
            # Marcar como "generando resumen"
            transcription_locked.status = 'summarizing'
            transcription_locked.save(update_fields=['status'])
            
            logger.info(f"Locked transcription {transcription_locked.id} for final summary generation")
            
            # Obtener prompt personalizado
            user_prompt = transcription_locked.temp_custom_prompt if transcription_locked.temp_custom_prompt else None
            if user_prompt:
                logger.info(f"Using custom prompt from upload for transcription {transcription_locked.id}: {user_prompt[:50]}...")
            
            # Generar resumen final
            generate_final_summary.delay(transcription_locked.id, user_prompt)


@shared_task(bind=True, max_retries=3, default_retry_delay=90)
def generate_final_summary(self, transcription_id, user_prompt=None, model_name="llama-3.3-70b-versatile"):
    """
    Generate final summary by combining all chunk summaries.
    Includes duplicate detection and rate limit handling with automatic retry.
    """
    logger.info(f"Starting final summary generation for transcription {transcription_id}")
    
    try:
        from apps.api.models import Transcription, Summary, TranscriptionChunk
        
        transcription = Transcription.objects.get(id=transcription_id)
        
        # 🛡️ SOLUCIÓN 2: Verificación temprana
        if Summary.objects.filter(transcription=transcription).exists():
            logger.warning(f"Summary already exists for transcription {transcription_id}, skipping duplicate generation")
            # Asegurar que el estado sea 'done'
            if transcription.status != 'done':
                transcription.status = 'done'
                transcription.save(update_fields=['status'])
            return {
                'status': 'skipped',
                'reason': 'summary_already_exists',
                'transcription_id': transcription_id
            }
        
        # Obtener todos los resúmenes de chunks en orden
        chunks_summarized = TranscriptionChunk.objects.filter(
            transcription=transcription,
            status='summarized'
        ).order_by('index')
        
        if not chunks_summarized.exists():
            logger.warning(f"No summarized chunks found for transcription {transcription_id}")
            return {'status': 'failed', 'error': 'no_summarized_chunks'}
        
        # Combinar resúmenes para prompt final
        combined_summaries = '\n\n'.join([
            f"Sección {chunk.index + 1}: {chunk.summary}" 
            for chunk in chunks_summarized
        ])
        
        # Construir prompt final considerando el prompt del usuario
        if user_prompt:
            final_prompt = f"""

INSTRUCCIONES ESPECÍFICAS DEL USUARIO:
{user_prompt}

RESÚMENES DE SECCIONES:
{combined_summaries}

INSTRUCCIONES CRÍTICAS:
- Une todo en un texto coherente y fluido
- NO repitas ideas o conceptos ya mencionados
- NO agregues información nueva que no esté en los resúmenes
- Mantén la secuencia lógica y cronológica
- Sigue las instrucciones específicas del usuario proporcionadas arriba

"""
        else:
            final_prompt = f"""

{combined_summaries}

INSTRUCCIONES CRÍTICAS:
- Une todo en un texto coherente y fluido
- NO repitas ideas o conceptos ya mencionados
- NO agregues información nueva que no esté en los resúmenes
- Mantén la secuencia lógica y cronológica
- Identifica temas principales y conclusiones
- Máximo 500 palabras
- Un solo bloque de texto profesional

"""

        # Llamar a Groq para resumen final
        groq_response = _call_groq_api(final_prompt, model_name, max_tokens=2000)
        
        if groq_response.get('success'):
            # Crear registro de Summary
            summary_obj, created = Summary.objects.get_or_create(
                transcription=transcription,
                defaults={
                    'header': groq_response['summary'],
                    'url_link': f'/api/transcriptions/{transcription.id}/',
                    'prompt': user_prompt if user_prompt else 'Resumen automático generado'
                }
            )
            
            # Si ya existía, actualizar
            if not created:
                summary_obj.header = groq_response['summary']
                summary_obj.prompt = user_prompt if user_prompt else summary_obj.prompt
                summary_obj.save(update_fields=['header', 'prompt'])
            
            # Actualizar estado a 'done'
            transcription.status = 'done'
            transcription.save(update_fields=['status'])
            
            # Limpiar prompt temporal después de crear el Summary
            if transcription.temp_custom_prompt:
                transcription.temp_custom_prompt = None
                transcription.save(update_fields=['temp_custom_prompt'])
                logger.info(f"Cleared temporary custom prompt for transcription {transcription_id}")
            
            logger.info(f"Final summary generated for transcription {transcription_id}")
            
            return {
                'status': 'success',
                'transcription_id': transcription_id,
                'summary_length': len(groq_response['summary']),
                'chunks_processed': chunks_summarized.count(),
                'user_prompt_used': bool(user_prompt)
            }
        else:
            error_msg = groq_response.get('error', 'Unknown error')
            
            # 🔄 SOLUCIÓN 3: Retry automático para rate limits
            if 'rate_limit' in error_msg.lower() or '429' in error_msg:
                logger.warning(f"Rate limit hit for transcription {transcription_id}, will retry in 90 seconds")
                raise self.retry(countdown=90, exc=Exception(error_msg))
            
            logger.error(f"Failed to generate final summary for transcription {transcription_id}: {error_msg}")
            
            # Actualizar estado a failed
            transcription.status = 'failed'
            transcription.save(update_fields=['status'])
            
            return {'status': 'failed', 'error': error_msg}
            
    except Transcription.DoesNotExist:
        logger.error(f"Transcription {transcription_id} not found")
        return {'status': 'failed', 'error': 'transcription_not_found'}
    except Exception as e:
        logger.error(f"Error generating final summary for transcription {transcription_id}: {str(e)}")
        
        # Si es rate limit, reintentar
        if 'rate_limit' in str(e).lower() or '429' in str(e):
            logger.warning(f"Rate limit exception for transcription {transcription_id}, retrying in 90 seconds")
            raise self.retry(countdown=90, exc=e)
        
        # Para otros errores, marcar como failed
        try:
            transcription = Transcription.objects.get(id=transcription_id)
            transcription.status = 'failed'
            transcription.save(update_fields=['status'])
        except:
            pass
        
        return {'status': 'failed', 'error': str(e)}


@shared_task
def start_chunk_summarization(transcription_id):
    """
    Start summarization process for all chunks of a completed transcription
    Process chunks PARALLEL with Groq (cloud service handles concurrency well)
    """
    try:
        from apps.api.models import Transcription, TranscriptionChunk
        
        transcription = Transcription.objects.get(id=transcription_id)
        
        # Obtener todos los chunks transcritos (status='done')
        chunks_to_summarize = TranscriptionChunk.objects.filter(
            transcription=transcription,
            status='done'
        ).order_by('index')
        
        if not chunks_to_summarize.exists():
            logger.warning(f"No chunks to summarize for transcription {transcription_id}")
            return {'status': 'no_chunks', 'transcription_id': transcription_id}
        
        logger.info(f"Starting PARALLEL summarization for {chunks_to_summarize.count()} chunks of transcription {transcription_id}")
        
        # Enviar tareas de resumen para cada chunk EN PARALELO (Groq maneja concurrencia)
        enqueued_count = 0
        for chunk in chunks_to_summarize:
            try:
                # ✅ SIN DELAY - Procesamiento paralelo con Groq
                generate_chunk_summary.delay(chunk.id)
                enqueued_count += 1
                logger.info(f"Enqueued chunk {chunk.id} (index {chunk.index}) for parallel processing")
            except Exception as e:
                logger.error(f"Failed to enqueue summary task for chunk {chunk.id}: {e}")
        
        logger.info(f"Enqueued {enqueued_count} chunk summarization tasks for PARALLEL processing")
        
        return {
            'status': 'success',
            'transcription_id': transcription_id,
            'chunks_enqueued': enqueued_count,
            'total_chunks': chunks_to_summarize.count(),
            'processing_mode': 'parallel',
            'estimated_completion_time': 'Variable - depends on Groq API response time'
        }
        
    except Transcription.DoesNotExist:
        logger.error(f"Transcription {transcription_id} not found")
        return {'status': 'failed', 'error': 'transcription_not_found'}
    except Exception as e:
        logger.error(f"Error starting chunk summarization for transcription {transcription_id}: {e}")
        return {'status': 'failed', 'error': str(e)}


