import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import WhiteboardSnapshot
from meetings.models import Meeting
from asgiref.sync import sync_to_async

class WhiteboardConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.meeting_id = self.scope['url_route']['kwargs']['meeting_id']
        self.room_group_name = f'whiteboard_{self.meeting_id}'

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        # Load last snapshot if available
        snapshot = await self.get_latest_snapshot(self.meeting_id)
        if snapshot:
            await self.send(text_data=json.dumps({
                'type': 'load',
                'data': snapshot
            }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data_json = json.loads(text_data)
        msg_type = data_json.get('type')
        whiteboard_data = data_json.get('data')

        if msg_type == 'update':
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'whiteboard_update',
                    'data': whiteboard_data,
                }
            )

            # Save to DB
            user = self.scope["user"] if self.scope["user"].is_authenticated else None
            await self.save_snapshot(self.meeting_id, whiteboard_data, user)

    async def whiteboard_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'update',
            'data': event['data']
        }))

    @sync_to_async
    def get_latest_snapshot(self, meeting_id):
        try:
            snapshot = WhiteboardSnapshot.objects.filter(meeting_id=meeting_id).latest('created_at')
            return snapshot.data
        except WhiteboardSnapshot.DoesNotExist:
            return None

    @sync_to_async
    def save_snapshot(self, meeting_id, data, user):
        try:
            meeting = Meeting.objects.get(id=meeting_id)
            WhiteboardSnapshot.objects.create(
                meeting=meeting,
                data=data,
                created_by=user
            )
        except Meeting.DoesNotExist:
            pass
