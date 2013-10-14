# -*- coding: utf-8 -*-

import os.path
import posixpath
from socket import gethostname

LIVE_HOST = (gethostname() == 'aehlke.xen.prgmr.com')

#PINAX_ROOT = os.path.abspath(os.path.dirname(pinax.__file__))
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))

# tells Pinax to use the default theme
#PINAX_THEME = 'default'

DEBUG = not LIVE_HOST
TEMPLATE_DEBUG = not LIVE_HOST #DEBUG

# tells Pinax to serve media through django.views.static.serve.
#SERVE_MEDIA = not LIVE_HOST  #DEBUG

INTERNAL_IPS = (
    '127.0.0.1',
)

ADMINS = (
    ('alex', 'alex.ehlke@gmail.com'),
)

MANAGERS = ADMINS

import logging
if DEBUG:
    logging.basicConfig(
        level=logging.ERROR,
        format='%(asctime)s %(levelname)s %(message)s')
else:
    logging.basicConfig(
        level=logging.ERROR,
        format='%(asctime)s %(levelname)s %(message)s',
        filename='/var/log/python-manabi.log')

TIME_ZONE = 'UTC'
LANGUAGE_CODE = 'en'
SITE_ID = 1
USE_I18N = False

if LIVE_HOST:
    #SITE_MEDIA_ROOT = '/var/www/manabi/site_media'
    SITE_MEDIA_ROOT = os.path.join(PROJECT_ROOT, 'site_media')
else:
    SITE_MEDIA_ROOT = os.path.join(PROJECT_ROOT, 'site_media')

USE_X_FORWARDED_HOST = True

STATIC_ROOT = os.path.join(SITE_MEDIA_ROOT, 'static')
STATIC_URL = '/site_media/static/'

# Additional directories which hold static files
#import uni_form
#STATICFILES_DIRS = (
#    #('basic_project', os.path.join(PROJECT_ROOT, 'media')),
#    ('pinax', os.path.join(PINAX_ROOT, 'media', PINAX_THEME)),
#    os.path.join(PROJECT_ROOT, 'static'),
#    os.path.join(PINAX_ROOT, 'media', PINAX_THEME),
#    os.path.join(uni_form.__path__[0], 'media'),
#)

ADMIN_MEDIA_PREFIX = posixpath.join(STATIC_URL, 'admin/')
SECRET_KEY = 'secret-key-only-used-for-development-do-not-use-in-production'

# List of callables that know how to import templates from various sources.
if LIVE_HOST:
    TEMPLATE_LOADERS = (
        ('django.template.loaders.cached.Loader', (
            'django.template.loaders.filesystem.Loader',
            'django.template.loaders.app_directories.Loader',
        )),
    )
else:
    TEMPLATE_LOADERS = (
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    )

MIDDLEWARE_CLASSES = (
    'django.middleware.gzip.GZipMiddleware',

    'django.middleware.common.CommonMiddleware',
    'catnap.middleware.HttpExceptionMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.transaction.TransactionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    #'account.middleware.LocaleMiddleware', #Enable when we add more translations.
    #'django.middleware.doc.XViewMiddleware',
    #'pagination.middleware.PaginationMiddleware',
    #'pinax.middleware.security.HideSensistiveFieldsMiddleware',
    'catnap.middleware.HttpAcceptMiddleware',
    'catnap.middleware.HttpMethodsFallbackMiddleware',
)

if DEBUG:
    MIDDLEWARE_CLASSES += (
        #'debug_toolbar.middleware.DebugToolbarMiddleware',
        'manabi.apps.utils.middleware.JsonDebugMiddleware',
    )


ROOT_URLCONF = 'manabi.urls'

TEMPLATE_DIRS = (
    os.path.join(PROJECT_ROOT, 'templates'),
    #os.path.join(PINAX_ROOT, 'templates', PINAX_THEME),
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.request',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
    'django.contrib.messages.context_processors.messages',
    #'staticfiles.context_processors.static_url',
    #"pinax.core.context_processors.pinax_settings",
    #'pinax.apps.account.context_processors.account',
    'notification.context_processors.notification',
    'announcements.context_processors.site_wide_announcements',
    'dojango.context_processors.config',
    'manabi.context_processors.site_base_extender',
)

INSTALLED_APPS = (
    # included
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.humanize',
    'django.contrib.staticfiles',

    # external
    #'notification', # must be first
    #'emailconfirmation',
    #'mailer',
    #'announcements',
    #'pagination',
    'timezones',
    #'ajax_validation',
    #'uni_form',

    # Pinax
    #'pinax.templatetags',
    #'pinax.apps.account',
    #'pinax.apps.signup_codes',
    #'pinax.apps.analytics',

    'django_extensions',

    # Sentry
    #'raven.contrib.django',
    #'sentry',

    # Other
    #'template_repl',
    'south',
    'django_nose', # Must come after south.
    'lazysignup',
    'catnap',
    'cachecow',

    # internal (for now)
    #'profiles',
    #'about',
  
    # my own
    'manabi.apps.flashcards',
    'manabi.apps.books',
    'dojango',
    'manabi.apps.utils',
    'manabi.apps.usertagging', #fork of django-tagging, which is isolated per-user
    'manabi.apps.jdic',
    'kanjivg',
    'manabi.apps.stats',
    #TODO-OLD 'mobileaccount',
    'manabi.apps.importer',
    #TODO-OLD 'popups',
    'manabi.apps.manabi_redis',

    'gunicorn',
)


if DEBUG:
    INSTALLED_APPS += (
        #'debug_toolbar',
        #'devserver',
    )

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'
NOSE_PLUGINS = [
    'manabi.nose_plugins.SilenceSouth',
]
NOSE_ARGS = ['--logging-level=WARNING']

DEVSERVER_MODULES = (
    #'devserver.modules.sql.SQLRealTimeModule',
    'devserver.modules.sql.SQLSummaryModule',
    'devserver.modules.profile.ProfileSummaryModule',

    ## Modules not enabled by default
    ##'devserver.modules.ajax.AjaxDumpModule',
    #'devserver.modules.profile.MemoryUseModule',
    'devserver.modules.cache.CacheSummaryModule',
)
#DEVSERVER_IGNORED_PREFIXES = ['/site_media', '/uploads', '/static', '/media']
DEVSERVER_IGNORED_PREFIXES = []

#DEBUG_TOOLBAR_PANELS = (
#    'debug_toolbar.panels.version.VersionDebugPanel',
#    'debug_toolbar.panels.timer.TimerDebugPanel',
#    'debug_toolbar.panels.settings_vars.SettingsVarsDebugPanel',
#    'debug_toolbar.panels.headers.HeaderDebugPanel',
#    'debug_toolbar.panels.request_vars.RequestVarsDebugPanel',
#    'debug_toolbar.panels.template.TemplateDebugPanel',
#    'debug_toolbar.panels.sql.SQLDebugPanel',
#    'debug_toolbar.panels.signals.SignalDebugPanel',
#    #'debug_toolbar.panels.logger.LoggingPanel',
#)


if LIVE_HOST:
   CACHES = {
       'default': dict(
           #BACKEND = 'johnny.backends.memcached.PyLibMCCache',
           BACKEND='johnny.backends.memcached.MemcachedCache',
           #BACKEND='django.core.cache.backends.memcached.MemcachedCache',
           LOCATION=['127.0.0.1:11211'],
           JOHNNY_CACHE=True,
           KEY_PREFIX='dj_manabi',
           MAX_ENTRIES=5000
       ),
   }
else:
   CACHES = {
       'default': {
           'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
       }
   }

#JOHNNY_MIDDLEWARE_KEY_PREFIX='jc_manabi'

#DISABLE_QUERYSET_CACHE = not LIVE_HOST

SEND_BROKEN_LINK_EMAILS = True
IGNORABLE_404_ENDS = ('.php', '.cgi')
IGNORABLE_404_STARTS = ('/phpmyadmin/',)


ABSOLUTE_URL_OVERRIDES = {
    'auth.user': lambda o: '/profiles/profile/%s/' % o.username,
}

#MARKUP_FILTER_FALLBACK = 'none'
#MARKUP_CHOICES = (
#    ('restructuredtext', u'reStructuredText'),
#    ('textile', u'Textile'),
#    ('markdown', u'Markdown'),
#    ('creole', u'Creole'),
#)
#WIKI_MARKUP_CHOICES = MARKUP_CHOICES

#AUTH_PROFILE_MODULE = "profiles.Profile"
#NOTIFICATION_LANGUAGE_MODULE = 'account.Account'

#ACCOUNT_OPEN_SIGNUP = True
#ACCOUNT_REQUIRED_EMAIL = LIVE_HOST
ACCOUNT_EMAIL_VERIFICATION = False
#ACCOUNT_EMAIL_AUTHENTICATION = False
#ACCOUNT_UNIQUE_EMAIL = EMAIL_CONFIRMATION_UNIQUE_EMAIL = False

AUTHENTICATION_BACKENDS = [
    #'pinax.apps.account.auth_backends.AuthenticationBackend',
    #'utils.auth_backends.AuthenticationBackendWithLazySignup',
    'django.contrib.auth.backends.ModelBackend',
    'lazysignup.backends.LazySignupBackend',
]

#LAZYSIGNUP_ENABLE = True
LAZYSIGNUP_ENABLE = False

SITE_NAME = 'Manabi'

LOGIN_URL = '/account/login/'
LOGIN_REDIRECT_URLNAME = 'home'

#EMAIL_CONFIRMATION_DAYS = 7
#EMAIL_DEBUG = DEBUG
#CONTACT_EMAIL = 'support@manabi.org'
DEFAULT_FROM_EMAIL = 'Manabi <support@manabi.org>'

FIXTURE_DIRS = (
    'fixtures/',
)

#dojango
if LIVE_HOST:
    DOJANGO_DOJO_PROFILE = 'google'
    DOJANGO_DOJO_VERSION = '1.6' # was .0
else:
    DOJANGO_DOJO_PROFILE = 'local'#'google'
    DOJANGO_DOJO_VERSION = '1.6'
    DOJANGO_DOJO_SECURE_JSON = False
if LIVE_HOST:
    DOJANGO_DOJO_THEME_URL = 'http://ajax.googleapis.com/ajax/libs/dojo/1.6/dijit/themes'
    DOJANGO_DOJO_THEME = 'tundra'
    DOJANGO_BASE_MEDIA_URL = STATIC_URL
    DOJO_BASE_PATH = './'#STATIC_URL + 'js'
else:
    DOJANGO_DOJO_THEME_URL = STATIC_URL + 'css/dojo_themes'
    DOJANGO_DOJO_THEME = 'tundra'
    DOJANGO_BASE_MEDIA_URL = STATIC_URL


# JDic audio server root URL - the directory containing the mp3s.
# Must end in '/'
#TODO-OLD
JDIC_AUDIO_SERVER_URL = 'http://jdic.manabi.org/audio/'
JDIC_AUDIO_SERVER_TIMEOUT = 6 # seconds

import kanjivg
_kanjivg_static_path = os.path.join(kanjivg.__path__[0], 'static', 'kanjivg')
KANJI_SVG_XSLT_PATH = os.path.join(_kanjivg_static_path, 'svg2gfx.xslt')
KANJI_SVGS_PATH = os.path.join(_kanjivg_static_path, 'svgs')
#KANJI_SVG_XSLT_PATH = os.path.join(STATIC_ROOT, 'kanjivg', 'svg2gfx.xslt')
#KANJI_SVGS_PATH = os.path.join(STATIC_ROOT, 'kanjivg', 'svgs')


START_OF_DAY = 5 # hour of day most likely to be while the user is asleep, localized
 
MECAB_ENCODING = 'utf8'


if LIVE_HOST:
    DEFAULT_URL_PREFIX = 'http://www.manabi.org'
else:
    #DEFAULT_URL_PREFIX = 'http://192.168.2.127:8000'
    DEFAULT_URL_PREFIX = 'http://192.168.0.1:8000'


# KISSmetrics
#KISS_KEY = ''

#sudo su postgres -c psql template1

if LIVE_HOST:
    try:
        from manabi.settings_production import *
    except ImportError:
        pass
else:
    try:
        from manabi.settings_development import *
    except ImportError:
        pass

