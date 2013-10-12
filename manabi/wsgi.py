import os

from dj_static import Cling

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'manabi.settings')

# This application object is used by the development server
# as well as any WSGI server configured to use this file.
from django.core.wsgi import get_wsgi_application

application = Cling(get_wsgi_application())

