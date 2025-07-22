from rest_framework import serializers
from .models import Application, EmployerProfile


class ApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Application
        fields = ["id", "job", "message", "status", "applied_at"]
        read_only_fields = ["status", "applied_at"]


class EmployerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployerProfile
        fields = "__all__"
        read_only_fields = ["user"]
