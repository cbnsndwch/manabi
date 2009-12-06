
from flashcards.models import FactType, Fact, Deck, CardTemplate, FieldType, FieldContent, Card, SharedDeck, GRADE_NONE, GRADE_HARD, GRADE_GOOD, GRADE_EASY, SchedulingOptions
from django.shortcuts import render_to_response
from django.template import RequestContext

def index(request):
    context = {}
    if request.user.is_authenticated():
        #build the context object
        #get flashcard context, for fact add form
        #assume Japanese fact type
        fact_type = FactType.objects.get(id=1)
        card_templates = fact_type.cardtemplate_set.all()
        field_types = fact_type.fieldtype_set.all()
        context['fact_add_form'] = {
            'card_templates': card_templates,
            'field_types': field_types,
        }

    return render_to_response('homepage.html', 
                              context, 
                              context_instance=RequestContext(request))
