from flashcards.models import FactType, Fact, Deck, CardTemplate, \
    FieldType, FieldContent, Card, \
    GRADE_NONE, GRADE_HARD, GRADE_GOOD, GRADE_EASY, \
    SchedulingOptions
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import resolve
from django.db.models import F
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from flashcards.contextprocessors import subfact_form_context
from flashcards.contextprocessors import deck_count_context, card_existence_context
from django.views.decorators.cache import cache_page



def index(request):
    '''Entry point to the site.'''
    context = {
        'extended_template_name': ('ajax_site_base.html' if request.user.is_authenticated() else 'site_base.html'),
    }
    if request.user.is_authenticated():
        #build the context object
        #get flashcard context, for fact add form
        #assume Japanese fact type
        fact_type = FactType.objects.get(id=1)
        card_templates = fact_type.cardtemplate_set.all()
        field_types = fact_type.fieldtype_set.exclude(disabled_in_form=True).order_by('ordinal')
        context['fact_add_form'] = {
            'card_templates': card_templates,
            'field_types': field_types,
        }

        context.update(subfact_form_context(request))
        

    return render_to_response('homepage.html', 
                              context, 
                              context_instance=RequestContext(request))


@login_required
def home(request):
    '''The homepage that gets loaded via ajax.'''
    context = {}
    return render_to_response('home.html', context,
        context_instance=RequestContext(request, processors=[card_existence_context]))







#########################################################################
# Copied from django-lazysignup
# We have to override the `convert` view to support our AJAX navigation
# I really don't want to have to fork their project, so I'll just
# violate a little DRY here...

import settings
from django.shortcuts import redirect
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.http import HttpResponseBadRequest
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _
from django.views.generic.simple import direct_to_template

from django.contrib.auth import authenticate
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

from lazysignup.decorators import allow_lazy_user
from lazysignup.exceptions import NotLazyError
from lazysignup.forms import UserCreationForm
from lazysignup.models import LazyUser

@allow_lazy_user
def convert(request,
    form_class=UserCreationForm,
    redirect_field_name='redirect_to',
    default_redirect_to='lazysignup_convert_done',
    anonymous_redirect=settings.LOGIN_URL):
    """ Convert a temporary user to a real one. Reject users who don't
    appear to be temporary users (ie. they have a usable password)
    """
    redirect_to = default_redirect_to

    # If we've got an anonymous user, redirect to login
    if request.user.is_anonymous():
        return HttpResponseRedirect(anonymous_redirect)

    if request.method == 'POST':
        redirect_to = request.POST.get(redirect_field_name) or redirect_to
        form = form_class(request.POST, instance=request.user)
        if form.is_valid():
            try:
                user = LazyUser.objects.convert(form)
            except NotLazyError:
                # If the user already has a usable password, return a Bad Request to
                # an Ajax client, or just redirect back for a regular client.
                if request.is_ajax():
                    return HttpResponseBadRequest(content=_(u"Already converted."))
                else:
                    return redirect(redirect_to)

            # Re-log the user in, as they'll now not be authenticatable with the Lazy
            # backend
            login(request, authenticate(**form.get_credentials()))

            # If we're being called via AJAX, then we just return a 200 directly
            # to the client. If not, then we redirect to a confirmation page or
            # to redirect_to, if it's set.
            if request.is_ajax():
                return HttpResponse()
            else:
                return redirect(redirect_to)
    else:
        form = form_class()

    return direct_to_template(
        request,
        'lazysignup/convert.html',
        { 'form': form,
            'redirect_to': redirect_to
        },
        )


