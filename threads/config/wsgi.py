"""WSGI config for threads project."""
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "threads.config.settings")

application = get_wsgi_application()
