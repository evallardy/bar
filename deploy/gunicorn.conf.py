import multiprocessing
import os


bind = os.environ.get('BAR_GUNICORN_BIND', 'unix:/run/gunicorn-bar.sock')
workers = int(os.environ.get('BAR_GUNICORN_WORKERS', max(multiprocessing.cpu_count() // 2, 2)))
worker_class = os.environ.get('BAR_GUNICORN_WORKER_CLASS', 'sync')
timeout = int(os.environ.get('BAR_GUNICORN_TIMEOUT', '120'))
graceful_timeout = int(os.environ.get('BAR_GUNICORN_GRACEFUL_TIMEOUT', '30'))
keepalive = int(os.environ.get('BAR_GUNICORN_KEEPALIVE', '5'))
accesslog = os.environ.get('BAR_GUNICORN_ACCESSLOG', '/var/log/bar/gunicorn-access.log')
errorlog = os.environ.get('BAR_GUNICORN_ERRORLOG', '/var/log/bar/gunicorn-error.log')
capture_output = True
