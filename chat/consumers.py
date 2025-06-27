import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import json
from channels.generic.websocket import AsyncWebsocketConsumer

from rest_framework_simplejwt.tokens import UntypedToken
from django.contrib.auth import get_user_model
from channels.db import database_sync_to_async
from jwt import decode as jwt_decode
from django.conf import settings

from .models import ChatMessage

User = get_user_model()

# Temporary in-memory user tracking (for dev)
ONLINE_USERS = {}  # { room_id: set(usernames) }

def get_cookie(headers, key):
    for header in headers:
        if header[0] == b'cookie':
            cookies = header[1].decode()
            for item in cookies.split(';'):
                if item.strip().startswith(key + "="):
                    return item.strip().split('=', 1)[1]
    return None



class VideoConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f"meeting_{self.room_id}"

        # Extract JWT from cookies
        token = get_cookie(self.scope["headers"], "access")
        self.user = await self.get_user_from_token(token)

        if not self.user or self.user.is_anonymous:
            await self.close()
            return

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        await self.add_online_user(self.room_id, self.user.username)
        await self.send_online_users()

        print(f"✅ {self.user.username} connected to {self.room_group_name}")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        await self.remove_online_user(self.room_id, self.user.username)
        await self.send_online_users()

        print(f"❌ {self.user.username} disconnected from {self.room_group_name}")

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message = data.get("message", "")

            if self.user and not self.user.is_anonymous:
                # Save to DB
                await database_sync_to_async(ChatMessage.objects.create)(
                    room_id=self.room_id,
                    user=self.user.username,
                    message=message
                )

                # Broadcast
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'broadcast_message',
                        'message': message,
                        'user': self.user.username
                    }
                )
        except Exception as e:
            print(f"[receive error] {str(e)}")

    async def broadcast_message(self, event):
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'user': event.get('user')
        }))

    async def online_users(self, event):
        await self.send(text_data=json.dumps({
            'type': 'online_users',
            'users': event['users']
        }))

    async def send_online_users(self):
        users = list(ONLINE_USERS.get(self.room_id, set()))
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'online_users',
                'users': users
            }
        )

    @database_sync_to_async
    def get_user_from_token(self, token):
        from django.contrib.auth.models import AnonymousUser
        try:
            UntypedToken(token)
            decoded = jwt_decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            user_id = decoded.get("user_id")
            return User.objects.get(id=user_id)
        except:
            return AnonymousUser()

    @database_sync_to_async
    def add_online_user(self, room_id, username):
        if room_id not in ONLINE_USERS:
            ONLINE_USERS[room_id] = set()
        ONLINE_USERS[room_id].add(username)

    @database_sync_to_async
    def remove_online_user(self, room_id, username):
        if room_id in ONLINE_USERS:
            ONLINE_USERS[room_id].discard(username)
