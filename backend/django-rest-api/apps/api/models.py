from django.db import models
from django.contrib.auth.models import User   # ✅ built-in User model
from django.conf import settings


class Transcription(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="transcriptions")
    total_duration = models.IntegerField(null=True, blank=True)  
    language = models.CharField(max_length=40, blank=True, default="Spanish")
    status = models.CharField(max_length=40, default="queued")   
    created_at = models.DateTimeField(auto_now_add=True)
    audio_file = models.CharField(max_length=100)

class TranscriptionChunk(models.Model):
    transcription = models.ForeignKey(Transcription, on_delete=models.CASCADE, related_name = "chunks")
    start_time = models.IntegerField(null=True, blank=True)
    end_time = models.IntegerField(null=True, blank=True)
    text = models.TextField(blank=True, null=True)
    status = models.CharField(max_length = 40, default="queued")

class Summary(models.Model):
    transcription = models.ForeignKey(Transcription, on_delete=models.CASCADE, related_name = "summary")
    header = models.TextField(max_length= 50)
    url_link = models.TextField(max_length= 100)
    prompt = models.TextField(default= "GENERE UN RESUMEN DE ACUERDO AL SIGUIENTE TEXTO:")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.header