from rest_framework import serializers
from .models import WhiteboardSnapshot

class WhiteboardSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = WhiteboardSnapshot
        fields = '__all__'