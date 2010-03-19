
from flashcards.models import FactType, Fact, Deck, CardTemplate, FieldType, FieldContent, Card, SharedDeck, GRADE_NONE, GRADE_HARD, GRADE_GOOD, GRADE_EASY, SchedulingOptions, NEW_CARDS_PER_DAY

import datetime


def subfact_form_context(request, fact=None):
    context = {}
    sentence_fact_type = FactType.objects.get(id=2)
    field_types = sentence_fact_type.fieldtype_set.exclude(disabled_in_form=True).order_by('ordinal')
    if fact:
        pass
    else:
        context.update({
            'fact_type': sentence_fact_type,
            'field_types': field_types,
            'is_js_template': True,
        })
    return {'subfact_form': context}



def study_options_context(request, deck_id=None):
    '''Returns a dictionary for studying either all decks, or a single deck.
    '''
    context = {}

    deck = Deck.objects.get(id=deck_id) if deck_id else None

    deck_count = Deck.objects.of_user(request.user).count()

    next_card_due_at = Card.objects.next_card_due_at(request.user, deck=deck)
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
    daily_new_card_limit = NEW_CARDS_PER_DAY
    if deck or deck_count:
        due_card_count = Card.objects.due_cards(request.user, deck=deck).count()
        new_card_count = Card.objects.new_cards(request.user, deck=deck).count()
        spaced_new_card_count = Card.objects.next_cards_count(request.user, deck=deck)
        new_reviews_today = request.user.reviewstatistics.get_new_reviews_today()
        if daily_new_card_limit:
            if spaced_new_card_count:
                new_cards_left_for_today = daily_new_card_limit - new_reviews_today
                if new_cards_left_for_today < 0:
                    new_cards_left_for_today = 0
                new_cards_left_for_today = min(new_cards_left_for_today, spaced_new_card_count)
            else:
                new_cards_left_for_today = 0
            #context['can_learn_more'] = new_cards_left_for_today > 0
        else:
            new_cards_left_for_today = None
        context['can_learn_more'] = new_card_count > 0

        context.update({
                'is_early_review': due_card_count == 0 and new_cards_left_for_today == 0,

                'card_count': Card.objects.of_user(request.user).count(),
                'due_card_count': due_card_count,
                'new_card_count': new_card_count,
                'spaced_new_card_count': spaced_new_card_count,

                'count_of_cards_due_tomorrow': Card.objects.count_of_cards_due_tomorrow(request.user, deck=deck),

                'new_cards_left_for_today': new_cards_left_for_today,
        })

    # is this (not) a request for a specific deck?
    if not deck_id:
        context.update({
                'deck_count': deck_count,
        })

    return context



