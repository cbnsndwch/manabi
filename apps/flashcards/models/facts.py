from django.db import models
from django.contrib.auth.models import User
from django.forms import ModelForm
from django.forms.util import ErrorList
from dbtemplates.models import Template

#from decks import Deck, SharedDeck


class FactType(models.Model):
    name = models.CharField(max_length=50)
    #owner = models.ForeignKey(User)
    active = models.BooleanField(default=True, blank=True)
    
    minimum_card_space = models.FloatField(default=60, help_text="Duration expressed in seconds.") #separate the cards of this fact initially
    minimum_space_factor = models.FloatField(default=.1) #minimal interval multiplier between two cards of the same fact
    
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    modified_at = models.DateTimeField(auto_now=True, editable=False)
    
    def __unicode__(self):
        return self.name
    
    class Meta:
        #unique_together = (('owner', 'name'), )
        app_label = 'flashcards'


class AbstractFact(models.Model):
    fact_type = models.ForeignKey(FactType)
    
    active = models.BooleanField(default=True, blank=True)
    
    priority = models.IntegerField(default=0, null=True, blank=True) #TODO how to reconcile with card priorities?
    
    notes = models.CharField(max_length=1000, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    modified_at = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        app_label = 'flashcards'
        abstract = True


class SharedFact(AbstractFact):
    deck = models.ForeignKey('SharedDeck')#SharedDeck)
    
    class Meta:
        app_label = 'flashcards'


class Fact(AbstractFact):
    deck = models.ForeignKey('Deck')#Deck)

    class Meta:
        app_label = 'flashcards'

