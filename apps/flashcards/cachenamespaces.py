
def fact_grid_namespace(deck=None, *args, **kwargs):
    '''
    This namespace is keyed on the deck PK. Used for the fact grid.
    '''
    return ['fact_grid', deck]




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



