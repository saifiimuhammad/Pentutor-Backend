from rest_framework import serializers
from .models import Application


class ApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Application
        fields = ["id", "job", "message", "status", "applied_at"]
        read_only_fields = ["status", "applied_at"]
