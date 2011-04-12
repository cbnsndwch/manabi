from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.translation import ugettext, ugettext_lazy as _

from django.contrib import messages
from django.contrib.auth.models import User

from pinax.apps.account.utils import get_default_redirect, user_display
from pinax.apps.account.forms import SignupForm
from pinax.apps.account.views import group_and_bridge, group_context

from django.db import models
from models import MobileSignupRecord
from emailconfirmation.models import EmailConfirmation
from emailconfirmation.views import confirm_email
from django.shortcuts import redirect
from django.core.exceptions import ObjectDoesNotExist


def confirm_email_proxy(request, confirmation_key):
    # See if the user signed up via the mobile interface.
    try:
        confirmation_key = confirmation_key.lower()
        user = EmailConfirmation.objects.get(
                confirmation_key=confirmation_key).email_address.user
        signup_record = MobileSignupRecord.objects.get(user=user)
        email_address = EmailConfirmation.objects.confirm_email(
                confirmation_key)
        return render_to_response('mobileaccount/confirm_email.html', {
            'email_address': email_address,
        }, context_instance=RequestContext(request))

    except ObjectDoesNotExist:
        return confirm_email(request, confirmation_key)


def signup(request, **kwargs):
    
    form_class = kwargs.pop("form_class", SignupForm)
    template_name = kwargs.pop("template_name", "account/signup.html")
    redirect_field_name = kwargs.pop("redirect_field_name", "next")
    success_url = kwargs.pop("success_url", None)
    verification_sent_template_name = kwargs.pop(
            "verification_sent_template_name",
            "account/verification_sent.html")
    
    group, bridge = group_and_bridge(kwargs)
    ctx = group_context(group, bridge)
    
    if success_url is None:
        if hasattr(settings, "SIGNUP_REDIRECT_URLNAME"):
            fallback_url = reverse(settings.SIGNUP_REDIRECT_URLNAME)
        else:
            if hasattr(settings, "LOGIN_REDIRECT_URLNAME"):
                fallback_url = reverse(settings.LOGIN_REDIRECT_URLNAME)
            else:
                fallback_url = settings.LOGIN_REDIRECT_URL
        success_url = get_default_redirect(request, fallback_url, redirect_field_name)
    
    if request.method == "POST":
        form = form_class(request.POST, group=group)
        if form.is_valid():
            user = form.save(request=request)
            signup_record = MobileSignupRecord(user=user)
            signup_record.save()
            if settings.ACCOUNT_EMAIL_VERIFICATION:
                ctx.update({
                    "email": form.cleaned_data["email"],
                    "success_url": success_url,
                })
                ctx = RequestContext(request, ctx)
                return render_to_response(verification_sent_template_name, ctx)
            else:
                form.login(request, user)
                messages.add_message(request, messages.SUCCESS,
                    ugettext("Successfully logged in as %(user)s.") % {
                        "user": user_display(user)
                    }
                )
                return HttpResponseRedirect(success_url)
    else:
        form = form_class(group=group)
    
    ctx.update({
        "form": form,
        "redirect_field_name": redirect_field_name,
        "redirect_field_value": request.REQUEST.get(redirect_field_name),
    })
    
    return render_to_response(template_name, RequestContext(request, ctx))
