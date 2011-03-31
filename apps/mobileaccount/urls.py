from django.conf import settings
from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template
from forms import SignupForm


urlpatterns = patterns('mobileaccount.views',
    url(r'^signup/$', 'signup', name='mobile_acct_signup', kwargs={
        'template_name': 'mobileaccount/signup.html',
        #'success_url': 'mobile_account/signup_success.html',
        'verification_sent_template_name':
            'mobileaccount/verification_sent.html',
        'form_class': SignupForm}),
)

