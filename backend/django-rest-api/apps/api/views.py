from rest_framework import viewsets
from .models import Summary
from .serializers import SummarySerializer

class SummaryViewSet(viewsets.ModelViewSet):
    queryset = Summary.objects.all()
    serializer_class = SummarySerializer

    def perform_create(self, serializer):
        serializer.save()

    def perform_update(self, serializer):
        serializer.save()

    def perform_destroy(self, instance):
        instance.delete()