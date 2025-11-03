from rest_framework import serializers
from apps.api.models import Transcription
from apps.api.models import TranscriptionChunk

class AudioCreateSerializer(serializers.ModelSerializer):
    audio_file = serializers.FileField()

    class Meta:
        model = Transcription
        fields = ('id','user' ,'total_duration', 'language', 'status', 'created_at', 'audio_file')
        read_only_fields = ('id','user','total_duration', 'status', 'created_at', 'language')

    def validate_audio_file(self, file):
        allowed = ['mp3']
        file_extension = file.name.split('.')[-1].lower()
        if file_extension not in allowed:
            raise serializers.ValidationError('FORMATO DE AUDIO INCOMPATIBLE')
        if file.size > 300 * 1024 * 1024:
            raise serializers.ValidationError('EL AUDIO SOBREPASA LOS 300MB')
        return file 
    
class TranscriptionChunkSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = TranscriptionChunk
        fields = ['id','index','file','file_url','start_time','end_time','duration_sec','status','text','created_at']
        read_only_fields = fields
        
    def get_file_url(self, obj):
        """Return the URL of the chunk file if it exists"""
        if obj.file:
            return obj.file.url
        return None

        
class TranscriptionDetailSerializer(serializers.ModelSerializer):
    chunks = TranscriptionChunkSerializer(many=True, read_only=True)
    class Meta:
        model = Transcription
        fields = ['id','user','audio_file','total_duration','language','status','created_at','chunks']
        read_only_fields = fields


class ChunkRequestSerializer(serializers.Serializer):
    seconds_per_chunk = serializers.IntegerField(default=180, min_value=30, max_value=600)
    force = serializers.BooleanField(default=False)
    
    def validate_seconds_per_chunk(self, value):
        """Ensure chunk duration is reasonable"""
        if value < 30:
            raise serializers.ValidationError("Chunk duration must be at least 30 seconds")
        if value > 600:
            raise serializers.ValidationError("Chunk duration must not exceed 600 seconds")
        return value


class TranscriptionRequestSerializer(serializers.Serializer):
    force = serializers.BooleanField(default=False)
    model = serializers.ChoiceField(
        choices=[
            ('tiny', 'Tiny (~39MB, fastest)'),
            ('base', 'Base (~74MB, balanced)'), 
            ('small', 'Small (~244MB, better accuracy)'),
            ('medium', 'Medium (~769MB, high accuracy)'),
            ('large', 'Large (~1550MB, highest accuracy)')
        ],
        default='base',
        help_text="Whisper model to use for transcription"
    )
    language = serializers.CharField(
        max_length=10, 
        default='es',
        help_text="Language code for transcription (es, en, etc.)"
    )
    
    def validate_language(self, value):
        """Validate language code"""
        # Common language codes supported by Whisper
        supported_languages = [
            'es', 'en', 'fr', 'de', 'it', 'pt', 'ru', 'ja', 'ko', 'zh', 
            'ar', 'tr', 'pl', 'ca', 'nl', 'sv', 'he', 'da', 'fi', 'no'
        ]
        if value not in supported_languages:
            # Don't fail validation, just warn - Whisper supports many languages
            pass
        return value.lower()