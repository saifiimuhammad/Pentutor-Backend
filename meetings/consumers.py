import json
from channels.generic.websocket import AsyncWebsocketConsumer



class VideoConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f"meeting_{self.room_id}"

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        print(f"Websocket connected: {self.room_group_name}")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        print(f"[Disconnected] {self.room_group_name} | Code: {close_code}")

    
    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message = data.get("message", "")
            user = data.get("user")

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'broadcast_message',
                    'message': message,
                    'user': user
                }
            )
        except Exception as e:
            print(f"[receive error] {str(e)}")

    async def broadcast_message(self, event):
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'user': event['user']
        }))