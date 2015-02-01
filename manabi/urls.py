from lazysignup.decorators import allow_lazy_user
from django.conf.urls import *
from django.conf import settings
from django.contrib import admin

#TODO-OLD from forms import SignupForm
from manabi.apps.utils.views import direct_to_template
from manabi.apps.utils.urldecorators import decorated_patterns
#from manabi.apps.flashcards.urls import rest_api_urlpatterns

admin.autodiscover()



urlpatterns = patterns(
    '',
    # Use our customized form
    #TODO-OLD url(r'^account/signup/$', 'account.views.signup',
    #    name="acct_signup", kwargs={'form_class': SignupForm}),

    url(r'convert/', include('lazysignup.urls')),

    #TODO-OLD (r'^account/', include('account.urls')),
    (r'^admin/', include(admin.site.urls)),
    #(r'^sentry/', include('sentry.web.urls')),

    #TODO-OLD (r'^mobile-account/', include('mobileaccount.urls')),

    #TODO-OLD url(r'^popups/login/$', 'account.views.login', name='popup_acct_login', kwargs={
        #'template_name': 'popups/login.html',}),

    #(r'^popups/', include('manabi.apps.popups.urls')),

    url(r'^terms-of-service/$', direct_to_template,
        {'template': 'tos.html'}, name='terms_of_service'),
    url(r'^privacy-policy/$', direct_to_template,
        {'template': 'privacy.html'}, name='privacy_policy'),
    url(r'^credits/$', direct_to_template,
        {'template': 'credits.html'}, name='credits'),

    url(r'^api/auth/', include('manabi.apps.manabi_auth.api_urls')),
    url(r'^api/flashcards/', include('manabi.apps.flashcards.api_urls')),

    #url(r'^flashcards/api/', include(rest_api_urlpatterns)),

) + decorated_patterns('', allow_lazy_user,
    #url(r'^$', direct_to_template, {
    #    "template": "homepage.html",
    #}, name="home"),
    url(r'^$', 'views.index', name='home'),

    url(r'^home/$', 'views.home', name='home_inline'),

    #(r'^dojango/', include('dojango.urls')),

    #url(r'^admin/invite_user/$', 'signup_codes.views.admin_invite_user',
        #name="admin_invite_user"),

    #(r'^profiles/', include('basic_profiles.urls')),
    #url(r'^profiles/', include('idios.urls')),

    (r'^about/', include('manabi.apps.about.urls')),

    # my own
    #(r'^reports/', include('reports.urls')),

    (r'^flashcards/', include('manabi.apps.flashcards.urls')),
    #(r'^textbooks/', include('manabi.apps.books.urls')),
    (r'^importer/', include('manabi.apps.importer.urls')),
    #(r'^jdic/', include('manabi.apps.jdic.urls')),
    (r'^kanjivg/', include('kanjivg.urls')),
    #(r'^stats/', include('manabi.apps.stats.urls')),
)

#if settings.SERVE_MEDIA:
#    urlpatterns += patterns('',
#TODO-OLD        (r'^favicon\.ico$', 'manabi.apps.utils.views.redirect_to', {'url': '/site_media/static/favicon.ico'}),
#    )

#    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
#    urlpatterns += staticfiles_urlpatterns()

#    #urlpatterns += patterns('',
#    #    #(r'^site_media/', include('staticfiles.urls')),
#    #    url(r'', include('staticfiles.urls')),
#    #)

