from manabi.apps.flashcards.models import (
    Deck,
    Fact,
    Card,
)


class ReviewInterstitial(object):
    def __init__(self):
        self.ready_for_review = True
        self.next_new_cards_count = 10 # FIXME


class NextCardsForReview(object):
    def __init__(self, user, count):
        next_cards = Card.objects.next_cards(
            user,
            count,
            #TODO
        )
        # FIXME don't need 2 queries here...
        self.cards = Card.objects.filter(pk__in=[card.pk for card in next_cards])

        self.interstitial = ReviewInterstitial()
