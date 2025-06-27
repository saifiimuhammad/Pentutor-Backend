from django.shortcuts import render

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import ChatMessage

# Create your views here.

class ChatHistoryView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, room_id):
        # Pagination params
        page = int(request.GET.get("page", 1))
        page_size = int(request.GET.get("limit", 20))
        offset = (page - 1) * page_size

        # Filter messages for the room, latest first
        messages_qs = ChatMessage.objects.filter(room_id=room_id).order_by("-timestamp")
        total = messages_qs.count()

        # Paginating
        messages = messages_qs[offset:offset + page_size]

        # Response
        data = [
            {
                "user": msg.user,
                "message": msg.message,
                "timestamp": msg.timestamp
            }
            for msg in messages
        ]

        return Response({
            "messages": data,
            "total": total,
            "page": page,
            "limit": page_size
        })