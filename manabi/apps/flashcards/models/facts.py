import datetime
from datetime import timedelta
import random

from django.db.models.query import QuerySet
from django.contrib.auth.models import User
from django.db import models, transaction
from django.db.models import Q, F
from natto import MeCab

from constants import MAX_NEW_CARD_ORDINAL
from fields import FieldContent
from manabi.apps.flashcards.signals import fact_suspended, fact_unsuspended
from manabi.apps.flashcards.models.constants import GRADE_NONE, MIN_CARD_SPACE, CARD_SPACE_FACTOR



#TODO-OLD
# separate the cards of this fact initially
# not used for child fact types (?)
#min_card_space = models.FloatField(default=seconds_to_days(600),
#        help_text='Duration expressed in (partial) days.')
#TODO-OLD
# minimal interval multiplier between two cards of the same fact
#space_factor = models.FloatField(default=.1)


class FactQuerySet(QuerySet):
    def deck_facts(self, deck):
        return self.filter(deck=deck)

    def buried(self, user, review_time=None, excluded_card_ids=[]):
        '''
        Facts with cards buried due to siblings.
        '''
        if review_time is None:
            review_time = datetime.datetime.utcnow()

        return self.filter(
            Q(card__deck__owner=user) & (
                # Sibling is due.
                Q(card__due_at__lt=review_time) |
                # Sibling was reviewed too recently.
                (
                    Q(card__last_reviewed_at__gte=(
                        review_time - timedelta(days=MIN_CARD_SPACE))) &
                    Q(card__last_reviewed_at__gte=(
                        review_time - F('card__interval') * CARD_SPACE_FACTOR))
                ) |
                # Sibling is currently in the client-side review queue.
                Q(card__id__in=excluded_card_ids) |
                # Sibling is failed. (Either sibling's due, or it's shown before new cards.)
                Q(card__last_review_grade=GRADE_NONE)
            )
        )


def _card_template_id_to_string(card_template_id):
    from manabi.apps.flashcards.models import (
        PRODUCTION, RECOGNITION, KANJI_READING, KANJI_WRITING)

    return {
        PRODUCTION: 'production',
        RECOGNITION: 'recognition',
        KANJI_READING: 'kanji_reading',
        KANJI_WRITING: 'kanji_writing',
    }[card_template_id]


def _card_template_string_to_id(card_template):
    from manabi.apps.flashcards.models import (
        PRODUCTION, RECOGNITION, KANJI_READING, KANJI_WRITING)

    return {
        'production': PRODUCTION,
        'recognition': RECOGNITION,
        'kanji_reading': KANJI_READING,
        'kanji_writing': KANJI_WRITING,
    }[card_template]


class Fact(models.Model):
    objects = FactQuerySet.as_manager()

    deck = models.ForeignKey('flashcards.Deck', db_index=True)

    synchronized_with = models.ForeignKey(
        'self', null=True, blank=True, related_name='subscriber_facts')

    new_fact_ordinal = models.PositiveIntegerField(null=True, blank=True)
    active = models.BooleanField(default=True, blank=True)

    expression = models.CharField(max_length=500)
    reading = models.CharField(max_length=1500, blank=True)
    meaning = models.CharField(max_length=1000)

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    modified_at = models.DateTimeField(blank=True, null=True)

    suspended = models.BooleanField(default=False)

    def roll_ordinal(self):
        if not self.new_fact_ordinal:
            self.new_fact_ordinal = random.randrange(0, MAX_NEW_CARD_ORDINAL)

    def save(self, *args, **kwargs):
        '''
        Set a random sorting index for new cards.
        '''
        self.roll_ordinal()
        super(Fact, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self.subscriber_facts.filter(modified_at__gt=self.created_at).delete()
        self.subscriber_facts.update(synchronized_with=None)
        super(Fact, self).delete(*args, **kwargs)

    @property
    def owner(self):
        return self.deck.owner

    @property
    def card_count(self):
        return self.card_set.filter(active=True).count()

    @property
    def active_card_templates(self):
        from manabi.apps.flashcards.models import PRODUCTION

        template_ids = (
            self.card_set.available().values_list('template', flat=True)
        )

        return {
            _card_template_id_to_string(id_) for id_ in template_ids
        }

    def set_active_card_templates(self, card_templates):
        '''
        Creates or updates associated `Card`s.
        '''
        from manabi.apps.flashcards.models import Card

        template_ids = {
            _card_template_string_to_id(template)
            for template in card_templates
        }

        self.card_set.filter(template__in=template_ids).update(active=True)
        self.card_set.exclude(template__in=template_ids).update(active=False)

        existing_template_ids = set(self.card_set.values_list(
            'template', flat=True))

        for template_id in template_ids - existing_template_ids:
            Card.objects.create(
                deck=self.deck,
                fact=self,
                template=template_id,
                new_card_ordinal=Card.random_card_ordinal(),
            )

    def suspend(self):
        self.card_set.update(suspended=True)
        self.suspended = True
        self.save()
        fact_suspended.send(sender=self, instance=self)

    def unsuspend(self):
        self.card_set.update(suspended=False)
        self.suspended = False
        self.save()
        fact_unsuspended.send(sender=self, instance=self)

    #TODELETE?
    def all_owner_decks(self):
        '''
        Returns a list of all the decks this object belongs to,
        including subscriber decks.
        '''
        return ([self.deck]
                + [d for d in self.deck.subscriber_decks.filter(active=True)])

    class Meta:
        app_label = 'flashcards'
        unique_together = (('deck', 'synchronized_with'),)

    def __unicode__(self):
        return unicode(self.id)



#############
# OLD:


#TODELETE
class FactTypeQuerySet(QuerySet):
    @property
    def japanese(self):
        # Unfortunately hard-coded for now, since we only have 2 types, and
        # this is a relic of an old abandoned design that should be refactored.
        return self.get(id=1)

    def example_sentences(self):
        return self.get(id=2)


#TODELETE
class FactType(models.Model):
    objects = FactTypeQuerySet.as_manager()

    name = models.CharField(max_length=50)
    active = models.BooleanField(default=True, blank=True)

    many_children_per_fact = models.NullBooleanField(blank=True, null=True)

    #TODELETE
    # minimal interval multiplier between two cards of the same fact
    space_factor = models.FloatField(default=.1)

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    modified_at = models.DateTimeField(auto_now=True, editable=False)

    def __unicode__(self):
        return self.name

    class Meta:
        app_label = 'flashcards'
