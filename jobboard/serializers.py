from rest_framework import serializers
from .models import Application, EmployerProfile, JobPost


class ApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Application
        fields = ["id", "job", "message", "status", "applied_at"]
        read_only_fields = ["status", "applied_at"]


class EmployerSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployerProfile
        fields = "__all__"


class JobPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobPost
        fields = "__all__"  # or choose specific fields
