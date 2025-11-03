from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser 
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from mutagen import File as MutagenFile
from apps.api.models import Transcription, TranscriptionChunk
from apps.api.services.chunking import ChunkingService
from apps.transcriptions.serializers import (
    AudioCreateSerializer, 
    TranscriptionDetailSerializer,
    ChunkRequestSerializer,
    TranscriptionChunkSerializer,
    TranscriptionRequestSerializer
)
import logging

logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([IsAuthenticated]) 
@parser_classes([MultiPartParser, FormParser])
def upload(request):
    serializer = AudioCreateSerializer(data=request.data)
    if serializer.is_valid():
        try: 
            with transaction.atomic():
                transcription = serializer.save(user=request.user, status="uploaded")
                
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
                    
                    # Return transcription with chunks
                    response_serializer = TranscriptionDetailSerializer(transcription)
                    return Response(response_serializer.data, status=status.HTTP_201_CREATED)
                    
                except Exception as e:
                    logger.error(f"Error chunking transcription {transcription.id}: {e}")
                    transcription.status = "failed"
                    transcription.save(update_fields=['status'])
                    return Response(
                        {"error": "Upload successful but chunking failed. Please try manual rechunking."}, 
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
    
        except Exception as e:
            logger.error(f"Error processing upload: {e}")
            return Response(
                {"error": f"Error processing file: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_transcriptions(request):
    """Listar transcripciones del usuario autenticado"""
    transcriptions = Transcription.objects.filter(user=request.user).order_by('-created_at')
    serializer = AudioCreateSerializer(transcriptions, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_transcription(request, pk):
    """Obtener una transcripción específica"""
    try:
        transcription = Transcription.objects.get(pk=pk, user=request.user)
        serializer = TranscriptionDetailSerializer(transcription)
        return Response(serializer.data)
    except Transcription.DoesNotExist:
        return Response(
            {'error': 'Transcripción no encontrada'}, 
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def manual_chunk(request, pk):
    """
    Manually (re)chunk a transcription.
    Query params: seconds_per_chunk (default 180), force (default false)
    """
    try:
        transcription = Transcription.objects.get(pk=pk, user=request.user)
    except Transcription.DoesNotExist:
        return Response(
            {'error': 'Transcription not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Parse request data
    serializer = ChunkRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    seconds_per_chunk = serializer.validated_data['seconds_per_chunk']
    force = serializer.validated_data['force']
    
    # Check if chunks already exist
    existing_chunks = TranscriptionChunk.objects.filter(transcription=transcription).exists()
    if existing_chunks and not force:
        return Response(
            {
                'error': 'Chunks already exist for this transcription. Use force=true to recreate.',
                'existing_chunks_count': TranscriptionChunk.objects.filter(transcription=transcription).count()
            },
            status=status.HTTP_409_CONFLICT
        )
    
    try:
        with transaction.atomic():
            # Delete existing chunks if force=true
            if existing_chunks and force:
                TranscriptionChunk.objects.filter(transcription=transcription).delete()
            
            # Perform chunking
            chunking_service = ChunkingService()
            chunks = chunking_service.chunk_transcription(transcription, seconds_per_chunk=seconds_per_chunk)
            
            # Update transcription status
            transcription.status = "chunked"
            transcription.save(update_fields=['status'])
            
            # Return chunk list
            chunk_serializer = TranscriptionChunkSerializer(chunks, many=True)
            return Response({
                'transcription_id': transcription.id,
                'chunks_created': len(chunks),
                'seconds_per_chunk': seconds_per_chunk,
                'chunks': chunk_serializer.data
            }, status=status.HTTP_201_CREATED)
            
    except Exception as e:
        logger.error(f"Error chunking transcription {transcription.id}: {e}")
        transcription.status = "failed"
        transcription.save(update_fields=['status'])
        return Response(
            {'error': f'Chunking failed: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def transcribe(request, pk):
    """
    Start transcription process for all chunks of a transcription.
    
    POST /api/transcriptions/{id}/transcribe/
    Optional JSON body: {"force": false, "model": "base", "language": "es"}
    
    - If force=false: only enqueue chunks with status in ["ready", "failed"]
    - If force=true: reset all chunks (status="ready", text=None) and enqueue all
    - Sets parent Transcription.status="transcribing"
    - Returns 202 Accepted with counts
    """
    try:
        transcription = Transcription.objects.get(pk=pk, user=request.user)
    except Transcription.DoesNotExist:
        return Response(
            {'error': 'Transcription not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Validate transcription has chunks
    if not transcription.chunks.exists():
        return Response(
            {'error': 'No chunks found. Please chunk the transcription first.'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Parse request data
    serializer = TranscriptionRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    force = serializer.validated_data['force']
    model_name = serializer.validated_data['model']
    language = serializer.validated_data['language']
    
    try:
        with transaction.atomic():
            # Update transcription status
            transcription.status = "transcribing"
            transcription.save(update_fields=['status'])
            
            chunks = TranscriptionChunk.objects.filter(transcription=transcription)
            
            if force:
                # Reset all chunks and enqueue all
                chunks.update(status="ready", text=None)
                chunks_to_enqueue = chunks
                logger.info(f"Force transcription: resetting {chunks.count()} chunks for transcription {transcription.id}")
            else:
                # Only enqueue ready/failed chunks
                chunks_to_enqueue = chunks.filter(status__in=["ready", "failed"])
                logger.info(f"Selective transcription: enqueuing {chunks_to_enqueue.count()} chunks for transcription {transcription.id}")
            
            # Enqueue Celery tasks for each chunk
            from apps.api.tasks import transcribe_chunk
            
            enqueued_count = 0
            for chunk in chunks_to_enqueue:
                try:
                    transcribe_chunk.delay(chunk.id, model_name, language)
                    enqueued_count += 1
                except Exception as e:
                    logger.error(f"Failed to enqueue transcription task for chunk {chunk.id}: {e}")
            
            # Get current status counts
            from django.db.models import Count, Q
            chunk_stats = chunks.aggregate(
                total=Count('id'),
                pending=Count('id', filter=Q(status__in=['ready', 'transcribing'])),
                done=Count('id', filter=Q(status='done')),
                failed=Count('id', filter=Q(status='failed'))
            )
            
            return Response({
                'status': 'transcribing',
                'transcription_id': transcription.id,
                'model': model_name,
                'language': language,
                'force_reset': force,
                'enqueued_tasks': enqueued_count,
                'pending': chunk_stats['pending'],
                'done': chunk_stats['done'],
                'failed': chunk_stats['failed'],
                'total': chunk_stats['total']
            }, status=status.HTTP_202_ACCEPTED)
            
    except Exception as e:
        logger.error(f"Error starting transcription for transcription {transcription.id}: {e}")
        transcription.status = "failed"
        transcription.save(update_fields=['status'])
        return Response(
            {'error': f'Failed to start transcription: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_chunks(request, pk):
    """List all chunks for a transcription"""
    try:
        transcription = Transcription.objects.get(pk=pk, user=request.user)
    except Transcription.DoesNotExist:
        return Response(
            {'error': 'Transcription not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    chunks = TranscriptionChunk.objects.filter(transcription=transcription).order_by('index')
    serializer = TranscriptionChunkSerializer(chunks, many=True)
    
    # Calculate progress statistics
    from django.db.models import Count, Q
    chunk_stats = chunks.aggregate(
        total=Count('id'),
        ready=Count('id', filter=Q(status='ready')),
        transcribing=Count('id', filter=Q(status='transcribing')),
        done=Count('id', filter=Q(status='done')),
        failed=Count('id', filter=Q(status='failed'))
    )
    
    return Response({
        'transcription_id': transcription.id,
        'transcription_status': transcription.status,
        'progress': {
            'total_chunks': chunk_stats['total'],
            'ready': chunk_stats['ready'],
            'transcribing': chunk_stats['transcribing'],
            'done': chunk_stats['done'],
            'failed': chunk_stats['failed'],
            'completion_percentage': round((chunk_stats['done'] / chunk_stats['total']) * 100, 1) if chunk_stats['total'] > 0 else 0
        },
        'chunks': serializer.data
    })