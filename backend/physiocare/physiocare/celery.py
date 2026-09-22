import os

from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'physiocare.settings')

app: Celery = Celery('physiocare')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self: object) -> None:
    """Zadanie pomocnicze Celery służące do weryfikacji prawidłowego działania workera.

    Args:
        self (object): Instancja wykonawcza zadania Celery.
    """
    print(f'Request: {self.request!r}')
