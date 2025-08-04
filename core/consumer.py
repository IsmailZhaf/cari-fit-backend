from channels.generic.websocket import AsyncWebsocketConsumer
import json
from chats.tasks import process_chat
from cv.models import CV
from asgiref.sync import sync_to_async

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        await self.channel_layer.group_add(
            'notification',
            self.channel_name
        )
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard('notification', self.channel_name)

    async def send_notification(self,event):
        data = event['data']
        await self.send(text_data=json.dumps(data))

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.document_id = self.scope['url_route']['kwargs']['document_id']
        self.group_name = f"chat_{self.document_id}"

        await self.accept()
        await self.channel_layer.group_add("chat", self.channel_name)

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("chat", self.channel_name)

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json.get("message")
        user = self.scope["user"]
        print('user', user)

        try:
            cv = await sync_to_async(CV.objects.get)(user_id=user.id)
            cv_id = cv.id
        except CV.DoesNotExist:
            await self.send(text_data=json.dumps({"message": "CV tidak ditemukan untuk user ini."}))
            return

        process_chat(message, self.document_id, cv_id)



    async def send_message(self, event):
        message = event["message"]
        await self.send(text_data=json.dumps({"message": message}))
