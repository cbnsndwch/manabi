import datetime

from cachecow.decorators import cached_function
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import models
from django.db import transaction
from django.db.models.query import QuerySet

from manabi.apps.manabi_redis.models import redis
from manabi.apps.books.models import Textbook
from constants import DEFAULT_EASE_FACTOR
from manabi.apps.flashcards.cachenamespaces import deck_review_stats_namespace
import cards
#from manabi.apps import usertagging


class DeckQuerySet(QuerySet):
    def of_user(self, user):
        return self.filter(owner=user, active=True)

    def shared_decks(self):
        return self.filter(shared=True, active=True)

    def synchronized_decks(self, user):
        return self.filter(owner=user, synchronized_with__isnull=False)


class Deck(models.Model):
    objects = DeckQuerySet.as_manager()

    name = models.CharField(max_length=100)
    description = models.TextField(max_length=2000, blank=True)
    owner = models.ForeignKey(User, db_index=True, editable=False)

    textbook_source = models.ForeignKey(Textbook, null=True, blank=True)

    picture = models.FileField(upload_to='/deck_media/', null=True, blank=True)
    #TODO-OLD upload to user directory, using .storage

    priority = models.IntegerField(default=0, blank=True)

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    modified_at = models.DateTimeField(auto_now=True, editable=False)

    # whether this is a publicly shared deck
    shared = models.BooleanField(default=False, blank=True)
    shared_at = models.DateTimeField(null=True, blank=True, editable=False)
    # or if not, whether it's synchronized with a shared deck
    synchronized_with = models.ForeignKey('self',
            null=True, blank=True, related_name='subscriber_decks')

    # "active" is just a soft deletion flag. "suspended" is temporarily
    # disabled.
    suspended = models.BooleanField(default=False, db_index=True)
    active = models.BooleanField(default=True, blank=True, db_index=True)

    def __unicode__(self):
        return u'{0} ({1})'.format(self.name, self.owner)

    class Meta:
        app_label = 'flashcards'
        ordering = ('name',)
        #TODO-OLD unique_together = (('owner', 'name'), )

    def get_absolute_url(self):
        return reverse('deck_detail', kwargs={'deck_id': self.id})

    def delete(self, *args, **kwargs):
        # You shouldn't delete a shared deck - just set active=False
        self.subscriber_decks.clear()
        super(Deck, self).delete(*args, **kwargs)

    def fact_tags(self):
        '''
        Returns tags for all facts inside this deck.
        Includes tags on facts made on subscribed facts.
        '''
        #return usertagging.models.Tag.objects.usage_for_queryset(
            #self.facts())
        from facts import Fact
        deck_facts = Fact.objects.with_upstream(
            self.owner, deck=self)
        return usertagging.models.Tag.objects.usage_for_queryset(
            deck_facts)

    @property
    def has_subscribers(self):
        '''
        Returns whether there are subscribers to this deck, because
        it is shared, or it had been shared before.
        '''
        return self.subscriber_decks.filter(active=True).exists()

    @transaction.atomic
    def share(self):
        '''
        Shares this deck publicly.
        '''
        if self.synchronized_with:
            raise TypeError('Cannot share synchronized decks (decks which are already synchronized with shared decks).')

        self.shared = True
        self.shared_at = datetime.datetime.utcnow()
        self.save()

    @transaction.atomic
    def unshare(self):
        '''
        Unshares this deck.
        '''
        if not self.shared:
            raise TypeError('This is not a shared deck, so it cannot be unshared.')

        self.shared = False
        self.save()

    def get_subscriber_deck_for_user(self, user):
        '''
        Returns the subscriber deck for `user` of this deck.
        If it doesn't exist, returns None.
        If multiple exist, even though this shouldn't happen,
        we just return the first one.
        '''
        subscriber_decks = self.subscriber_decks.filter(owner=user, active=True)

        if subscriber_decks.exists():
            return subscriber_decks[0]

    #TODO implement subscribing with new stuff.
    @transaction.atomic
    def subscribe(self, user):
        '''
        Subscribes to this shared deck for the given user.
        They will study this deck as their own, but will
        still receive updates to content.

        Returns the newly created deck.

        If the user was already subscribed to this deck,
        returns the existing deck.
        '''
        from facts import Fact

        # check if the user is already subscribed to this deck
        subscriber_deck = self.get_subscriber_deck_for_user(user)
        if subscriber_deck:
            return subscriber_deck

        if not self.shared:
            raise TypeError('This is not a shared deck - cannot subscribe to it.')
        if self.synchronized_with:
            raise TypeError('Cannot share a deck that is already synchronized to a shared deck.')

        #TODO-OLD dont allow multiple subscriptions to same deck by same user

        # copy the deck
        deck = Deck(
            synchronized_with=self,
            name=self.name,
            description=self.description,
            #TODO-OLD implement textbook=shared_deck.textbook, #picture too...
            priority=self.priority,
            textbook_source=self.textbook_source,
            owner_id=user.id)
        deck.save()

        # copy the tags
        # deck.tags = usertagging.utils.edit_string_for_tags(self.tags)

        # copy the facts - just the first few as a buffer
        shared_fact_to_fact = {}
        #TODO-OLD dont hardcode value here #chain(self.fact_set.all(), Fact.objects.filter(parent_fact__deck=self)):
        for shared_fact in self.fact_set.filter(active=True, parent_fact__isnull=True).order_by('new_fact_ordinal')[:10]:
            #FIXME get the child facts for this fact too
            #if shared_fact.parent_fact:
            #    #child fact
            #    fact = Fact(
            #        fact_type=shared_fact.fact_type,
            #        active=shared_fact.active) #TODO-OLD should it be here?
            #    fact.parent_fact = shared_fact_to_fact[shared_fact.parent_fact]
            #    fact.save()
            #else:
            #   #regular fact
            fact = Fact(
                deck=deck,
                fact_type_id=shared_fact.fact_type_id,
                synchronized_with=shared_fact,
                active=True, #shared_fact.active, #TODO-OLD should it be here?
                priority=shared_fact.priority,
                new_fact_ordinal=shared_fact.new_fact_ordinal,
                notes=shared_fact.notes)
            fact.save()
            shared_fact_to_fact[shared_fact] = fact

            # don't copy the field contents for this fact - we'll get them from
            # the shared fact later

            # copy the cards
            for shared_card in shared_fact.card_set.filter(active=True):
                card = shared_card.copy(fact)
                card.save()
        #done!
        return deck

    def card_count(self):
        return cards.Card.objects.of_deck(self, with_upstream=True).available().count()

    #TODO-OLD kill - unused?
    #@property
    #def new_card_count(self):
    #    return Card.objects.approx_new_count(deck=self)
    #    #FIXME do for sync'd decks
    #    return cards.Card.objects.cards_new_count(
    #            self.owner, deck=self, active=True, suspended=False)

    #TODO-OLD kill - unused?
    #@property
    #def due_card_count(self):
    #    return cards.Card.objects.cards_due_count(
    #            self.owner, deck=self, active=True, suspended=False)

    @cached_function(namespace=deck_review_stats_namespace)
    def average_ease_factor(self):
        '''
        Includes suspended cards in the calcuation. Doesn't include inactive cards.
        '''
        ease_factors = redis.zrange('ease_factor:deck:{0}'.format(self.id),
                                    0, -1, withscores=True)
        cardinality = len(ease_factors)
        if cardinality:
            return sum(score for val,score in ease_factors) / cardinality
        return DEFAULT_EASE_FACTOR

    @transaction.atomic
    def delete_cascading(self):
        #FIXME if this is a shared/synced deck
        for fact in self.fact_set.all():
            for card in fact.card_set.all():
                card.delete()
            fact.delete()
        self.delete()
