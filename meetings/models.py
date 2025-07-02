from django.db import models
from accounts.models import CustomUser
import uuid
import random
import string
from django.utils import timezone
# Create your models here.
    
class Meeting(models.Model):
    MEETING_STATUS = [
        ('waiting', 'Waiting Room'),
        ('active', 'Active'),
        ('ended', 'Ended'),
    ]
    
    MEETING_TYPES = [
        ('instant', 'Instant Meeting'),
        ('scheduled', 'Scheduled Meeting'),
    ]
    
    host = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='hosted_meetings')
    title = models.CharField(max_length=255)
    password = models.CharField(max_length=20, blank=True)
    meeting_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    meeting_type = models.CharField(max_length=20, choices=MEETING_TYPES, default='instant')
    is_active = models.BooleanField(default=True)
    status = models.CharField(max_length=20, choices=MEETING_STATUS, default='waiting')
    google_event_id = models.CharField(max_length=255, blank=True, null=True)

    # Meeting Settings
    max_participants = models.IntegerField(default=100)
    is_waiting_room_enabled = models.BooleanField(default=False)
    allow_participant_share_screen = models.BooleanField(default=True)
    allow_participant_unmute = models.BooleanField(default=True)
    enable_chat = models.BooleanField(default=True)
    enable_reactions = models.BooleanField(default=True)

     # Timestamps
    scheduled_time = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.meeting_id:
            self.meeting_id = self.generate_meeting_id()
        if not self.password:
            self.password = self.generate_password()
        super().save(*args, **kwargs)
    
    @staticmethod
    def generate_meeting_id():
        while True:
            meeting_id = ''.join(random.choices(string.digits, k=10))
            formatted_id = f"{meeting_id[:3]}-{meeting_id[3:6]}-{meeting_id[6:]}"
            if not Meeting.objects.filter(meeting_id=formatted_id).exists():
                return formatted_id
    
    @staticmethod
    def generate_password():
        return ''.join(random.choices(string.ascii_letters + string.digits, k=6))
    
    def start_meeting(self):
        self.status = 'active'
        self.started_at = timezone.now()
        self.save()
    
    def end_meeting(self):
        self.status = 'ended'
        self.ended_at = timezone.now()
        self.save()
        # Leave all participants
        self.participants.filter(left_at__isnull=True).update(left_at=timezone.now())


    def __str__(self):
        return f"{self.title} - {self.host.email}"

    class Meta:
        ordering = ['-scheduled_time']


class Participant(models.Model):
    ROLES = [
        ('host', 'Host'),
        ('co_host', 'Co-Host'),
        ('participant', 'Participant'),
    ]
    
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, related_name='participants')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    guest_name = models.CharField(max_length=100, blank=True, null=True)
    role = models.CharField(max_length=20, choices=ROLES, default='participant')
    
    # Status Controls
    is_muted = models.BooleanField(default=False)
    is_video_on = models.BooleanField(default=True)
    is_hand_raised = models.BooleanField(default=False)
    is_sharing_screen = models.BooleanField(default=False)
    
    # Timestamps
    joined_at = models.DateTimeField(auto_now_add=True)
    left_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['meeting', 'user']
    
    def leave_meeting(self):
        self.left_at = timezone.now()
        self.is_sharing_screen = False
        self.save()
    
    @property
    def is_active(self):
        return self.left_at is None
