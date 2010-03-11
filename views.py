
from flashcards.models import FactType, Fact, Deck, CardTemplate, FieldType, FieldContent, Card, SharedDeck, GRADE_NONE, GRADE_HARD, GRADE_GOOD, GRADE_EASY, SchedulingOptions, NEW_CARDS_PER_DAY
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.db.models import F

from django.contrib.auth.decorators import login_required
import datetime

@login_required
def home(request):
    deck_count = Deck.objects.of_user(request.user).count()
    context = {
            'shared_deck_list': Deck.objects.shared_decks(),
            'deck_count': deck_count,
    }

    next_card_due_at = Card.objects.next_card_due_at(request.user)
    if next_card_due_at:
        time_until_next_card_due = next_card_due_at - datetime.datetime.utcnow()
        context.update({
            'next_card_due_at': next_card_due_at,
            'time_until_next_card_due': time_until_next_card_due,
            'minutes_until_next_card_due': time_until_next_card_due.days * 24 + time_until_next_card_due.seconds / 60,
            'hours_until_next_card_due': time_until_next_card_due.days * 24 + time_until_next_card_due.seconds / (60 * 60),
        })


    # New card count for today.
    # estimate adjusted count of new cards that can be reviewed now, after spacing, by just counting the unique facts
    spaced_new_card_count = Card.objects.next_cards_count(request.user) #Fact.objects.filter(id__in=Card.objects.new_cards(request.user).values_list('fact', flat=True)).distinct()
    daily_new_card_limit = NEW_CARDS_PER_DAY
    if deck_count:
        new_reviews_today = request.user.reviewstatistics.get_new_reviews_today()
        if daily_new_card_limit:
            if spaced_new_card_count:
                new_cards_left_for_today = daily_new_card_limit - new_reviews_today
                if new_cards_left_for_today < 0:
                    new_cards_left_for_today = 0
                new_cards_left_for_today = min(new_cards_left_for_today, spaced_new_card_count)
            else:
                new_cards_left_for_today = 0
        else:
            new_cards_left_for_today = None

        context.update({
                'card_count': Card.objects.of_user(request.user).count(),
                'due_card_count': Card.objects.due_cards(request.user).count(),
                'new_card_count': Card.objects.new_cards(request.user).count(),
                'spaced_new_card_count': spaced_new_card_count,


                'count_of_cards_due_tomorrow': Card.objects.count_of_cards_due_tomorrow(request.user),

                'new_cards_left_for_today': new_cards_left_for_today,
        })

    return render_to_response('home.html', context, context_instance=RequestContext(request))



def index(request):
    context = {}
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

    return render_to_response('homepage.html', 
                              context, 
                              context_instance=RequestContext(request))
