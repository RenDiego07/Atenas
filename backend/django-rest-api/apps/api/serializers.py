from rest_framework import serializers
from .models import Summary

class SummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Summary
        fields = '__all__'  # Specify the fields you want to include in the serialization