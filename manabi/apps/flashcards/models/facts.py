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
        '''
        Purposed for the API. Deduplicates downstream facts.
        '''
        facts = self.with_upstream(user=deck.owner, deck=deck)
        facts = facts.exclude(id__in=facts.exclude(synchronized_with__isnull=True).values_list('synchronized_with_id', flat=True))
        return facts


    def with_upstream(self, user=None, deck=None):
        '''
        **WIP**: Was intended for use with lazy fact cloning.
        '''
        if deck is not None and user is not None and deck.owner != user:
            raise ValueError("Provided contradictory deck and user.")
        elif deck is None and user is None:
            raise ValueError("Must provide either deck or user.")

        if deck is not None:
            if deck.synchronized_with:
                return self.filter(Q(deck=deck) | Q(deck=deck.synchronized_with))

            return self.filter(deck=deck)

        return self.filter(
            Q(deck__owner=user) |
            Q(deck__subscriber_decks__owner=user)
        )

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

    #TODELETE, legacy.
    def get_for_owner_or_subscriber(self, fact_id, user):
        '''
        Returns a Fact object of the given id,
        or if the user is a subscriber to the deck of that fact,
        returns the subscriber's copy of that fact, which it
        creates if necessary.
        It will also create the associated cards.
        '''
        return Fact.objects.get(id=fact_id)

    #TODELETE, legacy.
    @transaction.atomic
    def add_new_facts_from_synchronized_decks(self, user, count, deck=None, tags=None):
        '''
        Returns a limited queryset of the new facts added,
        after adding them for the user.
        '''
        from cards import Card
        from decks import Deck

        if deck:
            if not deck.synchronized_with:
                return self.none()
            decks = Deck.objects.filter(id=deck.synchronized_with_id)
        else:
            decks = Deck.objects.synchronized_decks(user)

        user_facts = self.filter(deck__owner=user, deck__in=decks, active=True, parent_fact__isnull=True)

        if tags:
            raise Exception("user tagging disabled")
            #tagged_facts = UserTaggedItem.objects.get_by_model(Fact, tags)
            #user_facts = user_facts.filter(fact__in=tagged_facts)

        #shared_deck_ids = [deck.synchronized_with_id for deck in decks if deck.synchronized_with_id]
        new_shared_facts = self.filter(active=True, deck__in=decks.filter(
                synchronized_with__isnull=False)).exclude(id__in=user_facts)
        new_shared_facts = new_shared_facts.order_by('new_fact_ordinal')
        new_shared_facts = new_shared_facts[:count]
        #FIXME handle 0 ret

        # copy each fact
        for shared_fact in new_shared_facts:
            shared_fact.copy_to_deck(deck, synchronize=True)

        return new_shared_facts


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
    def pulls_from_upstream(self):
        return (not any([self.expression, self.reading, self.meaning]) and
                self.synchronized_with_id is not None)

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
        Returns a list of all the deck this object belongs to,
        including subscriber decks.
        '''
        return ([self.deck]
                + [d for d in self.deck.subscriber_decks.filter(active=True)])

    #TODELETE
    def copy_to_parent_fact(self, parent_fact):
        '''
        Copies a subfact to a parent fact.
        Returns the new copy, or the already existant one.
        If it already existed, it still copies the field contents,
        if needed.
        '''
        if not self.parent_fact:
            raise TypeError('This is not a subfact, so it cannot be copied to a parent fact.')
        # only copy if it doesn't already exist
        synchronize = parent_fact.synchronized_with == self.parent_fact
        if parent_fact.child_facts.filter(synchronized_with=self):
            subfact_copy = parent_fact.child_facts.get(synchronized_with=self)
        else:
            subfact_copy = Fact(
                    parent_fact=parent_fact,
                    fact_type=self.fact_type,
                    active=True,
                    notes=self.notes,
                    new_fact_ordinal=self.new_fact_ordinal)
            if synchronize:
                subfact_copy.synchronized_with = self
            subfact_copy.save()

        return subfact_copy

    #TODO-OLD
    def copy_to_deck(self, deck, copy_subfacts=False,
                     synchronize=False):
        '''
        Creates a copy of this fact and its cards and (optionally, if
        `synchronize` is False) field contents.

        If `synchronize` is True, the new fact will be subscribed to this one.
        Also copies its tags.

        Returns the newly copied fact.
        '''
        if self.parent_fact:
            raise TypeError('Cannot call this on a subfact.')

        copy = Fact(deck=deck,
                    fact_type=self.fact_type,
                    active=self.active,
                    notes=self.notes,
                    new_fact_ordinal=self.new_fact_ordinal)

        if synchronize:
            if self.synchronized_with:
                raise TypeError('Cannot synchronize with a fact that is already a synchronized fact.')
            elif not self.deck.shared_at:
                raise TypeError('This is not a shared fact - cannot synchronize with it.')
            #TODO-OLD enforce deck synchronicity too
            else:
                copy.synchronized_with = self

        copy.save()

        # copy the cards
        from cards import Card
        for shared_card in self.card_set.filter(active=True):
            card = shared_card.copy(copy)
            card.save()

        # copy the tags too
        #copy.tags = usertagging.utils.edit_string_for_tags(self.tags)

        # copy any subfacts
        if copy_subfacts or not synchronize:
            for subfact in self.child_facts.filter(active=True):
                subfact.copy_to_parent_fact(copy)
        return copy

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

    #e.g. for Example Sentences for Japanese facts
    parent_fact_type = models.ForeignKey('self',
            blank=True, null=True, related_name='child_fact_types')
    many_children_per_fact = models.NullBooleanField(blank=True, null=True)


    #TODELETE
    # minimal interval multiplier between two cards of the same fact
    space_factor = models.FloatField(default=.1)

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    modified_at = models.DateTimeField(auto_now=True, editable=False)

    def __unicode__(self):
        if self.parent_fact_type:
            return self.parent_fact_type.name + ' - ' + self.name
        return self.name

    class Meta:
        app_label = 'flashcards'
