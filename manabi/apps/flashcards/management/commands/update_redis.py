from django.core.management.base import BaseCommand

from manabi.apps.flashcards.models.constants import (
    GRADE_NONE, GRADE_HARD, GRADE_GOOD, GRADE_EASY,
    MAX_NEW_CARD_ORDINAL, EASE_FACTOR_MODIFIERS,
    YOUNG_FAILURE_INTERVAL, MATURE_FAILURE_INTERVAL,
    MATURE_INTERVAL_MIN, GRADE_EASY_BONUS_FACTOR,
    DEFAULT_EASE_FACTOR, INTERVAL_FUZZ_MAX,
    ALL_GRADES, GRADE_NAMES)
from manabi.apps.flashcards.models import Card
from manabi.apps.manabi_redis.models import redis



def active_cards():
    pass


def update_redis():
    for card in Card.objects.all():
        card.redis.update_all()


class Command(BaseCommand):
    def handle(self, *args, **options):
        if args and args[0].lower() == 'flush':
            redis.flushdb()
        update_redis()

