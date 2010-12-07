from django.db import models
from django.contrib.auth.models import User
from django.forms import ModelForm
from django.forms.util import ErrorList
from dbtemplates.models import Template
from django.db.models import Avg

import datetime
import random
from django.db import transaction

from itertools import chain

import cards

import usertagging


class DeckManager(models.Manager):
    #@property
    #def card_count(self):
    #    return cards.Card.objects.of_user(self.owner).count()

    def values_of_all_with_stats_and_totals(self, user, fields=None):
        '''
        Returns all decks of a user (as a list of dictionaries), 
        with stats for each deck, 
        and an "All decks" item on top with totals
        '''
        decks = self.filter(owner=user).order_by('name').values() #TODO fields
        if fields:
            decks = decks.values(*fields)

        deck_values = []
        for deck in decks:
            #add stats for each deck
            deck_instance = Deck.objects.get(id=deck['id'])
            for property in ['card_count', 'due_card_count', 'new_card_count']:
                deck[property] = getattr(deck_instance, property)
            deck_values.append(deck)

        #add "All decks" top item with totals
        #TODO optimize by keeping totals above
        all_decks_option = {'id': -1, 
                            'name': 'All decks',
                            'card_count': cards.Card.objects.of_user(user).count(),
                            'due_card_count': cards.Card.objects.cards_due_count(user),
                            'new_card_count': cards.Card.objects.cards_new_count(user)}

        deck_values.insert(0, all_decks_option)

        return deck_values

    def of_user(self, user):
        return self.filter(owner=user, active=True)

    def shared_decks(self):
        return self.filter(shared=True, active=True)

    def synchronized_decks(self, user):
        return self.filter(owner=user, synchronized_with__isnull=False)


#TODO use this
#TODO rename to Book or something instead?
class Textbook(models.Model):
    name = models.CharField(max_length=100)
    edition = models.CharField(max_length=50, blank=True)
    description = models.TextField(max_length=2000, blank=True)
    purchase_url = models.URLField(blank=True) #TODO amazon referrals
    isbn = models.CharField(max_length=20, blank=True)
    cover_picture = models.FileField(upload_to='/textbook_media/', null=True, blank=True)
    #TODO student level field

    class Meta:
        app_label = 'flashcards'

    def __unicode__(self):
        return self.name


class Deck(models.Model):
    #manager
    objects = DeckManager()

    name = models.CharField(max_length=100)
    description = models.TextField(max_length=2000, blank=True)
    owner = models.ForeignKey(User, db_index=True)

    textbook_source = models.ForeignKey(Textbook, null=True, blank=True)

    picture = models.FileField(upload_to='/deck_media/', null=True, blank=True) #TODO upload to user directory, using .storage

    priority = models.IntegerField(default=0, blank=True)

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    modified_at = models.DateTimeField(auto_now=True, editable=False)

    # whether this is a publicly shared deck
    shared = models.BooleanField(default=False, blank=True)
    shared_at = models.DateTimeField(null=True, blank=True)
    # or if not, whether it's synchronized with a shared deck
    synchronized_with = models.ForeignKey('self', null=True, blank=True, related_name='subscriber_decks')
    active = models.BooleanField(default=True, blank=True)


    def __unicode__(self):
        return self.name
    
    class Meta:
        app_label = 'flashcards'
        #TODO unique_together = (('owner', 'name'), )
    
    def get_absolute_url(self):
        return '/flashcards/decks/{0}'.format(self.id)

    def delete(self, *args, **kwargs):
        # You shouldn't delete a shared deck - just set active=False
        self.subscriber_decks.clear()
        super(Deck, self).delete(*args, **kwargs)

    #def card_count(self):
    #    return cards.Card.objects.filter(fact__deck=self, active=True, suspended=False).count()
    #    #return self.fact_set.filter(active=True, suspended=False).count()


    def facts(self):
        '''Returns all Facts for this deck,
        including subscribed ones, not including subfacts.
        '''
        from facts import FieldContent
        if self.synchronized_with:
            updated_fields = FieldContent.objects.filter(fact__deck=self, fact__active=True, fact__synchronized_with__isnull=False) #fact__in=self.subscriber_facts.all())
            # 'other' here means non-updated, subscribed
            other_facts = Fact.objects.filter(parent_fact__isnull=True, id__in=updated_fields.values_list('fact', flat=True))
            other_fields = FieldContent.objects.filter(fact__deck=self.synchronized_with).exclude(fact__active=True, fact__in=other_facts.values_list('synchronized_with', flat=True))
            #active_subscribers = active_subscribers | other_fields
            return updated_fields | other_fields
        else:
            return FieldContent.objects.filter(fact__deck=self, fact__active=True)


    def field_contents(self):
        '''Returns all FieldContents for facts in this deck,
        preferring updated subscriber fields to subscribed ones,
        when the deck is synchronized.
        '''
        from facts import FieldContent
        if self.synchronized_with:
            updated_fields = FieldContent.objects.filter(fact__deck=self, fact__active=True, fact__synchronized_with__isnull=False) #fact__in=self.subscriber_facts.all())
            # 'other' here means non-updated, subscribed
            other_facts = Fact.objects.filter(parent_fact__isnull=True, id__in=updated_fields.values_list('fact', flat=True))
            other_fields = FieldContent.objects.filter(fact__deck=self.synchronized_with).exclude(fact__active=True, fact__in=other_facts.values_list('synchronized_with', flat=True))
            #active_subscribers = active_subscribers | other_fields
            return updated_fields | other_fields
        else:
            return FieldContent.objects.filter(fact__deck=self, fact__active=True)


    @property
    def has_subscribers(self):
        '''Returns whether there are subscribers to this deck, because
        it is shared, or it had been shared before.
        '''
        return self.subscriber_decks.filter(active=True).count() > 0


    @transaction.commit_on_success    
    def share(self):
        '''Shares this deck publicly.
        '''
        if self.synchronized_with:
            raise TypeError('Cannot share synchronized decks (decks which are already synchronized with shared decks).')
        self.shared = True
        self.shared_at = datetime.datetime.utcnow()
        self.save()


    @transaction.commit_on_success
    def unshare(self):
        '''Unshares this deck.
        '''
        if not self.shared:
            raise TypeError('This is not a shared deck, so it cannot be unshared.')
        self.shared = False
        self.save()


    @transaction.commit_on_success    
    def subscribe(self, user):
        '''Subscribes to this shared deck for the given user.
        They will study this deck as their own, but will 
        still receive updates to content.

        Returns the newly created deck.

        If the user was already subscribed to this deck, 
        returns the existing deck.
        '''
        from facts import Fact
        # check if the user is already subscribed to this deck
        existing_decks = Deck.objects.filter(owner=user, synchronized_with=self, active=True)
        if len(existing_decks):
            return existing_decks[0]

        if not self.shared:
            raise TypeError('This is not a shared deck - cannot subscribe to it.')
        if self.synchronized_with:
            raise TypeError('Cannot share a deck that is already synchronized to a shared deck.')

        #TODO dont allow multiple subscriptions to same deck by same user
        
        # copy the deck
        deck = Deck(
            synchronized_with=self,
            name=self.name,
            description=self.description,
            #TODO implement textbook=shared_deck.textbook, #picture too...
            priority=self.priority,
            owner_id=user.id)
        deck.save()

        # copy the tags
        deck.tags = usertagging.utils.edit_string_for_tags(self.tags)

        # create default deck scheduling options
        scheduling_options = SchedulingOptions(deck=deck)
        scheduling_options.save()

        # copy the facts - just the first few as a buffer
        shared_fact_to_fact = {}
        #TODO dont hardcode value here #chain(self.fact_set.all(), Fact.objects.filter(parent_fact__deck=self)):
        for shared_fact in self.fact_set.filter(active=True, parent_fact__isnull=True).order_by('new_fact_ordinal')[:10]: 
            #FIXME get the child facts for this fact too
            #if shared_fact.parent_fact:
            #    #child fact
            #    fact = Fact(
            #        fact_type=shared_fact.fact_type,
            #        active=shared_fact.active) #TODO should it be here?
            #    fact.parent_fact = shared_fact_to_fact[shared_fact.parent_fact]
            #    fact.save()
            #else:
            #   #regular fact
            fact = Fact(
                deck=deck,
                fact_type_id=shared_fact.fact_type_id,
                synchronized_with=shared_fact,
                active=True, #shared_fact.active, #TODO should it be here?
                priority=shared_fact.priority,
                new_fact_ordinal=shared_fact.new_fact_ordinal,
                notes=shared_fact.notes)
            fact.save()
            shared_fact_to_fact[shared_fact] = fact

            # don't copy the field contents for this fact - we'll get them from the shared fact later

            # copy the cards
            for shared_card in shared_fact.card_set.filter(active=True):
                card = cards.Card(
                    fact=fact,
                    template_id=shared_card.template_id,
                    priority=shared_card.priority,
                    leech=False, #shared_card.leech,
                    active=True,# shared_card.active,
                    suspended=shared_card.suspended,
                    new_card_ordinal=shared_card.new_card_ordinal)
                card.save()
        #done!
        return deck


    @property
    def card_count(self):
        deck = self.synchronized_with if self.synchronized_with else self
        return cards.Card.objects.filter(fact__deck=deck, active=True, suspended=False).count()

    @property
    def new_card_count(self):
        #FIXME do for sync'd decks
        return cards.Card.objects.cards_new_count(self.owner, deck=self, active=True, suspended=False)

    @property
    def due_card_count(self):
        return cards.Card.objects.cards_due_count(self.owner, deck=self, active=True, suspended=False)

    def average_ease_factor(self):
        deck_cards = cards.Card.objects.filter(fact__deck=self, active=True, suspended=False, ease_factor__isnull=False)
        if deck_cards.count():
            average_ef = deck_cards.aggregate(average_ease_factor=Avg('ease_factor'))['average_ease_factor']
            if average_ef:
                return average_ef
        return 2.5
    
    @transaction.commit_on_success    
    def delete_cascading(self):
        #FIXME if this is a shared/synced deck
        for fact in self.fact_set.all():
            for card in fact.card_set.all():
                card.delete()
            fact.delete()
        self.schedulingoptions.delete()
        self.delete()

usertagging.register(Deck)



class SchedulingOptions(models.Model):
    deck = models.OneToOneField(Deck)
    
    mature_unknown_interval_min = models.FloatField(default=0.333)
    mature_unknown_interval_max = models.FloatField(default=0.333)
    unknown_interval_min = models.FloatField(default=20.0/(24.0*60.0))  # 
    unknown_interval_max = models.FloatField(default=25.0/(24.0*60.0))  #TODO more? 0.5)
    hard_interval_min = models.FloatField(default=0.333)       #  8 hours
    hard_interval_max = models.FloatField(default=0.5)         # 12 hours
    medium_interval_min = models.FloatField(default=3.0)       #  3 days
    medium_interval_max = models.FloatField(default=5.0)       #  5 days
    easy_interval_min = models.FloatField(default=7.0)         #  7 days
    easy_interval_max = models.FloatField(default=9.0)         #  9 days

    def __unicode__(self):
        return self.deck.name

    class Meta:
        app_label = 'flashcards'
    
    #TODO should be classmethod
    def _generate_interval(self, min_duration, max_duration):
        return random.uniform(min_duration, max_duration) #TODO favor (random.triangular) conservatism

    def initial_interval(self, grade, do_fuzz=True):
        '''
        Generates an initial interval duration for a new card that's been reviewed.
        '''
        if grade == cards.GRADE_NONE:
            min, max = self.unknown_interval_min, self.unknown_interval_max
        if grade == cards.GRADE_HARD:
            min, max = self.hard_interval_min, self.hard_interval_max
        elif grade == cards.GRADE_GOOD:
            min, max = self.medium_interval_min, self.medium_interval_max
        elif grade == cards.GRADE_EASY:
            min, max = self.easy_interval_min, self.easy_interval_max
        
        if do_fuzz:
            return self._generate_interval(min, max)
        else:
            return (min + max) / 2.0








