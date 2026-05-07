import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'
        self.user = self.scope['user']

        if self.user.is_anonymous:
            await self.close()
            return

        is_participant = await self.user_in_room()
        if not is_participant:
            await self.close()
            return

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get('action', 'message')

        if action == 'message':
            text = data.get('text', '').strip()
            if text:
                msg = await self.save_message(text)
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat_message',
                        'message': text,
                        'sender_id': self.user.id,
                        'sender_name': self.user.get_full_name() or self.user.email,
                        'sender_avatar': self.user.avatar.url if self.user.avatar else '',
                        'time': msg.created_at.strftime('%H:%M'),
                        'message_id': msg.id,
                    }
                )

        elif action == 'typing':
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_typing',
                    'user_id': self.user.id,
                    'user_name': self.user.get_full_name() or self.user.email,
                    'typing': data.get('typing', False),
                }
            )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))

    async def user_typing(self, event):
        await self.send(text_data=json.dumps(event))

    @database_sync_to_async
    def save_message(self, text):
        from .models import ChatRoom, Message
        room = ChatRoom.objects.get(id=self.room_id, participants=self.user)
        return Message.objects.create(room=room, sender=self.user, text=text)

    @database_sync_to_async
    def user_in_room(self):
        from .models import ChatRoom
        return ChatRoom.objects.filter(id=self.room_id, participants=self.user).exists()
