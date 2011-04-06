from constants import MAX_NEW_CARD_ORDINAL
from dbtemplates.models import Template
from django.contrib.auth.models import User
from django.db import models, transaction
from django.db.models import Q
from django.forms import ModelForm
from django.forms.util import ErrorList
import flashcards.partsofspeech
import pickle
import random
import usertagging
from fields import FieldContent


def seconds_to_days(s):
    return s / 86400.0


class FactType(models.Model):
    name = models.CharField(max_length=50)
    active = models.BooleanField(default=True, blank=True)

    #e.g. for Example Sentences for Japanese facts
    parent_fact_type = models.ForeignKey('self',
        blank=True, null=True, related_name='child_fact_types')
    many_children_per_fact = models.NullBooleanField(blank=True, null=True)

    # separate the cards of this fact initially
    # not used for child fact types (?)
    min_card_space = models.FloatField(default=seconds_to_days(600),
        help_text="Duration expressed in (partial) days.")

    # minimal interval multiplier between two cards of the same fact
    space_factor = models.FloatField(default=.1) 
    
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    modified_at = models.DateTimeField(auto_now=True, editable=False)
    
    def __unicode__(self):
        if self.parent_fact_type:
            return self.parent_fact_type.name + ' - ' + self.name
        return self.name
    
    class Meta:
        #unique_together = (('owner', 'name'), )
        app_label = 'flashcards'



class FactManager(models.Manager):
    #TODO move to User
    def all_tags_per_user(self, user):
        '''
        Includes tags on facts made on subscribed facts.
        '''
        #user_facts = self.filter(deck__owner=user) 
        user_facts = self.with_upstream(user)
        return usertagging.models.Tag.objects.usage_for_queryset(
            user_facts)
    
    def search(self, fact_type, query, query_set=None):
        '''Returns facts which have FieldContents containing the query.
        `query` is a substring to match on
        '''
        #TODO or is in_bulk() faster?
        query = query.strip()
        if not query_set:
            query_set = self.filter(parent_fact__isnull=True) #all()

        subscriber_facts = Fact.objects.filter(synchronized_with__in=query_set)

        matches = FieldContent.objects.filter(
                Q(content__icontains=query)
                | Q(cached_transliteration_without_markup__icontains=query)
                & (Q(fact__in=query_set)
                   | Q(fact__synchronized_with__in=subscriber_facts)))
                #& Q(fact__fact_type=fact_type)).all()

        #TODO use values_list to be faster
        match_ids = matches.values_list('fact', flat=True)
        return query_set.filter(Q(id__in=match_ids) |
                                Q(synchronized_with__in=match_ids))
        #return query_set.filter(id__in=set(field_content.fact_id 
        #for field_content in matches))

    def get_for_owner_or_subscriber(self, fact_id, user):
        '''
        Returns a Fact object of the given id,
        or if the user is a subscriber to the deck of that fact,
        returns the subscriber's copy of that fact, which it 
        creates if necessary.
        It will also create the associated cards.
        '''
        fact = Fact.objects.get(id=fact_id)
        if fact.owner != user:
            if False: #FIXME sometimes fact.parent_fact not fact.deck.shared_at:
                pass #FIXME raise permissions error
            else:
                from decks import Deck
                # find the subscriber deck for this user
                try:
                    subscriber_deck = Deck.objects.get(owner=user, synchronized_with=fact.deck)
                except Deck.DoesNotExist:
                    raise forms.ValidationError(
                            'You do not have permission to access this flashcard deck.')

                # check if the fact exists already
                existent_fact = subscriber_deck.fact_set.filter(synchronized_with=fact)
                if existent_fact:
                    fact = existent_fact[0]
                else:
                    fact = fact.copy_to_deck(subscriber_deck, synchronize=True)
        return fact


    def with_upstream(self, user, deck=None, tags=None):
        '''
        Returns a queryset of all active Facts which the user owns, or which 
        the user is subscribed to (via a subscribed deck).
        Optionally filter by deck and tags too.
        '''
        from decks import Deck
        user_facts = self.filter(deck__owner=user, parent_fact__isnull=True)
        
        if deck:
            decks = Deck.objects.filter(id=deck.id)
            user_facts = user_facts.filter(deck__in=decks)
        else:
            decks = Deck.objects.filter(owner=user, active=True)
        if tags:
            tagged_facts = usertagging.models.UserTaggedItem.objects.get_by_model(Fact, tags)
            user_facts = user_facts.filter(id__in=tagged_facts)

        subscriber_decks = decks.filter(synchronized_with__isnull=False)
        subscribed_decks = [deck.synchronized_with for deck in subscriber_decks if deck.synchronized_with is not None]
        #shared_facts = self.filter(deck_id__in=shared_deck_ids)
        copied_subscribed_fact_ids = [fact.synchronized_with_id for fact in user_facts if fact.synchronized_with_id is not None]
        subscribed_facts = self.filter(deck__in=subscribed_decks).exclude(id__in=copied_subscribed_fact_ids) # should not be necessary.exclude(id__in=user_facts)
        return user_facts | subscribed_facts

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
            tagged_facts = usertagging.models.UserTaggedItem.objects.get_by_model(Fact, tags)
            user_facts = user_facts.filter(fact__in=tagged_facts)

        #shared_deck_ids = [deck.synchronized_with_id for deck in decks if deck.synchronized_with_id]
        new_shared_facts = self.filter(active=True, deck__in=decks.filter(synchronized_with__isnull=False)).exclude(id__in=user_facts)
        new_shared_facts = new_shared_facts.order_by('new_fact_ordinal')
        new_shared_facts = new_shared_facts[:count]
        #FIXME handle 0 ret
        
        # copy each fact
        for shared_fact in new_shared_facts:
            shared_fact.copy_to_deck(deck, synchronize=True)

        return new_shared_facts







class Fact(models.Model):
    objects = FactManager()
    deck = models.ForeignKey('flashcards.Deck',
        blank=True, null=True, db_index=True)
    synchronized_with = models.ForeignKey('self',
        null=True, blank=True, related_name='subscriber_facts')
    new_fact_ordinal = models.PositiveIntegerField(null=True, blank=True)

    fact_type = models.ForeignKey(FactType)
    
    active = models.BooleanField(default=True, blank=True)
    #suspended = models.BooleanField(default=False, blank=True)
    priority = models.IntegerField(default=0, null=True, blank=True)
    #TODO how to reconcile with card priorities?

    notes = models.CharField(max_length=1000, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    modified_at = models.DateTimeField(auto_now=True, editable=False)

    #child facts (e.g. example sentences for a Japanese fact)
    parent_fact = models.ForeignKey('self',
        blank=True, null=True, related_name='child_facts')


    def save(self, *args, **kwargs):
        '''
        Set a random sorting index for new cards.
        '''
        if not self.new_fact_ordinal:
            self.new_fact_ordinal = random.randrange(
                0, MAX_NEW_CARD_ORDINAL)
        super(Fact, self).save(*args, **kwargs)

    
    @transaction.commit_on_success
    def delete(self, *args, **kwargs):
        deck = self.parent_fact.deck if self.parent_fact else self.deck
        # don't necessarily delete for any subscribers of this fact
        if self.subscriber_facts.all():
            # don't bother with users who don't have this fact yet - we can safely (according to guidelines) delete at this point.
            # if subscriber facts have reviewed or edited anything within this fact,
            # don't delete it for those subscribers.
            from cards import Card

            # get active subscriber facts
            active_cards = Card.objects.filter(fact__in=self.subscriber_facts.all(), active=True, suspended=False, last_reviewed_at__isnull=False)

            updated_fields = FieldContent.objects.filter(fact__in=self.subscriber_facts.all())# | \
            #FieldContent.objects.filter(fact__parent_fact__in=self.subscriber_facts.all())

            updated_subfacts = Fact.objects.filter(
                    id__in=FieldContent.objects.filter(
                        fact__parent_fact__in=self.subscriber_facts.all()).values_list('fact_id', flat=True))

            active_subscribers = self.subscriber_facts.filter(
                    #Q(id__in=updated_fields.values_list('parent_fact_id', flat=True)) |
                    Q(id__in=updated_subfacts.values_list('parent_fact_id', flat=True)) |
                    Q(id__in=active_cards.values_list('fact_id', flat=True)) |
                    Q(id__in=updated_fields.values_list('fact_id', flat=True)))

            # de-synchronize the facts which users have updated or reviewed,
            # after making sure they contain the field contents.
            for fact in active_subscribers.iterator():
                # unsynchronize each fact by copying field contents
                fact.copy_subscribed_field_contents_and_subfacts()
                fact.synchronized_with = None
                for subfact in fact.child_facts.all():
                    subfact.synchronized_with = None
                    subfact.save()
                fact.save()

            other_subscriber_facts = self.subscriber_facts.exclude(id__in=active_subscribers)
            other_subscriber_facts.delete()
        super(Fact, self).delete(*args, **kwargs)

    @property
    def owner(self):
        if self.parent_fact:
            return self.parent_fact.deck.owner
        return self.deck.owner

    @property
    def subfacts(self):
        '''
        Returns subfacts (via the child_facts relation) of this fact.
        Includes subfacts of the subscribed fact if this is synchronized 
        with a shared deck.

        Only includes active subfacts.
        '''
        subfacts = self.child_facts.all()
        if self.synchronized_with:
            synchronized_subfacts = self.synchronized_with.child_facts
            subfacts = subfacts | synchronized_subfacts.exclude(id__in=subfacts.exclude(synchronized_with__isnull=True).values_list('synchronized_with_id', flat=True))
        return subfacts.filter(active=True)


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
            #TODO only override on a per-field basis when the 
            #user updates field contents
            if not field_contents:
                field_contents = self.synchronized_with.fieldcontent_set.all().order_by('field_type__ordinal')
        #return dict((field_content.field_type_id, field_content) for field_content in field_contents)
        return field_contents

    def suspend(self):
        for card in fact.card_set.all():
            card.suspended = True
            card.save()
        
    def unsuspend(self):
        for card in fact.card_set.all():
            card.suspended = False
            card.save()

    def has_updated_content(self):
        '''Only call this for subscriber facts.
        Returns whether the subscriber user has edited any 
        field contents in this fact.
        '''
        if not self.synchronized_with:
            raise TypeError('This is not a subscriber fact.')
        return self.fieldcontent_set.all().counter() > 0 #.exists()

    @transaction.commit_on_success
    def copy_subscribed_field_contents_and_subfacts(self):
        '''
        Only call this for subscriber facts.
        Copies all the field contents for the synchronized fact,
        so that it will not longer receive updates to field 
        contents when the subscribed fact is updated. (including deletes)
        Also copies any subfacts, and their field contents.
        Effectively unsubscribes just for this fact.
        '''
        if not self.synchronized_with:
            raise TypeError('This is not a subscriber fact.')
        #elif self.parent_fact:
            #raise TypeError('This must be called on parent facts, not subfacts.')
        for field_content in self.synchronized_with.fieldcontent_set.all():
            # copy if it doesn't already exist
            if not self.fieldcontent_set.filter(field_type=field_content.field_type):
                field_content.copy_to_fact(self)
        if not self.parent_fact:
            for subfact in self.synchronized_with.child_facts.all():
                # copy (if it doesn't already exist - but that's handled by the copy method)
                subfact.copy_to_parent_fact(self, copy_field_contents=True)


    def fieldcontent_set_plus_blank_fields(self):
        '''
        Returns self.fieldcontent_set, but adds mock 
        FieldContent objects for any FieldTypes of this 
        fact's FactType which do not have corresponding 
        FieldContent objects.
        (e.g. a fact without a notes field, so that 
        the notes field can be included in an update form.)
        '''
        pass
        #field_contents = self.fieldcontent_set.all()
        #TODO add this


    @transaction.commit_on_success
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


    @transaction.commit_on_success
    def copy_to_deck(self, deck, copy_field_contents=False, copy_subfacts=False, synchronize=False):
        '''Creates a copy of this fact and its cards and (optionally, if `synchronize` is False) field contents.
        If `synchronize` is True, the new fact will be subscribed to this one.
        Also copies its tags.
        Returns the newly copied fact.
        '''
        if self.parent_fact:
            raise TypeError('Cannot call this on a subfact.')
        copy = Fact(deck=deck, fact_type=self.fact_type, active=self.active, notes=self.notes, new_fact_ordinal=self.new_fact_ordinal)
        if synchronize:
            if self.synchronized_with:
                raise TypeError('Cannot synchronize with a fact that is already a synchronized fact.')
            elif not self.deck.shared_at:
                raise TypeError('This is not a shared fact - cannot synchronize with it.')
            #TODO enforce deck synchronicity too
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
            card = Card(
                    fact=copy,
                    template_id=shared_card.template_id,
                    priority=shared_card.priority,
                    leech=False,
                    active=True,
                    suspended=shared_card.suspended,
                    new_card_ordinal=shared_card.new_card_ordinal)
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





class SubFact(Fact):
    '''
    Proxy model for subfacts (like example sentences).
    '''
    #TODO use this!

    class Meta:
        app_label = 'flashcards'
        proxy = True


