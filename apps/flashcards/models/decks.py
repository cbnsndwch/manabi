from django.db import models
from django.contrib.auth.models import User
from django.forms import ModelForm
from django.forms.util import ErrorList
from dbtemplates.models import Template

import random

import cards



class Deck(models.Model):
    owner = models.ForeignKey(User)
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    
    priority = models.IntegerField(default=0, blank=True)
    
    def __unicode__(self):
        return self.name
    
    class Meta:
        app_label = 'flashcards'
        unique_together = (('owner', 'name'), )
    
    ##GRADE GETTER FOR EASE


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

       
       

