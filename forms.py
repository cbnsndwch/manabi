from account.forms import SignupForm as PinaxSignupForm, OpenIDSignupForm as PinaxOpenIDSignupForm
from timezones.forms import TimeZoneField
from django.utils.translation import ugettext_lazy as _, ugettext

class SignupForm(PinaxSignupForm):
    timezone = TimeZoneField(label=_("Timezone"), required=True, initial='America/New_York')

class OpenIDSignupForm(PinaxOpenIDSignupForm):
    timezone = TimeZoneField(label=_("Timezone"), required=True, initial='America/New_York')
