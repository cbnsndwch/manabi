DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'manabi',
        'USER': 'alex',
        'PASSWORD': 'development',
        'HOST': 'localhost',
        'PORT': '5432',
    },
}

REDIS = {
    'host': 'localhost',
    'port': 6379,
    'db'  : 0,
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}
