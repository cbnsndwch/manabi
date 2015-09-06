#!/usr/bin/env python

import sys

from os.path import abspath, dirname, join
import os


def add_path(p):
    if p in sys.path:
        sys.path.remove(p)
    sys.path.insert(0, p)


def remove_path(p):
    if p in sys.path:
        sys.path.remove(p)


remove_path(os.path.dirname(os.path.dirname(__file__)))

add_path(join(os.path.dirname(__file__), 'manabi'))
add_path(os.path.dirname(__file__))


if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "manabi.settings")

    from django.core.management import execute_from_command_line

    #from django.conf import settings
    #apps_path = join(settings.PROJECT_ROOT, "apps")
    #if apps_path not in sys.path:
    #    sys.path.insert(0, apps_path)

    #for p in sys.path: print p

    execute_from_command_line(sys.argv)
