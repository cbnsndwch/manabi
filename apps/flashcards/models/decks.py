from django.db import models
from django.contrib.auth.models import User
from django.forms import ModelForm
from django.forms.util import ErrorList
from dbtemplates.models import Template

import random
from django.db import transaction

from fields import FieldContent, SharedFieldContent
import cards
from facts import Fact, SharedFact
#import fields
#import facts

import usertagging

class DeckManager(models.Manager):
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
                            'card_count': len(cards.Card.objects.of_user(user)),
                            'due_card_count': cards.Card.objects.cards_due_count(user),
                            'new_card_count': cards.Card.objects.cards_new_count(user)}

        deck_values.insert(0, all_decks_option)

        return deck_values
            



class AbstractDeck(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(max_length=2000, blank=True)

    priority = models.IntegerField(default=0, blank=True)

    class Meta:
        app_label = 'flashcards'
        abstract = True


class SharedDeck(AbstractDeck):
    creator = models.ForeignKey(User)

    downloads = models.PositiveIntegerField(default=0, blank=True)
    
    def __unicode__(self):
        return self.name
    
    class Meta:
        app_label = 'flashcards'
        #TODO unique_together = (('creator', 'name'), )

    #FIXME delete cascading
    
usertagging.register(SharedDeck)


class Deck(AbstractDeck):
    #manager
    objects = DeckManager()

    owner = models.ForeignKey(User)
    
    def __unicode__(self):
        return self.name
    
    class Meta:
        app_label = 'flashcards'
        #TODO unique_together = (('owner', 'name'), )
    
    @property
    def new_card_count(self):
        return cards.Card.objects.cards_new_count(self.owner, deck=self)

    @property
    def due_card_count(self):
        return cards.Card.objects.cards_due_count(self.owner, deck=self)

    @property
    def card_count(self):
        return len(cards.Card.objects.of_user(self.owner))

    def average_ease_factor(self):
        return 2.5 #FIXME
    
    @transaction.commit_on_success    
    def delete_cascading(self):
        for fact in self.fact_set.all():
            for card in fact.card_set.all():
                card.delete()
            fact.delete()
        self.schedulingoptions.delete()
        self.delete()

usertagging.register(Deck)



class SchedulingOptions(models.Model):
    deck = models.OneToOneField(Deck)

    #TODO make a custom 'range' field type
    unknown_interval_min = models.FloatField(default=0.006944) #10 mins #TODO is this right? 0.333)
    unknown_interval_max = models.FloatField(default=0.006944) #0.5)
    hard_interval_min = models.FloatField(default=0.333)
    hard_interval_max = models.FloatField(default=0.5)
    medium_interval_min = models.FloatField(default=3.0)
    medium_interval_max = models.FloatField(default=5.0)
    easy_interval_min = models.FloatField(default=7.0)
    easy_interval_max = models.FloatField(default=9.0)

    def __unicode__(self):
        return self.deck.name

    class Meta:
        app_label = 'flashcards'
    
    #TODO should be classmethod
    def _generate_interval(self, min_duration, max_duration):
        return random.uniform(min_duration, max_duration)

    def initial_interval(self, grade):
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
        #TODO raise an exception if the grade is something else
        
        return self._generate_interval(min, max)




@transaction.commit_on_success    
def share_deck(deck):
    '''Creates a SharedDeck containing all the facts and cards and their contents, given a user's Deck.''' 
    
    #copy the deck
    shared_deck = SharedDeck(
        name=deck.name,
        description=deck.description,
        priority=deck.priority,
        creator=deck.owner)
    shared_deck.save()

    #copy the facts
    #shared_fact_map = {}
    for fact in deck.fact_set.all():
        shared_fact = SharedFact(
            deck=shared_deck,
            fact_type=fact.fact_type,
            active=fact.active, #TODO should it be here?
            priority=fact.priority,
            notes=fact.notes)

        shared_fact.save()
        #shared_fact_map[shared_fact] = fact

        #copy the field contents for this fact
        for field_content in fact.fieldcontent_set.all():
            shared_field_content = SharedFieldContent(
                fact=shared_fact,
                field_type=field_content.field_type,
                content=field_content.content,
                media_uri=field_content.media_uri,
                media_file=field_content.media_file)

            shared_field_content.save()
                                                      
        #copy the cards
        for card in fact.card_set.filter(active=True):
            shared_card = cards.SharedCard(
                fact=shared_fact,
                template=card.template,
                priority=card.priority,
                leech=card.leech,
                active=True,#card.active,
                suspended=card.suspended,
                new_card_ordinal=card.new_card_ordinal)

            shared_card.save()

    #done!


@transaction.commit_on_success    
def download_shared_deck(user, shared_deck):
    '''Copies a shared deck and all its contents to a user's own deck library.'''
    
    #copy the deck
    deck = Deck(
        name=shared_deck.name,
        description=shared_deck.description,
        priority=shared_deck.priority,
        owner=user)
    deck.save()

    #create default deck scheduling options
    scheduling_options = SchedulingOptions(deck=deck)
    scheduling_options.save()

    #copy the facts
    #fact_map = {}
    for shared_fact in shared_deck.sharedfact_set.all():
        fact = Fact(
            deck=deck,
            fact_type=shared_fact.fact_type,
            active=shared_fact.active, #TODO should it be here?
            priority=shared_fact.priority,
            notes=shared_fact.notes)

        fact.save()
        #fact_map[fact] = shared_fact

        #copy the field contents for this fact
        for shared_field_content in shared_fact.sharedfieldcontent_set.all():
            field_content = FieldContent(
                fact=fact,
                field_type=shared_field_content.field_type,
                content=shared_field_content.content,
                media_uri=shared_field_content.media_uri,
                media_file=shared_field_content.media_file)

            field_content.save()
                                                      
        #copy the cards
        for shared_card in shared_fact.sharedcard_set.filter(active=True):
            card = cards.Card(
                fact=fact,
                template=shared_card.template,
                priority=shared_card.priority,
                leech=shared_card.leech,
                active=True,# shared_card.active,
                suspended=shared_card.suspended,
                new_card_ordinal=shared_card.new_card_ordinal)

            card.save()

    #done!

