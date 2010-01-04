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

    #e.g. for Example Sentences for Japanese facts
    parent_fact_type = models.ForeignKey('self', blank=True, null=True, related_name='child_fact_types')
    many_children_per_fact = models.NullBooleanField(blank=True, null=True)

    #not used for child fact types
    minimum_card_space = models.FloatField(default=60, help_text="Duration expressed in seconds.") #separate the cards of this fact initially
    minimum_space_factor = models.FloatField(default=.1) #minimal interval multiplier between two cards of the same fact
    
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    modified_at = models.DateTimeField(auto_now=True, editable=False)
    
    def __unicode__(self):
        if self.parent_fact_type:
            return self.parent_fact_type.name + ' - ' + self.name
        else:
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


#TODO citation/fact source class


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
    deck = models.ForeignKey('SharedDeck', blank=True, null=True)
    
    #child facts (e.g. example sentences for a Japanese fact)
    parent_fact = models.ForeignKey('self', blank=True, null=True, related_name='child_facts')

    class Meta:
        app_label = 'flashcards'

usertagging.register(SharedFact)


class Fact(AbstractFact):
    #manager
    objects = FactManager()

    deck = models.ForeignKey('Deck', blank=True, null=True)

    #child facts (e.g. example sentences for a Japanese fact)
    parent_fact = models.ForeignKey('self', blank=True, null=True, related_name='child_facts')

    @property
    def owner(self):
        return self.deck.owner

    def fieldcontent_set_plus_blank_fields(self):
        '''
        Returns self.fieldcontent_set, but adds mock 
        FieldContent objects for any FieldTypes of this 
        fact's FactType which do not have corresponding 
        FieldContent objects.
        (e.g. a fact without a notes field, so that 
        the notes field can be included in an update form.)
        '''
        #field_contents = self.fieldcontent_set.all()
        #TODO add this

    class Meta:
        app_label = 'flashcards'

    def __unicode__(self):
        field_content_contents = []
        for field_content in self.fieldcontent_set.all():
            field_content_contents.append(field_content.content)
        return u' - '.join(field_content_contents)

usertagging.register(Fact)

