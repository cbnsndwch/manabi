from django import template
from flashcards.models import CardHistory, Deck
from copy import copy

register = template.Library()


def _usage_history(deck=None):
    s = '''<div dojoType="stats.UsageSparkline"{0}></div>'''

    if deck:
        return s.format('')
    else:
        return s.format(' deckId="{}"'.format(deck.id))


@register.simple_tag
def usage_history(user):
    return _usage_history()
    
    
@register.simple_tag
def deck_usage_history(deck):
    return _usage_history(deck=deck)

