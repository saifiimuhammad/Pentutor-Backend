"""
ASGI config for authentication project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/asgi/
"""

import os
import django
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

import whiteboard
import alerts
import jobboard

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "authentication.settings")
django.setup()

application = ProtocolTypeRouter(
    {
        "http": get_asgi_application(),
        "websocket": AuthMiddlewareStack(
            URLRouter(
                whiteboard.routing.websocket_urlpatterns,
                alerts.routing.websocket_urlpatterns,
                jobboard.routing.websocket_urlpatterns,
            )
        ),
    }
)
