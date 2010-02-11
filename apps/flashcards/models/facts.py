from django.db import models
from django.contrib.auth.models import User
from django.forms import ModelForm
from django.forms.util import ErrorList
from dbtemplates.models import Template
from django.db.models import Q

from fields import FieldContent
from cards import MAX_NEW_CARD_ORDINAL
from decks import Deck
#import fields
import random
#from decks import Deck, SharedDeck
import usertagging
from django.db import transaction


def seconds_to_days(s):
    return s / 86400.0


class FactType(models.Model):
    name = models.CharField(max_length=50)
    active = models.BooleanField(default=True, blank=True)

    #e.g. for Example Sentences for Japanese facts
    parent_fact_type = models.ForeignKey('self', blank=True, null=True, related_name='child_fact_types')
    many_children_per_fact = models.NullBooleanField(blank=True, null=True)

    #not used for child fact types
    min_card_space = models.FloatField(default=seconds_to_days(600), help_text="Duration expressed in (partial) days.") #separate the cards of this fact initially
    space_factor = models.FloatField(default=.1) #minimal interval multiplier between two cards of the same fact
    
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
        '''Returns facts which have FieldContents containing the query.
        `query` is a substring to match on
        '''
        #TODO or is in_bulk() faster?
        query = query.strip()
        if not query_set:
            query_set = self.all()
        
        matches = FieldContent.objects.filter( \
                Q(content__icontains=query) \
                | Q(cached_transliteration_without_markup__icontains=query) \
                & Q(fact__fact_type=fact_type)).all()

        return query_set.filter(id__in=set(field_content.fact_id for field_content in matches))


    @transaction.commit_on_success    
    def add_new_facts_from_synchronized_decks(self, user, count, deck=None, tags=None):
        '''Returns the count of new facts added, after adding them for the user.
        '''
        if deck:
            if not deck.synchronized_with:
                return 0
            decks = [deck]
        else:
            decks = Deck.objects.synchronized_decks(user)
        user_facts = self.filter(deck__owner=user, deck__in=decks)
        if tags:
            tagged_facts = usertagging.models.UserTaggedItem.objects.get_by_model(Fact, tags)
            user_facts = user_facts.filter(fact__in=tagged_facts)
        shared_deck_ids = [deck.synchronized_with_id for deck in decks]
        new_shared_facts = self.filter(deck_id__in=shared_deck_ids).exclude(id__in=user_facts)
        new_shared_facts = new_shared_facts.order_by('new_fact_ordinal')
        #FIXME handle 0 ret
        
        # copy each fact
        created_count = len(new_shared_facts[count])
        for shared_fact in new_shared_facts[count]:
            if shared_fact.parent_fact:
                #child fact
                fact = Fact(
                    fact_type_id=shared_fact.fact_type_id,
                    active=shared_fact.active) #TODO should it be here?
                fact.parent_fact = shared_fact_to_fact[shared_fact.parent_fact]
                fact.save()
            else:
                #regular fact
                fact = Fact(
                    deck=deck,
                    fact_type_id=shared_fact.fact_type_id,
                    active=shared_fact.active, #TODO should it be here?
                    priority=shared_fact.priority,
                    notes=shared_fact.notes)
                fact.save()
                shared_fact_to_fact[shared_fact] = fact

            # don't copy the field contents - we will get them from the synchronized fact
            
            # copy the cards
            for shared_card in shared_fact.card_set.filter(active=True):
                card = cards.Card(
                    fact=fact,
                    template_id=shared_card.template_id,
                    priority=shared_card.priority,
                    leech=False, #shared_card.leech,
                    active=True, #shared_card.active, #TODO what to do with these ...
                    suspended=shared_card.suspended,
                    new_card_ordinal=shared_card.new_card_ordinal)
                card.save()
        return created_count





#TODO citation/fact source class


class AbstractFact(models.Model):
    fact_type = models.ForeignKey(FactType)
    
    active = models.BooleanField(default=True, blank=True)
    priority = models.IntegerField(default=0, null=True, blank=True) #TODO how to reconcile with card priorities?
    notes = models.CharField(max_length=1000, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    modified_at = models.DateTimeField(auto_now=True, editable=False)

    @property
    def ordered_fieldcontent_set(self):
        #field_types = self.fact_type.fieldtype_set.all()
        return self.fieldcontent_set.all().order_by('field_type__ordinal')
        

    class Meta:
        app_label = 'flashcards'
        abstract = True



class SharedFact(AbstractFact):
    deck = models.ForeignKey('SharedDeck', blank=True, null=True, db_index=True)
    
    #child facts (e.g. example sentences for a Japanese fact)
    parent_fact = models.ForeignKey('self', blank=True, null=True, related_name='child_facts')

    class Meta:
        app_label = 'flashcards'

usertagging.register(SharedFact)



class Fact(AbstractFact):
    objects = FactManager()
    deck = models.ForeignKey('Deck', blank=True, null=True, db_index=True)
    synchronized_with = models.ForeignKey('self', null=True, blank=True)
    new_fact_ordinal = models.PositiveIntegerField(null=True, blank=True)

    #child facts (e.g. example sentences for a Japanese fact)
    parent_fact = models.ForeignKey('self', blank=True, null=True, related_name='child_facts')


    def save(self):
        if not self.new_fact_ordinal:
            self.new_fact_ordinal = random.randrange(0, MAX_NEW_CARD_ORDINAL)
        super(Fact, self).save()


    @property
    def owner(self):
        return self.deck.owner


    @property
    def field_contents(self):
        '''Returns a dict of {field_type_id: field_content}
        '''
        fact = self
        field_contents = self.fieldcontent_set.all()
        if self.synchronized_with:
            # first see if the user has updated this fact's contents.
            # this would override the synced fact's.
            if not len(field_contents):
                field_contents = self.synchronized_with.fieldcontent_set.all()
        return dict((field_content.field_type_id, field_content) for field_content in field_contents)


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
        unique_together = (('deck', 'synchronized_with'),)


    def __unicode__(self):
        field_content_contents = []
        for field_content in self.fieldcontent_set.all():
            field_content_contents.append(field_content.content)
        return u' - '.join(field_content_contents)

usertagging.register(Fact)

