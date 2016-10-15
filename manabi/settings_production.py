import os
import raven

RAVEN_CONFIG = {
    'dsn': 'https://d074e80bd2b349118459c80495184cfd:5a9e697b456241d587fd62e27f8b6faa@sentry.io/105057',
    # If you are using git, you can also automatically configure the
    # release based on the git info.
    'release': raven.fetch_git_sha(os.path.join(os.path.dirname(__file__), '..')),
}

REDIS = {
    'host': 'localhost',
    'port': 6378,
    'db'  : 0,
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '127.0.0.1:11211',
    }
}
