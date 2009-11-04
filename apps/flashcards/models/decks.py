from django.db import models
from django.contrib.auth.models import User
from django.forms import ModelForm
from django.forms.util import ErrorList
from dbtemplates.models import Template

import random

import cards


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
    

class Deck(AbstractDeck):
    owner = models.ForeignKey(User)
    
    def __unicode__(self):
        return self.name
    
    class Meta:
        app_label = 'flashcards'
        #TODO unique_together = (('owner', 'name'), )
    
    def average_ease_factor(self):
        return 2.5 #FIXME



class SchedulingOptions(models.Model):
    deck = models.OneToOneField(Deck)

    #TODO make a custom 'range' field type
    unknown_interval_min = models.FloatField(default=0.333)
    unknown_interval_max = models.FloatField(default=0.5)
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
    shared_fact_map = {}
    shared_field_content_map = {}
    for fact in deck.fact_set.all():
        shared_fact = SharedFact(
            deck=shared_deck,
            fact_type=fact.fact_type,
            active=fact.active, #TODO should it be here?
            priority=fact.priority,
            notes=fact.notes)

        shared_fact.save()
        shared_fact_map[shared_fact] = fact

        #copy the field contents for this fact
        for field_content in fact.fieldcontent_set.all():
            shared_field_content = SharedFieldContent(
                fact=shared_fact,
                field_type=field_content.field_type,
                contents=field_content.content,
                media_url=field_content.media_url,
                media_file=field_content.media_file)

            shared_field_content.save()
                                                      
        #copy the cards
        for card in fact.card_set.all():
            shared_card = SharedCard(
                fact=shared_fact,
                template=card.template,
                priority=card.priority,
                leech=card.leech,
                active=card.active,
                suspended=card.suspended,
                new_card_ordinal=card.new_card_ordinal)

            shared_card.save()





