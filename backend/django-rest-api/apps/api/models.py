from django.db import models
from django.contrib.auth.models import User   # ✅ built-in User model
from django.conf import settings


class Transcription(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="transcriptions")
    total_duration = models.IntegerField(null=True, blank=True)  
    language = models.CharField(max_length=40, blank=True, default="Spanish")
    status = models.CharField(max_length=40, default="queued")   
    created_at = models.DateTimeField(auto_now_add=True)
    audio_file = models.FileField(upload_to='audios/')
    # Campo para pasar prompt personalizado através del pipeline automático
    temp_custom_prompt = models.TextField(max_length=1000, blank=True, null=True)

class TranscriptionChunk(models.Model):
    transcription = models.ForeignKey(Transcription, on_delete=models.CASCADE, related_name="chunks")
    start_time = models.IntegerField(null=True, blank=True)  # start time in seconds
    end_time = models.IntegerField(null=True, blank=True)    # end time in seconds
    duration_sec = models.FloatField(null=True, blank=True)  # actual chunk duration in seconds
    text = models.TextField(blank=True, null=True)           # transcribed text (future use)
    status = models.CharField(max_length=40, default="ready")
    index = models.PositiveIntegerField(null=True, blank=True)
    file = models.FileField(upload_to='audios/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    summary = models.TextField(blank=True, null = True)

    class Meta:
        unique_together = ('transcription', 'index')
        ordering = ['index']

    def __str__(self):
        return f"Chunk {self.index} of Transcription {self.transcription.id}"

class Summary(models.Model):
    transcription = models.ForeignKey(Transcription, on_delete=models.CASCADE, related_name = "summary")
    header = models.TextField(max_length= 50)
    url_link = models.TextField(max_length= 100)
    prompt = models.TextField(default= "GENERE UN RESUMEN DE ACUERDO AL SIGUIENTE TEXTO:")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.header