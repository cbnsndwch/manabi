from django.conf.urls.defaults import *
from django.conf import settings

from django.views.generic.simple import direct_to_template

from django.contrib import admin
admin.autodiscover()

from account.openid_consumer import PinaxConsumer

from forms import SignupForm, OpenIDSignupForm


if settings.ACCOUNT_OPEN_SIGNUP:
    signup_view = "account.views.signup"
else:
    signup_view = "signup_codes.views.signup"

class ManabiConsumer(PinaxConsumer):
    def get_registration_form_class(self, request):
        return OpenIDSignupForm

urlpatterns = patterns('',
    #url(r'^$', direct_to_template, {
    #    "template": "homepage.html",
    #}, name="home"),
    url(r'^$', 'views.index', name='home'),

    url(r'^home$', 'views.home', name='home_inline'), #direct_to_template, {'template': 'home.html',}, name='home_inline'),
    
    url(r'^admin/invite_user/$', 'signup_codes.views.admin_invite_user', name="admin_invite_user"),
    url(r'^account/signup/$', signup_view, name="acct_signup", kwargs={'form_class': SignupForm}), # Use our customized form
    
    (r'^about/', include('about.urls')),
    (r'^account/', include('account.urls')),
    (r'^openid/(.*)', ManabiConsumer()),
    (r'^profiles/', include('basic_profiles.urls')),
    (r'^notices/', include('notification.urls')),
    (r'^announcements/', include('announcements.urls')),
    
    (r'^admin/(.*)', admin.site.root),
    
    # my own
    (r'^dojango/', include('dojango.urls')),
    (r'^flashcards/', include('flashcards.urls')),
)

if settings.SERVE_MEDIA:
    urlpatterns += patterns('', 
        (r'^site_media/', include('staticfiles.urls')),
    )
