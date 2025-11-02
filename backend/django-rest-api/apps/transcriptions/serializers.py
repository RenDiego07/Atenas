from rest_framework import serializers
from apps.api.models import Transcription

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