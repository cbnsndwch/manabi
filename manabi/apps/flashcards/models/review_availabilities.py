from manabi.apps.flashcards.models import (
    Deck,
    Fact,
    Card,
)


class ReviewAvailabilities(object):
    def __init__(self):
        self.ready_for_review = True
        self.next_new_cards_count = 10 # FIXME
        self.early_review_available = False

        self.primary_prompt = "Primary prompt"
        self.secondary_prompt = "Secondary prompt"
