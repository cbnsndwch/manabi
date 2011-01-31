from django.conf.urls.defaults import *
from django.conf import settings

from django.views.generic.simple import direct_to_template

from django.contrib import admin
admin.autodiscover()

from forms import SignupForm


if settings.ACCOUNT_OPEN_SIGNUP:
    signup_view = "account.views.signup"
else:
    signup_view = "signup_codes.views.signup"

#class ManabiConsumer(PinaxConsumer):
#    def get_registration_form_class(self, request):
#        return OpenIDSignupForm

urlpatterns = patterns('',
    #url(r'^$', direct_to_template, {
    #    "template": "homepage.html",
    #}, name="home"),
    url(r'^$', 'views.index', name='home'),

    url(r'^home$', 'views.home', name='home_inline'),
    
    url(r'^admin/invite_user/$', 'signup_codes.views.admin_invite_user',
        name="admin_invite_user"),

    # Use our customized form
    url(r'^account/signup/$', signup_view,
        name="acct_signup", kwargs={'form_class': SignupForm}), 
    
    (r'^about/', include('about.urls')),
    (r'^account/', include('account.urls')),
    #(r'^profiles/', include('basic_profiles.urls')),
    #url(r'^profiles/', include('idios.urls')),
    (r'^notices/', include('notification.urls')),
    (r'^announcements/', include('announcements.urls')),
    
    (r'^admin/', include(admin.site.urls)),
    
    # my own
    (r'^reports/', include('reports.urls')),
    (r'^dojango/', include('dojango.urls')),
    (r'^flashcards/', include('flashcards.urls')),
    (r'^jdic/', include('jdic.urls')),
    (r'^kanjivg/', include('kanjivg.urls')),
    (r'^stats/', include('stats.urls')),
)

if settings.SERVE_MEDIA:
    urlpatterns += patterns('',
        (r'^favicon\.ico$', 'django.views.generic.simple.redirect_to', {'url': '/site_media/static/icons/favicon.ico'}),
    )

    urlpatterns += patterns('', 
        #(r'^site_media/', include('staticfiles.urls')),
        url(r'', include('staticfiles.urls')),
    )
