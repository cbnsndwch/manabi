import os
import raven

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
