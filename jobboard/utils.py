from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.utils.timezone import now
from django.core.mail import send_mail
from django.conf import settings

from .models import Notification


def send_notification(user, subject, message, url=None):
    Notification.objects.create(user=user, message=message, url=url)

    if user.email:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"user_{user.id}",
        {
            "type": "send_notification",
            "message": message,
            "url": url or "",
            "created_at": now().isoformat(),
        },
    )
