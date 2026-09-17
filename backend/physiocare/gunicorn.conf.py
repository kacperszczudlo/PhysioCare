import os

# Worker class - MUST be UvicornWorker to support async SSE streams without worker starvation
worker_class: str = os.getenv('GUNICORN_WORKER_CLASS', 'uvicorn.workers.UvicornWorker')

# Binding
bind: str = os.getenv('GUNICORN_BIND', '0.0.0.0:8000')

# Number of worker processes (default: 4 or WEB_CONCURRENCY env)
workers: int = int(os.getenv('WEB_CONCURRENCY', os.getenv('GUNICORN_WORKERS', '4')))

# Timeout for workers (in seconds). SSE streams use heartbeat frames, but keep timeout reasonable.
timeout: int = int(os.getenv('GUNICORN_TIMEOUT', '120'))

# Keepalive connection duration
keepalive: int = int(os.getenv('GUNICORN_KEEPALIVE', '75'))

# Process naming
proc_name: str = 'physiocare_api'

# Logging
accesslog: str = '-'
errorlog: str = '-'
loglevel: str = os.getenv('GUNICORN_LOG_LEVEL', 'info')
