import os
import raven

RAVEN_CONFIG = {
    'dsn': 'https://d074e80bd2b349118459c80495184cfd:5a9e697b456241d587fd62e27f8b6faa@sentry.io/105057',
    # If you are using git, you can also automatically configure the
    # release based on the git info.
    'release': raven.fetch_git_sha(os.path.dirname(__file__)),
}

REDIS = {
    'host': 'localhost',
    'port': 6378,
    'db'  : 0,
}

#SITE_MEDIA_ROOT = '/var/www/manabi/site_media'
SITE_MEDIA_ROOT = os.path.join(PROJECT_ROOT, 'site_media')
