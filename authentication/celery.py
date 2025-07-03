import os
from celery import Celery
from celery.schedules import crontab 

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'authentication.settings')

app = Celery('authentication')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'auto-renew-calendar-watch-daily': {
        'task': 'calendersync.tasks.auto_renew_calendar_watches',
        'schedule': crontab(hour=0, minute=0),  # runs daily at midnight
    },
}

app.conf.beat_schedule.update({
    'cleanup-expired-calendar-watches-daily': {
        'task': 'calendersync.tasks.cleanup_expired_calendar_channels',
        'schedule': crontab(hour=1, minute=0),  # every day at 1 AM
    },
})