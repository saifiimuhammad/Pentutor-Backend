# meetings/urls.py

from django.urls import path
from .views import ChatHistoryView

urlpatterns = [
    path('chat/<str:room_id>/', ChatHistoryView.as_view(), name='chat-history'),
]
