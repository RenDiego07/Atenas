from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser 
from rest_framework.permissions import IsAuthenticated
from mutagen import File as MutagenFile
from apps.api.models import Transcription 
from apps.transcriptions.serializers import AudioCreateSerializer

@api_view(['POST'])
@permission_classes([IsAuthenticated]) 
@parser_classes([MultiPartParser, FormParser])
def upload(request):
    serializer = AudioCreateSerializer(data = request.data)
    if serializer.is_valid():
        try: 
            transcription = serializer.save(user=request.user, status="uploaded")
            try:
                audio_file = MutagenFile(transcription.audio_file.path)
                if audio_file and audio_file.info:
                    duration = float(getattr(audio_file.info, "length", 0.0)) or None
                    transcription.total_duration = duration
            except Exception as e:
                print(f"Error calculando duración {e}")
            transcription.status = "queued"
            transcription.save()     
            response_data = AudioCreateSerializer(transcription).data
            return Response(response_data, status=status.HTTP_201_CREATED)
    
        except Exception as e:
            return Response({"error" : f"Error procesando archivo {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
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
        serializer = AudioCreateSerializer(transcription)
        return Response(serializer.data)
    except Transcription.DoesNotExist:
        return Response(
            {'error': 'Transcripción no encontrada'}, 
            status=status.HTTP_404_NOT_FOUND
        )