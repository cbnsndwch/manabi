from django.conf import settings
from django.conf.urls import *
from django.contrib import admin
from lazysignup.decorators import allow_lazy_user

from manabi.apps.utils.urldecorators import decorated_patterns
from manabi.apps.utils.views import direct_to_template

# TODO admin.autodiscover()


urlpatterns = patterns(
    '',
    (r'^admin/', include(admin.site.urls)),

    url(r'^terms-of-service/$', direct_to_template,
        {'template': 'tos.html'}, name='terms_of_service'),
    url(r'^privacy-policy/$', direct_to_template,
        {'template': 'privacy.html'}, name='privacy_policy'),
    url(r'^credits/$', direct_to_template,
        {'template': 'credits.html'}, name='credits'),

    # API URLs.
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^api/auth/', include('manabi.apps.manabi_auth.api_urls')),
    url(r'^api/flashcards/', include('manabi.apps.flashcards.api_urls')),
    url(r'^api/twitter_usages/', include('manabi.apps.twitter_usages.api_urls')),

    #url(r'^flashcards/api/', include(rest_api_urlpatterns)),

) + decorated_patterns('', allow_lazy_user,
    url(r'^$', 'views.index', name='home'),

    (r'^flashcards/', include('manabi.apps.flashcards.urls')),
    (r'^importer/', include('manabi.apps.importer.urls')),
    (r'^kanjivg/', include('kanjivg.urls')),
)

