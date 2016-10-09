import multiprocessing

bind = '127.0.0.1:3031'
workers = multiprocessing.cpu_count() * 2
#log_file = '/var/log/gunicorn-manabi.log'
errorlog = '/var/log/manabi/gunicorn.error.log'
pidfile = '/tmp/manabi-gunicorn.pid'

