import multiprocessing

bind = '127.0.0.1:3031'
workers = multiprocessing.cpu_count() * 2 + 1
#log_file = '/var/log/gunicorn-manabi.log'
logfile = '/var/log/manabi/gunicorn.log'
pid = '/tmp/gunicorn-manabi.pid'

