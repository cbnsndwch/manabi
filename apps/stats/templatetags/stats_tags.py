from copy import copy
from datetime import datetime, timedelta
from django import template
from flashcards.models import CardHistory, Deck, Card

register = template.Library()

SPARKLINE_DAYS = 60


def _usage_history_sparkline(user, deck=None):
    # First make sure that any of these cards have actually 
    # been reviewed yet, within the given timespan.
    from_ = datetime.utcnow() - timedelta(days=SPARKLINE_DAYS)

    user_items = CardHistory.objects.of_user(user).filter(
        reviewed_at__gte=from_)
    if deck:
        user_items = user_items.of_deck(deck)
    if user_items.exists():
        s = u'''<div dojoType="stats.UsageSparkline"{0}></div>'''

        if deck:
            return s.format(' deckId="{0}"'.format(deck.id))
        else:
            return s.format('')
    else:
        return u''



@register.inclusion_tag('stats/_usage_history.html')
def usage_history(user):
    return {'sparkline': _usage_history_sparkline(user)}

    
@register.inclusion_tag('stats/_usage_history.html')
def deck_usage_history(deck):
    return {'sparkline': _usage_history_sparkline(deck.owner, deck=deck)}



def _overview_stat_counts(user, deck=None):
    cards = Card.objects.common_filters(user,
            deck=deck, with_upstream=True)
    
    context = {
        'total': cards.count(),
        'young': cards.young(user).count(),
        'mature': cards.mature(user).count(),
        'new': cards.new_count(user),
    }
    return context

@register.inclusion_tag('stats/_overview_stat_counts.html')
def overview_stat_counts(user):
    return _overview_stat_counts(user)

@register.inclusion_tag('stats/_overview_stat_counts.html')
def deck_overview_stat_counts(deck):
    return _overview_stat_counts(deck.owner, deck=deck)


