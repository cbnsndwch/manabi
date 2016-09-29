DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'manabi',
        'USER': 'alex',
        'PASSWORD': 'development',
        'HOST': 'localhost',
        'PORT': '5432',
    },
    'old': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'manabi-pre-data-loss',
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

DEVSERVER_MODULES = (
    'devserver.modules.sql.SQLRealTimeModule',
    'devserver.modules.sql.SQLSummaryModule',
    'devserver.modules.profile.ProfileSummaryModule',

    # Modules not enabled by default
    'devserver.modules.ajax.AjaxDumpModule',
    'devserver.modules.profile.MemoryUseModule',
    'devserver.modules.cache.CacheSummaryModule',
    'devserver.modules.profile.LineProfilerModule',
)
