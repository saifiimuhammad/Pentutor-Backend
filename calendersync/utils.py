from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from calendersync.models import GoogleCredentials
from django.utils.timezone import is_naive, make_aware
from meetings.models import Meeting 
import pytz


from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from calendersync.models import GoogleCredentials

def build_service(user):
    try:
        creds_obj = GoogleCredentials.objects.get(user=user)

        creds = Credentials(
            token=creds_obj.token,
            refresh_token=creds_obj.refresh_token,
            token_uri=creds_obj.token_uri,
            client_id=creds_obj.client_id,
            client_secret=creds_obj.client_secret,
            scopes=creds_obj.scopes.split(','),
        )

        if creds.expired and creds.refresh_token:
            creds.refresh(Request())

        return build('calendar', 'v3', credentials=creds)

    except GoogleCredentials.DoesNotExist:
        return None




def create_google_event(user, meeting):
    service = build_service(user)
    if not service:
        print("❌ No credentials found.")
        return

    # Ensure timezone-aware datetime
    if is_naive(meeting.start_time):
        meeting.start_time = make_aware(meeting.start_time, timezone=pytz.timezone('Asia/Karachi'))
    if is_naive(meeting.end_time):
        meeting.end_time = make_aware(meeting.end_time, timezone=pytz.timezone('Asia/Karachi'))

    event = {
        'summary': meeting.title,
        'description': f'Join meeting: {meeting.join_url}',
        'start': {
            'dateTime': meeting.start_time.isoformat(),
            'timeZone': 'Asia/Karachi',
        },
        'end': {
            'dateTime': meeting.end_time.isoformat(),
            'timeZone': 'Asia/Karachi',
        },
        'attendees': [{'email': u.email} for u in meeting.participants.all()],
        'reminders': {'useDefault': True},
    }

    created_event = service.events().insert(calendarId='primary', body=event).execute()
    print("✅ Created Google Event:", created_event)

    # Save event ID to meeting
    meeting.google_event_id = created_event['id']
    meeting.save(update_fields=['google_event_id'])

def update_google_event(user, meeting):
    if not meeting.google_event_id:
        return

    service = build_service(user)
    if not service:
        print("❌ No credentials found.")
        return

    event_body = {
        'summary': meeting.title,
        'description': meeting.description or "",
        'start': {'dateTime': meeting.start_time.isoformat(), 'timeZone': 'Asia/Karachi'},
        'end': {'dateTime': meeting.end_time.isoformat(), 'timeZone': 'Asia/Karachi'},
    }

    service.events().update(
        calendarId='primary',
        eventId=meeting.google_event_id,
        body=event_body
    ).execute()

def delete_google_event(user, meeting):
    if not meeting.google_event_id:
        return

    service = build_service(user)
    if not service:
        print("❌ No credentials found.")
        return

    service.events().delete(
        calendarId='primary',
        eventId=meeting.google_event_id
    ).execute()
    if not meeting.google_event_id:
        return

    service = build_service(user)

    service.events().delete(
        calendarId='primary',
        eventId=meeting.google_event_id
    ).execute()