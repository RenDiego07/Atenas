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
import requests
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

@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def generate_chunk_summary(self, chunk_id, model_name="llama3.1:8b"):
    """
    Generate summary for a specific chunk using Ollama
    with context from previous chunk's summary (windowed chain-of-context)
    """
    import requests
    import json
    
    try:
        from apps.api.models import TranscriptionChunk
        
        chunk = TranscriptionChunk.objects.get(id=chunk_id)
        
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
        
        # Llamar a Ollama
        ollama_response = _call_ollama_api(prompt, model_name)
        
        # ✅ LOGGING DETALLADO DE LA RESPUESTA
        logger.info(f"Ollama response for chunk {chunk_id}: success={ollama_response.get('success')}")
        if not ollama_response.get('success'):
            logger.error(f"Ollama failed for chunk {chunk_id}. Error: {ollama_response.get('error')}")
            logger.error(f"Response details: {ollama_response}")
        
        if ollama_response.get('success'):
            # Guardar el resumen en el chunk y cambiar estado
            with transaction.atomic():
                chunk.refresh_from_db()
                chunk.summary = ollama_response['summary']
                chunk.status = 'summarized'  # Nuevo estado
                chunk.save(update_fields=['summary', 'status'])
            
            logger.info(f"Successfully generated summary for chunk {chunk_id} ({len(ollama_response['summary'])} chars)")
            
            # Verificar si este es el último chunk y generar resumen final
            _check_and_generate_final_summary(chunk.transcription)
            
            return {
                'status': 'success',
                'chunk_id': chunk_id,
                'summary_length': len(ollama_response['summary']),
                'model_used': model_name
            }
        else:
            logger.error(f"Ollama API failed for chunk {chunk_id}: {ollama_response.get('error')}")
            
            # ✅ RETRY LOGIC PARA TIMEOUTS
            error_msg = str(ollama_response.get('error', ''))
            if 'timeout' in error_msg.lower() or 'timed out' in error_msg.lower():
                if self.request.retries < self.max_retries:
                    logger.warning(f"Timeout detected for chunk {chunk_id}, retrying in {self.default_retry_delay}s (attempt {self.request.retries + 1}/{self.max_retries})")
                    raise self.retry(countdown=self.default_retry_delay)
                else:
                    logger.error(f"Max retries exceeded for chunk {chunk_id} due to timeouts")
            
            return {'status': 'failed', 'error': ollama_response.get('error')}
            
    except TranscriptionChunk.DoesNotExist:
        logger.error(f"Chunk {chunk_id} not found")
        return {'status': 'failed', 'error': 'chunk_not_found'}
    except Exception as e:
        logger.error(f"Error generating summary for chunk {chunk_id}: {e}")
        
        # ✅ RETRY LOGIC PARA ERRORES DE RED
        error_msg = str(e).lower()
        if any(keyword in error_msg for keyword in ['timeout', 'connection', 'network']):
            if self.request.retries < self.max_retries:
                logger.warning(f"Network error for chunk {chunk_id}, retrying in {self.default_retry_delay}s (attempt {self.request.retries + 1}/{self.max_retries})")
                raise self.retry(exc=e, countdown=self.default_retry_delay)
            else:
                logger.error(f"Max retries exceeded for chunk {chunk_id} due to network errors")
        
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
- Máximo 180-200 palabras
- Un solo bloque de texto corrido, sin listas ni viñetas
- Mantén solo los puntos clave y conceptos importantes
- Usa un lenguaje claro y profesional

TEXTO A RESUMIR:
{chunk.text}

RESUMEN:"""
    
    return prompt


def _call_ollama_api(prompt, model_name="llama3.1:8b"):
    """
    Call Ollama API to generate summary
    """
    import requests
    
    try:
        url = "http://localhost:11434/api/generate"
        
        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "top_p": 0.9
            }
        }
        
        response = requests.post(url, json=payload, timeout=240)  # Aumentado de 120 a 240 segundos
        
        # ✅ LOGGING DETALLADO DE LA RESPUESTA HTTP
        logger.info(f"Ollama HTTP response: status={response.status_code}")
        logger.debug(f"Ollama raw response: {response.text[:500]}...")
        
        if response.status_code == 200:
            result = response.json()
            summary = result.get('response', '').strip()
            
            # ✅ VERIFICAR SI OLLAMA RECHAZÓ EL CONTENIDO
            if "Lo siento" in summary or "no puedo cumplir" in summary or "cannot fulfill" in summary:
                logger.warning(f"Ollama rejected content. Response: '{summary}'")
                return {
                    'success': False,
                    'error': 'content_rejected_by_model',
                    'ollama_response': summary
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
                    'error': 'empty_response_from_ollama'
                }
        else:
            return {
                'success': False,
                'error': f'ollama_api_error_{response.status_code}'
            }
            
    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'error': f'network_error: {str(e)}'
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'unexpected_error: {str(e)}'
        }


def _check_and_generate_final_summary(transcription):
    """
    Check if all chunks have summaries and generate final summary
    """
    from apps.api.models import TranscriptionChunk
    
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
        
        # Verificar si ya existe un resumen final
        from apps.api.models import Summary
        if not Summary.objects.filter(transcription=transcription).exists():
            # Buscar el prompt del usuario en la transcripción
            generate_final_summary.delay(transcription.id)


@shared_task
def generate_final_summary(transcription_id, user_prompt=None, model_name="llama3.1:8b"):
    """
    Generate final summary by combining all chunk summaries
    with user's custom prompt consideration
    """
    try:
        from apps.api.models import Transcription, Summary, TranscriptionChunk
        
        transcription = Transcription.objects.get(id=transcription_id)
        
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

        # Llamar a Ollama para resumen final
        ollama_response = _call_ollama_api(final_prompt, model_name)
        
        if ollama_response.get('success'):
            # Crear registro de Summary
            summary_obj, created = Summary.objects.get_or_create(
                transcription=transcription,
                defaults={
                    'header': ollama_response['summary'],
                    'url_link': f'/api/transcriptions/{transcription.id}/',
                    'prompt': user_prompt if user_prompt else 'Resumen automático generado'
                }
            )
            
            # Si ya existía, actualizar
            if not created:
                summary_obj.header = ollama_response['summary']
                summary_obj.prompt = user_prompt if user_prompt else summary_obj.prompt
                summary_obj.save(update_fields=['header', 'prompt'])
            
            logger.info(f"Final summary generated for transcription {transcription_id}")
            
            return {
                'status': 'success',
                'transcription_id': transcription_id,
                'summary_length': len(ollama_response['summary']),
                'chunks_processed': chunks_summarized.count(),
                'user_prompt_used': bool(user_prompt)
            }
        else:
            logger.error(f"Failed to generate final summary for transcription {transcription_id}: {ollama_response.get('error')}")
            return {'status': 'failed', 'error': ollama_response.get('error')}
            
    except Transcription.DoesNotExist:
        logger.error(f"Transcription {transcription_id} not found")
        return {'status': 'failed', 'error': 'transcription_not_found'}
    except Exception as e:
        logger.error(f"Error generating final summary for transcription {transcription_id}: {e}")
        return {'status': 'failed', 'error': str(e)}


@shared_task
def start_chunk_summarization(transcription_id):
    """
    Start summarization process for all chunks of a completed transcription
    Process chunks SEQUENTIALLY to avoid Ollama concurrency issues
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
        
        logger.info(f"Starting SEQUENTIAL summarization for {chunks_to_summarize.count()} chunks of transcription {transcription_id}")
        
        # Enviar tareas de resumen para cada chunk en orden secuencial con delay
        enqueued_count = 0
        for i, chunk in enumerate(chunks_to_summarize):
            try:
                # Procesar chunks secuencialmente con delay entre ellos para evitar concurrencia
                delay_seconds = i * 30  # Aumentado a 30 segundos para dar más tiempo entre chunks
                generate_chunk_summary.apply_async(
                    args=[chunk.id], 
                    countdown=delay_seconds
                )
                enqueued_count += 1
                logger.info(f"Enqueued chunk {chunk.id} (index {chunk.index}) with {delay_seconds}s delay")
            except Exception as e:
                logger.error(f"Failed to enqueue summary task for chunk {chunk.id}: {e}")
        
        logger.info(f"Enqueued {enqueued_count} chunk summarization tasks for SEQUENTIAL processing")
        
        return {
            'status': 'success',
            'transcription_id': transcription_id,
            'chunks_enqueued': enqueued_count,
            'total_chunks': chunks_to_summarize.count(),
            'processing_mode': 'sequential',
            'estimated_completion_time': f"{enqueued_count * 30} seconds + processing time"
        }
        
    except Transcription.DoesNotExist:
        logger.error(f"Transcription {transcription_id} not found")
        return {'status': 'failed', 'error': 'transcription_not_found'}
    except Exception as e:
        logger.error(f"Error starting chunk summarization for transcription {transcription_id}: {e}")
        return {'status': 'failed', 'error': str(e)}


