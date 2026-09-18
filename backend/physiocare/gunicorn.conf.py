"""Gunicorn production configuration for PhysioCare.

IMPORTANT FOR SSE (Server-Sent Events):
Standard Gunicorn sync workers (gunicorn.workers.sync.SyncWorker) block 1 worker process
per open stream. Long-running SSE connections (/api/v1/me/events/) will quickly exhaust
all available sync workers, freezing the rest of the REST API.

To serve SSE reliably without worker starvation:
- Use worker_class = 'uvicorn.workers.UvicornWorker'
- Point Gunicorn to the ASGI application: physiocare.asgi:application
"""

import os

worker_class = os.getenv('GUNICORN_WORKER_CLASS', 'uvicorn.workers.UvicornWorker')

bind = os.getenv('GUNICORN_BIND', '0.0.0.0:8000')

workers = int(os.getenv('WEB_CONCURRENCY', os.getenv('GUNICORN_WORKERS', '4')))

timeout = int(os.getenv('GUNICORN_TIMEOUT', '120'))

keepalive = int(os.getenv('GUNICORN_KEEPALIVE', '75'))

proc_name = 'physiocare_api'

accesslog = '-'
errorlog = '-'
loglevel = os.getenv('GUNICORN_LOG_LEVEL', 'info')
