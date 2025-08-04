from django.urls import path
from .consumer import NotificationConsumer, ChatConsumer

websocket_urlpatterns = [
    path("ws/notification/", NotificationConsumer.as_asgi()),
    path("ws/chat/<str:document_id>/", ChatConsumer.as_asgi())
]