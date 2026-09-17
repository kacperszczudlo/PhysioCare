import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'physiocare.settings')

application: object = get_wsgi_application()
