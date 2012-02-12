from fabric.api import *


env.project_name = 'manabi'
env.hosts = ['alex@manabi.org']
env.home = '/home/alex/'
env.path = env.home + 'manabi'
env.virtualenv_path = '/home/alex/virtualenvs/manabi'


def upload_settings():
    put('settings.py', env.path)

def python(cmd, *args, **kwargs):
    return run('{0}/bin/python '.format(env.virtualenv_path) + cmd, *args, **kwargs)

def migrate():
    'Update the database'
    with cd(env.path):
        python('manage.py migrate')

def build_media():
    with cd(env.path):
        python('manage.py collectstatic --noinput')

def git_pull():
    with cd(env.path):
        run('git pull origin master')

def backup():
    with cd(env.home):
        sudo('cron/tarsnap_backup.sh')

def deploy():
    backup()
    git_pull()
    upload_settings()
    restart_webserver()

def full_deploy():
    deploy()
    build_media()
    
def restart_webserver():
    sudo('/etc/init.d/cherokee restart')
    #sudo('kill -9 `cat /tmp/cherokee-django.pid`')
    # do it gracefully (send HUP signal, wait 10-15s, then kill)
    with settings(warn_only=True):
        sudo('kill -HUP `cat /tmp/cherokee-gunicorn-manabi.pid`')
    run('wget manabi.org -O /dev/null')

def hard_restart_webserver():
    sudo('/etc/init.d/cherokee stop')
    sudo('kill -INT `cat /tmp/cherokee-gunicorn-manabi.pid`')
    sudo('/etc/init.d/cherokee restart')
    run('wget manabi.org -O /dev/null')

