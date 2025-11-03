from django.urls import path
from .views import upload, list_transcriptions, get_transcription, manual_chunk, list_chunks, transcribe

urlpatterns = [
    path('upload/', upload, name='transcription-upload'),
    path('', list_transcriptions, name='transcription-list'),
    path('<int:pk>/', get_transcription, name='transcription-detail'),
    path('<int:pk>/chunk/', manual_chunk, name='transcription-chunk'),
    path('<int:pk>/transcribe/', transcribe, name='transcription-transcribe'),
    path('<int:pk>/chunks/', list_chunks, name='transcription-chunks'),
]