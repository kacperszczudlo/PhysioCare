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

# Worker class - MUST be UvicornWorker to support async SSE streams without worker starvation
worker_class = os.getenv('GUNICORN_WORKER_CLASS', 'uvicorn.workers.UvicornWorker')

# Binding
bind = os.getenv('GUNICORN_BIND', '0.0.0.0:8000')

# Number of worker processes (default: 4 or WEB_CONCURRENCY env)
workers = int(os.getenv('WEB_CONCURRENCY', os.getenv('GUNICORN_WORKERS', '4')))

# Timeout for workers (in seconds). SSE streams use heartbeat frames, but keep timeout reasonable.
timeout = int(os.getenv('GUNICORN_TIMEOUT', '120'))

# Keepalive connection duration
keepalive = int(os.getenv('GUNICORN_KEEPALIVE', '75'))

# Process naming
proc_name = 'physiocare_api'

# Logging
accesslog = '-'
errorlog = '-'
loglevel = os.getenv('GUNICORN_LOG_LEVEL', 'info')
