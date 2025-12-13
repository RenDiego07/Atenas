from django.urls import path
from .views import upload, list_transcriptions

urlpatterns = [
    path('upload/', upload, name='transcription-upload'),
    path('', list_transcriptions, name='transcription-list'),
]