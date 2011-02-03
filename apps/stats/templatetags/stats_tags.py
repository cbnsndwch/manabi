from django import template
from flashcards.models import CardHistory, Deck
from copy import copy

register = template.Library()


def _usage_history(deck=None):
    s = '''<div dojoType="stats.UsageSparkline"{0}></div>'''

    if deck:
        return s.format(' deckId="{0}"'.format(deck.id))
    else:
        return s.format('')


@register.simple_tag
def usage_history():
    return _usage_history()
    
    
@register.simple_tag
def deck_usage_history(deck):
    return _usage_history(deck=deck)



def _overview_stat_counts(deck=None):
    context = {
        #'':
    }

@register.inclusion_tag('stats/_overview_stat_counts.html')
def overview_stat_counts():
    return _overview_stat_counts()

@register.inclusion_tag('stats/_overview_stat_counts.html')
def deck_overview_stat_counts(deck):
    return _overview_stat_counts(deck=deck)
