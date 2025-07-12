from django.db import models
from django.contrib.auth import get_user_model
from meetings.models import Meeting

User = get_user_model()

class WhiteboardSnapshot(models.Model):
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE)
    data = models.JSONField()  
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)