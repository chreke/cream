"""
ASGI config for cream project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

from cream.telemetry import configure_logging, configure_telemetry

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cream.settings')

configure_telemetry()
application = get_asgi_application()
configure_logging()
