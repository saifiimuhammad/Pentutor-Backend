from accounts.serializers import UserProfileSerializer
from rest_framework import serializers
from .models import Meeting,Participant

class MeetingSerializer(serializers.ModelSerializer):
    """Meeting serializer with host info"""
    host = UserProfileSerializer(read_only=True)
    participants_count = serializers.SerializerMethodField()
    is_active = serializers.SerializerMethodField()
    
    class Meta:
        model = Meeting
        fields = [
            'id', 'meeting_id', 'title', 'password', 'meeting_type', 
            'status', 'host', 'max_participants', 'is_waiting_room_enabled',
            'allow_participant_share_screen', 'allow_participant_unmute',
            'enable_chat', 'enable_reactions', 'scheduled_time', 
            'started_at', 'ended_at', 'created_at', 'participants_count',
            'is_active'
        ]
        read_only_fields = [
            'id', 'meeting_id', 'password', 'host', 'status', 
            'started_at', 'ended_at', 'created_at'
        ]
    
    def get_participants_count(self, obj):
        """Get count of active participants"""
        return obj.participants.filter(left_at__isnull=True).count()
    
    def get_is_active(self, obj):
        """Check if meeting is currently active"""
        return obj.status == 'active'

class ParticipantSerializer(serializers.ModelSerializer):
    """Participant serializer with user info"""
    user = UserProfileSerializer(read_only=True)
    is_active = serializers.SerializerMethodField()
    duration_minutes = serializers.SerializerMethodField()
    
    class Meta:
        model = Participant
        fields = [
            'id', 'user', 'role', 'is_muted', 'is_video_on', 
            'is_hand_raised', 'is_sharing_screen', 'joined_at', 
            'left_at', 'is_active', 'duration_minutes'
        ]
        read_only_fields = [
            'id', 'user', 'joined_at', 'left_at'
        ]
    
    def get_is_active(self, obj):
        """Check if participant is currently in meeting"""
        return obj.left_at is None
    
    def get_duration_minutes(self, obj):
        """Calculate how long participant has been in meeting"""
        if obj.left_at:
            duration = obj.left_at - obj.joined_at
        else:
            from django.utils import timezone
            duration = timezone.now() - obj.joined_at
        return int(duration.total_seconds() / 60)


# Create Meeting Serializer (for API input)
class CreateMeetingSerializer(serializers.Serializer):
    """Serializer for creating new meeting"""
    title = serializers.CharField(max_length=200, required=False)
    meeting_type = serializers.ChoiceField(
        choices=['instant', 'scheduled'], 
        default='instant'
    )
    scheduled_time = serializers.DateTimeField(required=False)
    max_participants = serializers.IntegerField(default=100, min_value=2, max_value=500)
    waiting_room = serializers.BooleanField(default=False)
    allow_unmute = serializers.BooleanField(default=True)
    allow_screen_share = serializers.BooleanField(default=True)
    enable_chat = serializers.BooleanField(default=True)
    enable_reactions = serializers.BooleanField(default=True)
    password = serializers.CharField(max_length=20, required=False, allow_blank=True)
    
    def validate_scheduled_time(self, value):
        """Validate scheduled time is in future"""
        if value:
            from django.utils import timezone
            if value <= timezone.now():
                raise serializers.ValidationError(
                    "Scheduled time must be in the future"
                )
        return value
    
    def validate(self, data):
        """Validate meeting data"""
        if data.get('meeting_type') == 'scheduled' and not data.get('scheduled_time'):
            raise serializers.ValidationError(
                "Scheduled time is required for scheduled meetings"
            )
        return data

# Join Meeting Serializer
class JoinMeetingSerializer(serializers.Serializer):
    """Serializer for joining meeting"""
    name = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    password = serializers.CharField(max_length=20, required=False, allow_blank=True)
    
    def validate_password(self, value):
        """Clean password input"""
        return value.strip() if value else ''

# Reaction Serializer  
class ReactionSerializer(serializers.Serializer):
    """Serializer for adding reactions"""
    reaction_type = serializers.ChoiceField(
        choices=['like', 'love', 'clap', 'laugh', 'wow', 'sad'],
        required=True
    )
