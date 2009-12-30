from django.db import models
from django.contrib.auth.models import User
from django.forms import ModelForm
from django.forms.util import ErrorList
from dbtemplates.models import Template

from fields import FieldContent
#import fields

#from decks import Deck, SharedDeck

import usertagging


class FactType(models.Model):
    name = models.CharField(max_length=50)
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
    def all_tags_per_user(self, user):
        user_facts = self.filter(deck__owner=user).all()
        return usertagging.models.Tag.objects.usage_for_queryset(user_facts)
    
    def search(self, fact_type, query, query_set=None):
        '''
        Returns facts which have FieldContents containing the query.
        query is a substring
        '''
        #TODO or is in_bulk() faster?
        query = query.strip()
        if not query_set:
            query_set = self.all()
        return query_set.filter(id__in=set(field_content.fact_id for field_content in FieldContent.objects.filter(content__icontains=query, fact__fact_type=fact_type).all()))


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
    deck = models.ForeignKey('SharedDeck')
    
    class Meta:
        app_label = 'flashcards'

usertagging.register(SharedFact)


class Fact(AbstractFact):
    #manager
    objects = FactManager()

    deck = models.ForeignKey('Deck')

    @property
    def owner(self):
        return self.deck.owner

    class Meta:
        app_label = 'flashcards'

    def __unicode__(self):
        field_content_contents = []
        for field_content in self.fieldcontent_set.all():
            field_content_contents.append(field_content.content)
        return u' - '.join(field_content_contents)

usertagging.register(Fact)

