from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import  IsAuthenticated
from .serializers import MeetingSerializer
from .models import Meeting,Participant
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .serializers import MeetingSerializer, ParticipantSerializer,CreateMeetingSerializer,JoinMeetingSerializer
import random
from accounts.models import CustomUser
from django.utils.text import slugify
from calendersync.utils import create_google_event

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_meeting(request):
    """Create a new meeting"""
    serializer = CreateMeetingSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(
            {'errors': serializer.errors}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    data = serializer.validated_data
    
    # Create meeting
    meeting = Meeting.objects.create(
        host=request.user,
        title=data.get('title', f'{request.user.username}\'s Meeting'),
        meeting_type=data.get('meeting_type', 'instant'),
        scheduled_time=data.get('scheduled_time'),
        max_participants=data.get('max_participants', 100),
        is_waiting_room_enabled=data.get('waiting_room', False),
        allow_participant_share_screen=data.get('allow_screen_share', True),
        allow_participant_unmute=data.get('allow_unmute', True),
        enable_chat=data.get('enable_chat', True),
        enable_reactions=data.get('enable_reactions', True)
    )
    
    # Set custom password if provided
    if data.get('password'):
        meeting.password = data['password']
        meeting.save()
    print("Running create_google_event")
    create_google_event(request.user, meeting)
    print("Done create_google_event")

    # Host automatically joins as participant
    participant = Participant.objects.create(
        meeting=meeting,
        user=request.user,
        role='host'
    )
    
    # Start meeting if instant
    if meeting.meeting_type == 'instant':
        meeting.start_meeting()
    
    return Response({
        'google_event_id': meeting.google_event_id,
        'meeting_id': meeting.meeting_id,
        'password': meeting.password,
        'join_url': f'/meeting/join/{meeting.meeting_id}',
        'status': 'created',
        'meeting': MeetingSerializer(meeting).data,
        'participant': ParticipantSerializer(participant).data,
        'message': 'Meeting created successfully'
    }, status=status.HTTP_201_CREATED)

@api_view(['POST'])
@permission_classes([])
def join_meeting(request, meeting_id):
    """Join an existing meeting"""
    serializer = JoinMeetingSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(
            {'errors': serializer.errors}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        meeting = Meeting.objects.get(meeting_id=meeting_id)
        
        # Check if meeting exists and is active
        if meeting.status == 'ended':
            return Response({
                'error': 'Meeting has ended'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check password if provided
        password = serializer.validated_data.get('password', '')
        if meeting.password and password != meeting.password:
            return Response({
                'error': 'Invalid meeting password'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Check max participants
        active_participants = meeting.participants.filter(left_at__isnull=True).count()
        if active_participants >= meeting.max_participants:
            return Response({
                'error': 'Meeting is full'
            }, status=status.HTTP_400_BAD_REQUEST)
        # 👤 Get or create user (login or guest)
        if request.user.is_authenticated:
            user = request.user
        else:
            name = serializer.validated_data.get('name')
            username = slugify(name) + str(random.randint(1000, 9999))
            email = serializer.validated_data.get('email')
            user = CustomUser.objects.create_user(username=username, password=password,email=email)

        # Check if user already in meeting
        participant, created = Participant.objects.get_or_create(
            meeting=meeting,
            user=user,
            guest_name=name,
            defaults={'role': 'participant'}
        )
        
        if not created and participant.is_active:
            return Response({
                'error': 'You are already in this meeting'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Rejoin if previously left
        if not created:
            participant.left_at = None
            participant.save()
        
        # Start meeting if host joins
        if meeting.status == 'waiting' and participant.role == 'host':
            meeting.start_meeting()
        
        # Notify other participants
        channel_layer = get_channel_layer()
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                f'meeting_{meeting_id}',
                {
                    'type': 'participant_joined',
                    'participant': {
                        'id': participant.id,
                        'user': request.user.username,
                        'role': participant.role,
                        'joined_at': participant.joined_at.isoformat()
                    }
                }
            )
        
        return Response({
            # 'meeting': MeetingSerializer(meeting).data,
            'participant': ParticipantSerializer(participant).data,
            'message': 'Successfully joined meeting'
        }, status=status.HTTP_200_OK)
        
    except Meeting.DoesNotExist:
        return Response({
            'error': 'Meeting not found'
        }, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([])
def leave_meeting(request, meeting_id):
    """Leave a meeting"""
    guest_name = request.data.get('guest_name', None)
    user = request.user if request.user.is_authenticated else None
    try:
        participant = Participant.objects.get(
            meeting__meeting_id=meeting_id,
            guest_name=guest_name,
            left_at__isnull=True
        )
        
        participant.leave_meeting()
        
        # Notify other participants
        channel_layer = get_channel_layer()
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                f'meeting_{meeting_id}',
                {
                    'type': 'participant_left',
                    'participant_id': participant.id,
                    'user': request.user.username
                }
            )
        
        return Response({
            'message': 'Successfully left meeting'
        }, status=status.HTTP_200_OK)
        
    except Participant.DoesNotExist:
        return Response({
            'error': 'You are not in this meeting'
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def end_meeting(request, meeting_id):
    """End a meeting (only host can do this)"""
    try:
        participant = Participant.objects.get(
            meeting__meeting_id=meeting_id,
            user=request.user,
            role__in=['host', 'co_host'],
            left_at__isnull=True
        )
        
        meeting = participant.meeting
        meeting.end_meeting()
        
        # Notify all participants
        channel_layer = get_channel_layer()
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                f'meeting_{meeting_id}',
                {
                    'type': 'meeting_ended',
                    'ended_by': request.user.username,
                    'message': 'Meeting has been ended by host'
                }
            )
        
        return Response({
            'message': 'Meeting ended successfully'
        }, status=status.HTTP_200_OK)
        
    except Participant.DoesNotExist:
        return Response({
            'error': 'Only host or co-host can end meeting'
        }, status=status.HTTP_403_FORBIDDEN)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_meeting_participants(request, meeting_id):
    """Get list of all participants in meeting"""
    try:
        meeting = Meeting.objects.get(meeting_id=meeting_id)
        
        # Check if user is in meeting
        user_participant = meeting.participants.filter(
            user=request.user,
            left_at__isnull=True
        ).first()
        
        if not user_participant:
            return Response({
                'error': 'You are not in this meeting'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get all active participants
        participants = meeting.participants.filter(left_at__isnull=True)
        
        return Response({
            'participants': ParticipantSerializer(participants, many=True).data
        }, status=status.HTTP_200_OK)
        
    except Meeting.DoesNotExist:
        return Response({
            'error': 'Meeting not found'
        }, status=status.HTTP_404_NOT_FOUND)
