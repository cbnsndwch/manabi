#from flashcards.views.api import rest_facts
from django.dispatch import receiver
from flashcards.signals import fact_grid_updated
from cachecow.cache import invalidate_namespace


@receiver(fact_grid_updated, dispatch_uid='nuke_fact_grid_namespace')
def nuke_fact_grid_namespace(sender, decks=[], **kwargs):
    for deck in decks:
        invalidate_namespace(fact_grid_namespace(deck=deck.pk))
 

def fact_grid_namespace(deck=None, *args, **kwargs):
    '''
    This namespace is keyed on the deck PK.
    '''
    print 'fact_grid_namespace'
    return ['fact_grid', deck]

###############################################################################

#@receiver(post_save, sender=FieldContent, dispatch_uid='human_readable_field_ps')
#def nuke_human_readable_field(sender, instance, created, **kwargs):
    
