from .models import UserActivity


def log_activity(user, activity):
    UserActivity.objects.create(user=user, activity=activity)
