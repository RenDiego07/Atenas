from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser 
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from mutagen import File as MutagenFile
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from apps.api.models import Transcription, TranscriptionChunk, Summary
from apps.api.services.chunking import ChunkingService
from apps.transcriptions.serializers import (
    AudioCreateSerializer,
    TranscriptionHistorySerializer
)
import logging
import time

logger = logging.getLogger(__name__)

@swagger_auto_schema(
    method='post',
    operation_summary="Subir audio para transcripción y resumen (sincrónico)",
    operation_description="""
    Sube un archivo de audio y espera a que el procesamiento completo termine antes de responder.
    
    El endpoint realiza automáticamente:
    1. División del audio en chunks de 180 segundos
    2. Transcripción de cada chunk con Whisper
    3. Generación de resúmenes de cada chunk con Groq
    4. Creación de un resumen final usando el prompt personalizado
    
    ⏱️ El endpoint espera hasta 10 minutos para que el procesamiento termine.
    Si el procesamiento toma más tiempo, devuelve un código 202 y continúa en segundo plano.
    
    Códigos de respuesta:
    - 201: Procesamiento completado exitosamente
    - 202: Timeout (>10 minutos), procesamiento continúa en segundo plano
    - 400: Error de validación
    - 500: Error en el procesamiento
    """,
    tags=['Transcripciones'],
    manual_parameters=[
        openapi.Parameter(
            'audio_file',
            openapi.IN_FORM,
            description="Archivo de audio MP3 (máximo 300MB)",
            type=openapi.TYPE_FILE,
            required=True
        ),
        openapi.Parameter(
            'custom_prompt',
            openapi.IN_FORM,
            description="Prompt personalizado para el resumen final (opcional, máximo 1000 caracteres)",
            type=openapi.TYPE_STRING,
            required=False
        ),
    ],
    responses={
        201: openapi.Response(
            description="Audio procesado exitosamente con resumen completo",
            schema=TranscriptionHistorySerializer,
            examples={
                "application/json": {
                    "id": 25,
                    "audio_name": "economía.mp3",
                    "summary_content": "Resumen completo del audio con los puntos clave...",
                    "summary_prompt": "Resume los puntos clave del audio",
                    "status": "done",
                    "processing_time": 45.2
                }
            }
        ),
        202: openapi.Response(
            description="Timeout: El procesamiento excedió 10 minutos. Continúa en segundo plano.",
            examples={
                "application/json": {
                    "id": 25,
                    "audio_name": "economía.mp3",
                    "status": "processing",
                    "message": "El procesamiento está tomando más tiempo del esperado. Continúa en segundo plano.",
                    "processing_time": 600.5
                }
            }
        ),
        400: "Datos inválidos o formato de audio no soportado",
        401: "No autenticado",
        500: "Error en el servidor o procesamiento"
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated]) 
@parser_classes([MultiPartParser, FormParser])
def upload(request):
    """
    Endpoint sincrónico para subir audio y obtener transcripción con resumen.
    Espera hasta que el resumen esté completo antes de responder (máximo 10 minutos).
    """
    serializer = AudioCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    # Variable para almacenar el ID de la transcripción
    transcription_id = None
    
    try: 
        with transaction.atomic():
            # Extraer prompt personalizado del serializer
            custom_prompt = serializer.validated_data.get('custom_prompt', '').strip()
            
            # Remover custom_prompt del validated_data ya que no está en el modelo base
            validated_data = serializer.validated_data.copy()
            if 'custom_prompt' in validated_data:
                del validated_data['custom_prompt']
            
            # Crear transcripción
            transcription = Transcription.objects.create(
                user=request.user, 
                status="uploaded",
                **validated_data
            )
            transcription_id = transcription.id
            
            # Guardar prompt personalizado si se proporcionó
            if custom_prompt:
                transcription.temp_custom_prompt = custom_prompt
                transcription.save(update_fields=['temp_custom_prompt'])
                logger.info(f"Custom prompt saved for transcription {transcription.id}: {custom_prompt[:50]}...")
            
            # Calculate total duration
            try:
                audio_file = MutagenFile(transcription.audio_file.path)
                if audio_file and audio_file.info:
                    duration = float(getattr(audio_file.info, "length", 0.0))
                    transcription.total_duration = int(duration) if duration else None
                    transcription.save(update_fields=['total_duration'])
            except Exception as e:
                logger.warning(f"Error calculating duration for transcription {transcription.id}: {e}")
            
            # Automatically trigger chunking
            try:
                chunking_service = ChunkingService()
                chunks = chunking_service.chunk_transcription(transcription, seconds_per_chunk=180)
                transcription.status = "chunked"
                transcription.save(update_fields=['status'])
                
                # Auto-start transcription after chunking
                try:
                    # Import here to avoid circular imports
                    from apps.api.tasks import transcribe_chunk
                    
                    # Update status to transcribing
                    transcription.status = "transcribing" 
                    transcription.save(update_fields=['status'])
                    
                    # Enqueue all chunks for transcription
                    enqueued_count = 0
                    for chunk in chunks:
                        try:
                            # Use default model and language from request or defaults
                            model_name = request.data.get('model', 'base')
                            language = request.data.get('language', 'es')
                            transcribe_chunk.delay(chunk.id, model_name, language)
                            enqueued_count += 1
                        except Exception as e:
                            logger.error(f"Failed to enqueue task for chunk {chunk.id}: {e}")
                    
                    logger.info(f"Auto-started transcription for {enqueued_count} chunks of transcription {transcription.id}")
                    
                except Exception as e:
                    logger.error(f"Failed to auto-start transcription for {transcription.id}: {e}")
                    # Don't fail the upload, just log the error
                    transcription.status = "chunked"  # Revert to chunked status
                    transcription.save(update_fields=['status'])
                
            except Exception as e:
                logger.error(f"Error chunking transcription {transcription.id}: {e}")
                transcription.status = "failed"
                transcription.save(update_fields=['status'])
                return Response(
                    {"error": "Upload successful but chunking failed. Please try manual rechunking."}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        # La transacción ya se completó, ahora esperamos de forma sincrónica
        # Configuración de timeout y polling
        TIMEOUT_SECONDS = 600  # 10 minutos
        POLL_INTERVAL = 3  # Verificar cada 3 segundos
        
        start_time = time.time()
        logger.info(f"Starting synchronous wait for transcription {transcription_id}")
        
        # Esperar hasta que el resumen esté completo o se alcance el timeout
        while True:
            elapsed_time = time.time() - start_time
            
            # Verificar timeout
            if elapsed_time > TIMEOUT_SECONDS:
                logger.warning(f"Timeout reached for transcription {transcription_id} after {elapsed_time:.2f}s")
                # Refrescar transcripción desde la base de datos
                transcription = Transcription.objects.get(id=transcription_id)
                return Response({
                    'id': transcription.id,
                    'audio_name': transcription.audio_file.name.split('/')[-1],
                    'status': 'processing',
                    'message': 'El procesamiento está tomando más tiempo del esperado. Continúa en segundo plano.',
                    'processing_time': elapsed_time
                }, status=status.HTTP_202_ACCEPTED)
            
            # Verificar si el resumen está completo
            try:
                # Refrescar transcripción desde la base de datos en cada iteración
                transcription = Transcription.objects.get(id=transcription_id)
                
                # Verificar si la transcripción está completa (status = 'done')
                if transcription.status == 'done':
                    # Verificar que el Summary existe y tiene contenido
                    try:
                        summary = Summary.objects.get(transcription=transcription)
                        if summary.header:  # El resumen está en el campo 'header'
                            # Resumen completo, devolver respuesta
                            logger.info(f"Summary completed for transcription {transcription_id} in {elapsed_time:.2f}s")
                            response_serializer = TranscriptionHistorySerializer(transcription)
                            response_data = response_serializer.data
                            response_data['processing_time'] = round(elapsed_time, 2)
                            return Response(response_data, status=status.HTTP_201_CREATED)
                    except Summary.DoesNotExist:
                        # Summary aún no existe pero status es 'done' (caso extraño)
                        logger.warning(f"Transcription {transcription_id} marked as 'done' but Summary not found")
                        pass
                
                # Verificar si hubo un error en el procesamiento
                elif transcription.status == 'failed' or transcription.status == 'error':
                    logger.error(f"Transcription {transcription_id} failed with status: {transcription.status}")
                    return Response({
                        'id': transcription.id,
                        'audio_name': transcription.audio_file.name.split('/')[-1],
                        'status': 'error',
                        'message': 'Error al generar el resumen',
                        'processing_time': elapsed_time
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                    
            except Transcription.DoesNotExist:
                logger.error(f"Transcription {transcription_id} not found during polling")
                return Response(
                    {"error": "Transcription not found"}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # Esperar antes de la siguiente verificación
            time.sleep(POLL_INTERVAL)

    except Exception as e:
        logger.error(f"Error processing upload: {e}", exc_info=True)
        return Response(
            {"error": f"Error processing file: {str(e)}"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@swagger_auto_schema(
    method='get',
    operation_summary="Listar historial de transcripciones",
    operation_description="""
    Obtiene el historial completo de transcripciones del usuario autenticado.
    
    Incluye:
    - Nombre del archivo de audio
    - Contenido del resumen final (si está disponible)
    - Prompt usado para generar el resumen
    - Estado del procesamiento
    - Fecha de creación
    
    Los resultados se ordenan por fecha de creación (más recientes primero).
    """,
    tags=['Transcripciones'],
    responses={
        200: openapi.Response(
            description="Lista de transcripciones con resúmenes",
            schema=TranscriptionHistorySerializer(many=True),
            examples={
                "application/json": [
                    {
                        "id": 50,
                        "audio_name": "economía.mp3",
                        "summary_content": "Resumen final del audio que destaca los puntos clave...",
                        "summary_prompt": "Resume los puntos clave y conceptos importantes del audio",
                        "status": "done",
                        "created_at": "2025-11-26T11:00:00Z"
                    },
                    {
                        "id": 49,
                        "audio_name": "conferencia.mp3",
                        "summary_content": None,
                        "summary_prompt": None,
                        "status": "transcribing",
                        "created_at": "2025-11-26T10:45:00Z"
                    }
                ]
            }
        ),
        401: "No autenticado"
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_transcriptions(request):
    """
    List all transcriptions with summaries for the authenticated user.
    Returns a history view with audio name, summary content, and metadata.
    """
    transcriptions = Transcription.objects.filter(user=request.user).order_by('-created_at')
    serializer = TranscriptionHistorySerializer(transcriptions, many=True)
    return Response(serializer.data)