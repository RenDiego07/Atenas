from rest_framework import serializers
from apps.api.models import Transcription, TranscriptionChunk, Summary

class AudioCreateSerializer(serializers.ModelSerializer):
    audio_file = serializers.FileField()
    custom_prompt = serializers.CharField(
        max_length=1000, 
        required=False, 
        allow_blank=True, 
        help_text="Prompt personalizado para el resumen final (opcional)"
    )

    class Meta:
        model = Transcription
        fields = ('id','user' ,'total_duration', 'language', 'status', 'created_at', 'audio_file', 'custom_prompt')
        read_only_fields = ('id','user','total_duration', 'status', 'created_at', 'language')

    def validate_audio_file(self, file):
        allowed = ['mp3']
        file_extension = file.name.split('.')[-1].lower()
        if file_extension not in allowed:
            raise serializers.ValidationError('FORMATO DE AUDIO INCOMPATIBLE')
        if file.size > 300 * 1024 * 1024:
            raise serializers.ValidationError('EL AUDIO SOBREPASA LOS 300MB')
        return file


class TranscriptionHistorySerializer(serializers.ModelSerializer):
    """Serializer para historial de transcripciones con resúmenes incluidos"""
    audio_name = serializers.SerializerMethodField()
    summary_content = serializers.SerializerMethodField()
    summary_prompt = serializers.SerializerMethodField()
    
    class Meta:
        model = Transcription
        fields = ['id', 'audio_name', 'summary_content', 'summary_prompt', 'status', 'created_at']
        read_only_fields = fields
    
    def get_audio_name(self, obj):
        """Extraer nombre del archivo de audio"""
        if obj.audio_file:
            return obj.audio_file.name.split('/')[-1]
        return None
    
    def get_summary_content(self, obj):
        """Obtener contenido del resumen final si existe"""
        try:
            summary = Summary.objects.get(transcription=obj)
            return summary.header
        except Summary.DoesNotExist:
            return None
    
    def get_summary_prompt(self, obj):
        """Obtener prompt usado en el resumen"""
        try:
            summary = Summary.objects.get(transcription=obj)
            return summary.prompt
        except Summary.DoesNotExist:
            return None