#from flashcards.views.api import rest_facts
from django.dispatch import receiver
from flashcards.signals import fact_grid_updated
from cachecow.cache import invalidate_namespace


@receiver(fact_grid_updated, dispatch_uid='nuke_fact_grid_namespace')
def nuke_fact_grid_namespace(sender, decks=[], **kwargs):
    for deck in decks:
        invalidate_namespace(fact_grid_namespace(deck=deck.id))
 

def fact_grid_namespace(deck=None, *args, **kwargs):
    '''
    This namespace is keyed on the deck ID.
    '''
    print 'fact_grid_namespace'
    return ['fact_grid', deck]


