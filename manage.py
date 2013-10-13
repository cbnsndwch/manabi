#!/usr/bin/env python

import sys

from os.path import abspath, dirname, join
import os

#try:
#    import pinax
#except ImportError:
#    sys.stderr.write("Error: Can't import Pinax. Make sure you are in a virtual environment that has Pinax installed or create one with pinax-boot.py.\n")
#    sys.exit(1)


#sys.path.insert(0, join(settings.PINAX_ROOT, "apps"))


def add_path(p):
    if p in sys.path:
        sys.path.remove(p)
    sys.path.insert(0, p)

add_path(os.path.dirname(__file__))
#add_path(join(os.path.dirname(__file__), 'manabi'))


if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "manabi.settings")

    from django.core.management import execute_from_command_line

    #from django.conf import settings
    #apps_path = join(settings.PROJECT_ROOT, "apps")
    #if apps_path not in sys.path:
    #    sys.path.insert(0, apps_path)
     
    #for p in sys.path: print p

    execute_from_command_line(sys.argv)



#if __name__ == "__main__":
#    if 'DJANGO_SETTINGS_MODULE' not in os.environ:
#        os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

#    if '/etc/canvas/website' not in sys.path:
#        sys.path.append('/etc/canvas/website')

#    from django.conf import settings
#    apps_path = join(settings.PROJECT_ROOT, "apps")
#    if apps_path not in sys.path:
#        sys.path.insert(0, apps_path)

#    from django.core.management import execute_from_command_line

#    execute_from_command_line(sys.argv)

