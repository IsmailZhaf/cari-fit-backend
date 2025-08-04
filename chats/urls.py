from django.urls import path

from .views import ChatView

urlpatterns = [path("chat/<str:document_id>/", ChatView.as_view(), name="chat")]
