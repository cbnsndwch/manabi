def with_siblings_buried(cards, order_by=None):
    '''
    Removes siblings from a queryset.
    '''
    from manabi.apps.flashcards.models import Card

    if order_by is None:
        ordered_cards = cards.order_by('fact_id')
    else:
        ordered_cards = cards.order_by('fact_id', order_by)

    cards_with_burying_applied = ordered_cards.distinct('fact_id')

    if order_by is None:
        return cards_with_burying_applied
    else:
        return Card.objects.filter(
            pk__in=cards_with_burying_applied,
        ).order_by(order_by)
