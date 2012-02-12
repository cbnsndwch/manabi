import multiprocessing

bind = '127.0.0.1:3031'
workers = multiprocessing.cpu_count() * 2 + 1
#log_file = '/var/log/gunicorn-manabi.log'
errorlog = '/var/log/manabi/gunicorn.error.log'
logfile = '/var/log/manabi/gunicorn.error.1.log'
log_file = '/var/log/manabi/gunicorn.error.2.log'
error_logfile = '/var/log/manabi/gunicorn.error.3.log'
pidfile = '/tmp/manabi-gunicorn.pid'

