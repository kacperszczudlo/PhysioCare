import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'physiocare.settings')

application: object = get_asgi_application()
