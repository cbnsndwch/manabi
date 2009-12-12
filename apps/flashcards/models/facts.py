from django.db import models
from django.contrib.auth.models import User
from django.forms import ModelForm
from django.forms.util import ErrorList
from dbtemplates.models import Template

from fields import FieldContent
#import fields

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



class FactManager(models.Manager):
    def search(self, user, fact_type, query):
        '''
        Returns facts which have FieldContents containing the query.
        query is a substring
        '''
        #TODO or is in_bulk() faster?
        query = query.strip()
        return Fact.objects.filter(id__in=set(field_content.fact_id for field_content in FieldContent.objects.filter(content__icontains=query, fact__deck__owner=user, fact__fact_type=fact_type).all()))


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
    #manager
    objects = FactManager()

    deck = models.ForeignKey('Deck')#Deck)

    class Meta:
        app_label = 'flashcards'

    def __unicode__(self):
        field_content_contents = []
        for field_content in self.fieldcontent_set.all():
            field_content_contents.append(field_content.content)
        return u' - '.join(field_content_contents)

