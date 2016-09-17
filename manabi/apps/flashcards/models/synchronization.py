import itertools

from django.contrib.auth import get_user_model


def _copy_facts_to_subscribers(facts, subscribers):
    '''
    The meat-and-potatoes of the copy operation.
    '''
    from manabi.apps.flashcards.models import Card, Fact

    deck = facts[0].deck

    try:
        facts = facts.filter(active=True).iterator()
    except AttributeError:
        facts = [fact for fact in facts if fact.active]

    copied_facts = []
    copied_cards = []
    for shared_fact in facts:
        copy_attrs = [
            'active', 'suspended', 'new_fact_ordinal',
            'expression', 'reading', 'meaning',
        ]
        fact_kwargs = {attr: getattr(shared_fact, attr) for attr in copy_attrs}
        fact = Fact(
            deck=deck,
            synchronized_with=shared_fact,
            **fact_kwargs
        )
        copied_facts.append(fact)

        # Copy the cards.
        copied_cards_for_fact = []
        for shared_card in (
            shared_fact.card_set.filter(active=True, suspended=False)
            .iterator()
        ):
            card = shared_card.copy(fact)
            copied_cards_for_fact.append(card)
        copied_cards.append(copied_cards_for_fact)

    # Persist everything.
    created_facts = Fact.objects.bulk_create(copied_facts)
    for fact, fact_cards in zip(created_facts, copied_cards):
        for fact_card in fact_cards:
            fact_card.fact_id = fact.id
    Card.objects.bulk_create(itertools.chain.from_iterable(copied_cards))


def copy_facts_to_subscribers(facts, subscribers=None):
    '''
    Only call this with facts of the same deck.

    If `subscribers` is `None`, it will copy to all subscribers of the facts'
    decks.
    '''
    if not facts:
        return

    if not all(fact.deck_id is not None for fact in facts):
        raise ValueError("Facts must be saved first to copy them.")
    if len({fact.deck_id for fact in facts}) != 1:
        raise ValueError("Can only copy facts from the same deck.")

    deck = facts[0].deck

    if not deck.shared:
        raise TypeError("Facts cannot be copied from an unshared deck.")

    if subscribers is None:
        subscribers = get_user_model().filter(
            pk__in=deck.subscriber_decks.values_list('owner'))

    _copy_facts_to_subscribers(facts, subscribers=subscribers)
