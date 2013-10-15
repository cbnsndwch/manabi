import pickle
import random

from django.db.models.query import QuerySet
from django.contrib.auth.models import User
from django.db import models, transaction
from django.db.models import Q
from django.forms import ModelForm
from django.forms.util import ErrorList
from model_utils.managers import PassThroughManager

from constants import MAX_NEW_CARD_ORDINAL
from fields import FieldContent
from manabi.apps.flashcards.signals import fact_suspended, fact_unsuspended
from manabi.apps import usertagging
from manabi.apps.usertagging.models import UserTaggedItem




#TODO-OLD 
# separate the cards of this fact initially
# not used for child fact types (?)
#min_card_space = models.FloatField(default=seconds_to_days(600),
#        help_text='Duration expressed in (partial) days.')
#TODO-OLD
# minimal interval multiplier between two cards of the same fact
#space_factor = models.FloatField(default=.1) 


class FactManager(models.Manager):
    def all_tags_per_user(self, user):
        '''
        Includes tags on facts made on subscribed facts.
        '''
        user_facts = self.with_upstream(user)
        return usertagging.models.Tag.objects.usage_for_queryset(
                user_facts)
    
    #TODO-OLD
    def search(self, fact_type, query, query_set=None):
        '''Returns facts which have FieldContents containing the query.
        `query` is a substring to match on
        '''
        #TODO-OLD or is in_bulk() faster?
        query = query.strip()
        if not query_set:
            query_set = self.filter(parent_fact__isnull=True)

        subscriber_facts = Fact.objects.filter(
                synchronized_with__in=query_set)

        matches = FieldContent.objects.filter(
            Q(content__icontains=query)
            | Q(cached_transliteration_without_markup__icontains=query)
            & (Q(fact__in=query_set)
               | Q(fact__synchronized_with__in=subscriber_facts)))
            #& Q(fact__fact_type=fact_type)).all()

        #TODO-OLD use values_list to be faster
        match_ids = matches.values_list('fact', flat=True)
        return query_set.filter(Q(id__in=match_ids) |
                                Q(synchronized_with__in=match_ids))
        #return query_set.filter(id__in=set(field_content.fact_id 
        #for field_content in matches))

    #TODELETE, legacy.
    def get_for_owner_or_subscriber(self, fact_id, user):
        '''
        Returns a Fact object of the given id,
        or if the user is a subscriber to the deck of that fact,
        returns the subscriber's copy of that fact, which it 
        creates if necessary.
        It will also create the associated cards.
        '''
        return Fact.objects.get(id=fact_id)

    #TODELETE, legacy.
    @transaction.commit_on_success
    def add_new_facts_from_synchronized_decks(self, user, count, deck=None, tags=None):
        '''
        Returns a limited queryset of the new facts added,
        after adding them for the user.
        '''
        from cards import Card
        from decks import Deck

        if deck:
            if not deck.synchronized_with:
                return self.none()
            decks = Deck.objects.filter(id=deck.synchronized_with_id)
        else:
            decks = Deck.objects.synchronized_decks(user)

        user_facts = self.filter(deck__owner=user, deck__in=decks, active=True, parent_fact__isnull=True)

        if tags:
            tagged_facts = UserTaggedItem.objects.get_by_model(Fact, tags)
            user_facts = user_facts.filter(fact__in=tagged_facts)

        #shared_deck_ids = [deck.synchronized_with_id for deck in decks if deck.synchronized_with_id]
        new_shared_facts = self.filter(active=True, deck__in=decks.filter(
                synchronized_with__isnull=False)).exclude(id__in=user_facts)
        new_shared_facts = new_shared_facts.order_by('new_fact_ordinal')
        new_shared_facts = new_shared_facts[:count]
        #FIXME handle 0 ret
        
        # copy each fact
        for shared_fact in new_shared_facts:
            shared_fact.copy_to_deck(deck, synchronize=True)

        return new_shared_facts


class Fact(models.Model):
    objects = FactManager()

    deck = models.ForeignKey('flashcards.Deck', blank=True, null=True, db_index=True)

    synchronized_with = models.ForeignKey(
        'self', null=True, blank=True, related_name='subscriber_facts')
    new_fact_ordinal = models.PositiveIntegerField(null=True, blank=True)
    active = models.BooleanField(default=True, blank=True)

    expression = models.CharField(max_length=500)
    reading = models.CharField(max_length=1500, blank=True)
    meaning = models.CharField(max_length=1000)

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    modified_at = models.DateTimeField(blank=True, null=True)

    def roll_ordinal(self):
        if not self.new_fact_ordinal:
            self.new_fact_ordinal = random.randrange(0, MAX_NEW_CARD_ORDINAL)

    def save(self, *args, **kwargs):
        '''
        Set a random sorting index for new cards.
        '''
        self.roll_ordinal()
        super(Fact, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self.subscriber_facts.filter(modified_at__gt=self.created_at).delete()
        self.subscriber_facts.update(synchronized_with=None)
        super(Fact, self).delete(*args, **kwargs)

    @property
    def owner(self):
        return self.deck.owner

    @property
    def field_contents(self):
        '''
        Returns a queryset of field contents for this fact.
        ?dict of {field_type_id: field_content}
        Includes field contents of any subfacts of this fact.
        '''
        fact = self
        field_contents = \
            self.fieldcontent_set.all().order_by('field_type__ordinal')
        #sub_field_contents = \
        #    FieldContent.objects.filter(fact__in=self.child_facts.all())
        if self.synchronized_with:
            # first see if the user has updated this fact's contents.
            # this would override the synced fact's.
            #TODO-OLD only override on a per-field basis when the 
            #user updates field contents
            if not field_contents:
                field_contents = self.synchronized_with.fieldcontent_set.all().order_by('field_type__ordinal')
        #return dict((field_content.field_type_id, field_content) for field_content in field_contents)
        return field_contents

    def suspended(self):
        '''Returns whether this fact's cards are all suspended.'''
        cards = self.card_set.filter(active=True)
        return cards.exists() and not cards.filter(suspended=False).exists()

    def suspend(self):
        for card in self.card_set.all():
            card.suspended = True
            card.save()
            fact_suspended.send(sender=self, instance=self)
        
    def unsuspend(self):
        for card in self.card_set.all():
            card.suspended = False
            card.save()
            fact_unsuspended.send(sender=self, instance=self)

    #TODELETE?
    def all_owner_decks(self):
        '''
        Returns a list of all the deck this object belongs to,
        including subscriber decks.
        '''
        return ([self.deck]
                + [d for d in self.deck.subscriber_decks.filter(active=True)])

    #TODELETE
    def copy_to_parent_fact(self, parent_fact, copy_field_contents=False):
        '''
        Copies a subfact to a parent fact.
        Returns the new copy, or the already existant one.
        If it already existed, it still copies the field contents,
        if needed.
        '''
        if not self.parent_fact:
            raise TypeError('This is not a subfact, so it cannot be copied to a parent fact.')
        # only copy if it doesn't already exist
        synchronize = parent_fact.synchronized_with == self.parent_fact
        if parent_fact.child_facts.filter(synchronized_with=self):
            subfact_copy = parent_fact.child_facts.get(synchronized_with=self)
        else:
            subfact_copy = Fact(
                    parent_fact=parent_fact,
                    fact_type=self.fact_type,
                    active=True,
                    notes=self.notes,
                    new_fact_ordinal=self.new_fact_ordinal)
            if synchronize:
                subfact_copy.synchronized_with = self
            subfact_copy.save()

        # copy the field contents
        if copy_field_contents or not synchronize:
            for field_content in self.fieldcontent_set.all():
                field_content.copy_to_fact(subfact_copy)
        return subfact_copy

    #TODO-OLD
    def copy_to_deck(self, deck, copy_field_contents=False, copy_subfacts=False,
                     synchronize=False):
        '''
        Creates a copy of this fact and its cards and (optionally, if
        `synchronize` is False) field contents.

        If `synchronize` is True, the new fact will be subscribed to this one.
        Also copies its tags.

        Returns the newly copied fact.
        '''
        if self.parent_fact:
            raise TypeError('Cannot call this on a subfact.')

        copy = Fact(deck=deck,
                    fact_type=self.fact_type,
                    active=self.active,
                    notes=self.notes,
                    new_fact_ordinal=self.new_fact_ordinal)

        if synchronize:
            if self.synchronized_with:
                raise TypeError('Cannot synchronize with a fact that is already a synchronized fact.')
            elif not self.deck.shared_at:
                raise TypeError('This is not a shared fact - cannot synchronize with it.')
            #TODO-OLD enforce deck synchronicity too
            else:
                copy.synchronized_with = self

        copy.save()

        # copy the field contents
        if copy_field_contents or not synchronize:
            for field_content in self.fieldcontent_set.all():
                field_content.copy_to_fact(copy)

        # copy the cards
        from cards import Card
        for shared_card in self.card_set.filter(active=True):
            card = shared_card.copy(copy)
            card.save()

        # copy the tags too
        copy.tags = usertagging.utils.edit_string_for_tags(self.tags)

        # copy any subfacts
        if copy_subfacts or not synchronize:
            for subfact in self.child_facts.filter(active=True):
                subfact.copy_to_parent_fact(copy, copy_field_contents=True)
        return copy

    class Meta:
        app_label = 'flashcards'
        unique_together = (('deck', 'synchronized_with'),)

    def __unicode__(self):
        return unicode(self.id)
        field_content_contents = []
        for field_content in self.fieldcontent_set.all():
            field_content_contents.append(field_content.content)
        return u' - '.join(field_content_contents)

usertagging.register(Fact)




#############
# OLD:


#TODELETE
class FactTypeQuerySet(QuerySet):
    @property
    def japanese(self):
        # Unfortunately hard-coded for now, since we only have 2 types, and 
        # this is a relic of an old abandoned design that should be refactored.
        return self.get(id=1)
    
    def example_sentences(self):
        return self.get(id=2)


#TODELETE
class FactType(models.Model):
    objects = PassThroughManager.for_queryset_class(FactTypeQuerySet)()

    name = models.CharField(max_length=50)
    active = models.BooleanField(default=True, blank=True)

    #e.g. for Example Sentences for Japanese facts
    parent_fact_type = models.ForeignKey('self',
            blank=True, null=True, related_name='child_fact_types')
    many_children_per_fact = models.NullBooleanField(blank=True, null=True)


    #TODELETE
    # minimal interval multiplier between two cards of the same fact
    space_factor = models.FloatField(default=.1) 
    
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    modified_at = models.DateTimeField(auto_now=True, editable=False)
    
    def __unicode__(self):
        if self.parent_fact_type:
            return self.parent_fact_type.name + ' - ' + self.name
        return self.name
    
    class Meta:
        app_label = 'flashcards'




#class SubFact(Fact):
#    '''
#    Proxy model for subfacts (like example sentences).
#    '''
#    #TODO-OLD use this!

#    class Meta:
#        app_label = 'flashcards'
#        proxy = True


