from django import template
from flashcards.models import CardHistory, Deck, Card
from copy import copy

register = template.Library()


def _usage_history_sparkline(deck=None):
    s = '''<div dojoType="stats.UsageSparkline"{0}></div>'''

    if deck:
        return s.format(' deckId="{0}"'.format(deck.id))
    else:
        return s.format('')


@register.simple_tag
def usage_history_sparkline():
    return _usage_history()
    
    
@register.simple_tag
def deck_usage_history_sparkline(deck):
    return _usage_history(deck=deck)


@register.inclusion_tag('stats/_usage_history.html')
def usage_history():
    return {'sparkline': _usage_history_sparkline()}

    
@register.inclusion_tag('stats/_usage_history.html')
def deck_usage_history(deck):
    return {'sparkline': _usage_history_sparkline(deck=deck)}



def _overview_stat_counts(user, deck=None):
    cards = Card.objects.of_user(user)

    if deck:
        cards = cards.of_deck(deck)
    
    context = {
        'total': cards.count(),
        'young': cards.young().count(),
        'mature': cards.mature().count(),
        'new': cards.new().count(),
    }
    return context

@register.inclusion_tag('stats/_overview_stat_counts.html')
def overview_stat_counts(user):
    return _overview_stat_counts(user)

@register.inclusion_tag('stats/_overview_stat_counts.html')
def deck_overview_stat_counts(deck):
    return _overview_stat_counts(deck.owner, deck=deck)
