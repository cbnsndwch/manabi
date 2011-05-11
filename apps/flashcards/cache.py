from cachecow.cache import invalidate_namespace
from django.db.models.signals import (post_save, m2m_changed, post_delete,
                                      pre_delete,)
from django.dispatch import receiver
from flashcards.signals import (fact_grid_updated,
                                card_reviewed, card_active_field_changed,)
from models.fields import FieldContent
from flashcards.models import Card


@receiver(fact_grid_updated, dispatch_uid='nuke_fact_grid_namespace')
def nuke_fact_grid_namespace(sender, decks=[], **kwargs):
    for deck in decks:
        invalidate_namespace(fact_grid_namespace(deck=deck.pk))
 

def fact_grid_namespace(deck=None, *args, **kwargs):
    '''
    This namespace is keyed on the deck PK.
    '''
    return ['fact_grid', deck]


###############################################################################

@receiver(post_save, sender=FieldContent, dispatch_uid='human_readable_field_ps')
def nuke_human_readable_field(sender, instance, created, **kwargs):
    instance.human_readable_content.delete_cache(instance)


###############################################################################
# Per-deck, review-related stat caches

def deck_review_stats_namespace(deck, *args, **kwargs):
    '''
    Namespace keyed on the deck PK.
    
    Invalidated by things like a card being reviewed, or a card being deleted.
    New cards do not affect this namespace, since most stats are unrelated to
    the number of new cards. For the stats which are related to that, use 
    a different caching strategy than what this namespace provides.
    '''
    return ['deck_review_stats', deck.pk]

@receiver(card_reviewed, dispatch_uid='deck_review_stats_cr')
@receiver(card_active_field_changed, dispatch_uid='deck_review_stats_cafc')
@receiver(pre_delete, sender=Card, dispatch_uid='deck_review_stats_cpd')
def nuke_deck_review_stats_namespace(sender, instance, **kwargs):
    invalidate_namespace(deck_review_stats_namespace(instance.deck))




