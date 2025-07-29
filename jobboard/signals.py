# in signals.py

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


@receiver(post_save, sender=Job)
def notify_matching_students(sender, instance, created, **kwargs):
    if not created:
        return

    job_tags = instance.tags.all()
    matching_students = StudentProfile.objects.filter(interests__in=job_tags).distinct()

    channel_layer = get_channel_layer()

    for student in matching_students:
        message = f"New job matched your interests: {instance.title}"

        # Save notification (optional)
        Notification.objects.create(user=student.user, message=message)

        # Send real-time via websocket
        async_to_sync(channel_layer.group_send)(
            f"user_{student.user.id}", {"type": "send_notification", "message": message}
        )
