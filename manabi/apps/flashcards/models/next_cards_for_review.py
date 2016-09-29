from manabi.apps.flashcards.models import (
    Card,
)


class ReviewInterstitial(object):
    def __init__(
        self,
        user,
        deck=None,
        excluded_card_ids=set(),
        time_zone=None,
    ):
        from manabi.apps.flashcards.models.review_availabilities import (
            ReviewAvailabilities,
        )

        self.review_availabilities = ReviewAvailabilities(
            user,
            deck=deck,
            excluded_card_ids=excluded_card_ids,
            time_zone=time_zone,
        )


class NextCardsForReview(object):
    def __init__(
        self,
        user,
        count,
        deck=None,
        early_review=False,
        excluded_card_ids=set(),
        time_zone=None,
    ):
        next_cards = Card.objects.next_cards(
            user,
            count,
            excluded_ids=excluded_card_ids,
            deck=deck,
            early_review=early_review,
        )

        card_ids = [card.id for card in next_cards]

        # FIXME don't need 2 queries here...
        self.cards = Card.objects.filter(pk__in=card_ids)

        excluded_card_ids.update(card_ids)

        self.interstitial = ReviewInterstitial(
            user, deck=deck, time_zone=time_zone,
            excluded_card_ids=excluded_card_ids)
