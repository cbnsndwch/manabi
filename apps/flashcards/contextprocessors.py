
from flashcards.models import FactType, Fact, Deck, CardTemplate, \
    FieldType, FieldContent, Card, \
    GRADE_NONE, GRADE_HARD, GRADE_GOOD, GRADE_EASY, \
    SchedulingOptions

from django.template.loader import render_to_string
import datetime


def subfact_form_context(request, subfact=None, field_content_offset=0, fact_form_ordinal=1):
    '''
    `form_ordinal` is the offset to use for e.g. fact-1-id
    '''
    context = {}
    sentence_fact_type = FactType.objects.get(id=2)
    field_types = sentence_fact_type.fieldtype_set.exclude(disabled_in_form=True).order_by('ordinal')
    context.update({
        'fact_type': sentence_fact_type,
        'field_types': field_types,
    })
    if subfact:
        context.update({
            'field_content_for_field_types': dict((field_type, subfact.field_contents.get(field_type=field_type),) for field_type in field_types),
            'field_content_offset': field_content_offset,
            'fact_form_ordinal': fact_form_ordinal,
            'is_js_template': False,
            'subfact': subfact,
        })
    else:
        context.update({
            'is_js_template': True,
        })
    return {'subfact_form': context}

def card_existence_context(request):
    '''
    adds 'cards_exist', 'decks_exist' (booleans)
    '''
    decks = Deck.objects.of_user(request.user)
    cards = Card.objects.of_user(request.user, with_upstream=True)
    return {
        'decks_exist': decks.exists(),
        'cards_exist': cards.exists(),
    }

def deck_count_context(request):
    '''
    adds `deck_count`
    '''
    deck_count = Deck.objects.of_user(request.user).count()
    return {'deck_count': deck_count}


def review_start_context(request, deck=None):
    '''
    Returns a dictionary for studying either all decks, or a single deck.
    This is for the screen before actually reviewing, which shows the buttons
    to start the review.
    '''
    user = request.user

    cards = Card.objects.common_filters(user,
        with_upstream=True, deck=deck)

    due_card_count = cards.due(user).count()
    new_card_count = cards.new_count(user)

    card_count = cards.count()

    unspaced_new_card_count = cards.unspaced_new_count(user)

    context = {
        'card_count': card_count,
        'next_card_due_at': cards.next_card_due_at(),
        'due_card_count': due_card_count,
        'new_card_count': new_card_count,
        'can_learn_more': new_card_count > 0,
        'is_early_review': (
            due_card_count == 0
            and card_count
            and unspaced_new_card_count == 0),
            #and card_count != new_card_count),
        'count_of_cards_due_tomorrow': cards.count_of_cards_due_tomorrow(user),
        'unspaced_new_card_count': unspaced_new_card_count,
    }
    context['next_card_due_at_message'] = render_to_string(
            'flashcards/_next_card_due_at.txt', context).strip()


    #'new_cards_left_for_today': new_cards_left_for_today,

    return context









#def study_options_context(request, deck_id=None):
#    '''
#    Returns a dictionary for studying either all decks, or a single deck.

#    DEPRECATED
#    '''
#    context = {}

#    deck = Deck.objects.get(id=deck_id) if deck_id else None

#    deck_count = Deck.objects.of_user(request.user).count()

#    next_card_due_at = Card.objects.next_card_due_at(request.user, deck=deck)
#    if next_card_due_at:
#        time_until_next_card_due = next_card_due_at - datetime.datetime.utcnow()
#        context.update({
#            'next_card_due_at': next_card_due_at,
#            'time_until_next_card_due': time_until_next_card_due,
#            'minutes_until_next_card_due': time_until_next_card_due.days * 24 + time_until_next_card_due.seconds / 60,
#            'hours_until_next_card_due': time_until_next_card_due.days * 24 + time_until_next_card_due.seconds / (60 * 60),
#        })

#    # New card count for today.
#    # estimate adjusted count of new cards that can be reviewed now, after spacing, by just counting the unique facts
#    daily_new_card_limit = NEW_CARDS_PER_DAY
#    if deck or deck_count:
#        due_card_count = Card.objects.due_cards(request.user, deck=deck).count()
#        new_card_count = Card.objects.new_cards(request.user, deck=deck).count()
#        new_reviews_today = request.user.reviewstatistics.get_new_reviews_today()
#        if daily_new_card_limit:
#            spaced_new_card_count = Card.objects.next_cards_count(request.user, deck=deck, new_cards_only=True)
#            if spaced_new_card_count:
#                new_cards_left_for_today = daily_new_card_limit - new_reviews_today
#                if new_cards_left_for_today < 0:
#                    new_cards_left_for_today = 0
#                new_cards_left_for_today = min(new_cards_left_for_today, spaced_new_card_count)
#            else:
#                new_cards_left_for_today = 0
#            #context['can_learn_more'] = new_cards_left_for_today > 0
#        else:
#            new_cards_left_for_today = None
#        context['can_learn_more'] = new_card_count > 0

#        context.update({
#                'is_early_review': due_card_count == 0 and new_cards_left_for_today == 0,

#                'card_count': Card.objects.of_user(request.user).count(),
#                'due_card_count': due_card_count,
#                'new_card_count': new_card_count,
#                #'spaced_new_card_count': spaced_new_card_count,

#                'count_of_cards_due_tomorrow': Card.objects.count_of_cards_due_tomorrow(request.user, deck=deck),

#                'new_cards_left_for_today': new_cards_left_for_today,
#        })

#    # is this (not) a request for a specific deck?
#    if not deck_id:
#        context.update({
#                'deck_count': deck_count,
#        })

#    return context



