from manabi.apps.flashcards.models import (FactType, Fact, Deck, CardTemplate,
    FieldType, FieldContent, Card,
    GRADE_NONE, GRADE_HARD, GRADE_GOOD, GRADE_EASY)
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import resolve
from django.db.models import F
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from manabi.apps.flashcards.contextprocessors import subfact_form_context
from manabi.apps.flashcards.contextprocessors import deck_count_context, card_existence_context
from django.views.decorators.cache import cache_page


def index(request):
    '''Entry point to the site.'''
    context = {
        #'extended_template_name': ('ajax_site_base.html' if request.user.is_authenticated() else 'site_base.html'),
        'extended_template_name': 'ajax_site_base.html',
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


def home(request):
    '''The homepage that gets loaded via ajax.'''
    context = {}
    return render_to_response('home.html', context,
        context_instance=RequestContext(request, processors=[card_existence_context]))

