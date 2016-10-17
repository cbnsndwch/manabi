def with_siblings_buried(cards, order_by):
    '''
    Removes siblings from a queryset.
    '''
    from manabi.apps.flashcards.models import Card

    cards_with_burying_applied = (
        cards.order_by('fact_id', order_by).distinct('fact_id'))
    return Card.objects.filter(
        pk__in=cards_with_burying_applied,
    ).order_by(order_by)
