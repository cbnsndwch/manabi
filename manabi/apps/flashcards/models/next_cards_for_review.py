from manabi.apps.flashcards.models import (
    Card,
)


class ReviewInterstitial(object):
    def __init__(self, user, deck=None, time_zone=None):
        from manabi.apps.flashcards.models.review_availabilities import (
            ReviewAvailabilities,
        )

        self.review_availabilities = ReviewAvailabilities(
            user,
            deck=deck,
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
        # FIXME don't need 2 queries here...
        self.cards = Card.objects.filter(pk__in=[card.pk for card in next_cards])

        self.interstitial = ReviewInterstitial(
            user, deck=deck, time_zone=time_zone)
