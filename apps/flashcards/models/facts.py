from django.db import models
from django.contrib.auth.models import User
from django.forms import ModelForm
from django.forms.util import ErrorList
from dbtemplates.models import Template
from django.db.models import Q

#from fields import FieldContent
from constants import MAX_NEW_CARD_ORDINAL
#from decks import Deck
#import fields
import random
#from decks import Deck, SharedDeck
#import Deck
import usertagging
from django.db import transaction

from utils.templatetags.japanese import strip_ruby_bottom, strip_ruby_text
import pickle
import flashcards.partsofspeech

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
    
    
    def get_for_owner_or_subscriber(self, fact_id, user):
        '''Returns a Fact object of the given id,
        or if the user is a subscriber to the deck of that fact,
        returns the subscriber's copy of that fact, which it 
        creates if necessary.
        It will also create the associated cards.
        '''
        fact = Fact.objects.get(id=fact_id)
        if fact.owner != user:
            if not fact.deck.shared_at:
                pass #FIXME raise permissions error
            else:
                from decks import Deck
                # find the subscriber deck for this user
                subscriber_deck = Deck.objects.get(owner=user, synchronized_with=fact.deck)

                # check if the fact exists already
                existent_fact = subscriber_deck.fact_set.filter(synchronized_with=fact)
                if existent_fact:
                    fact = existent_fact[0]
                else:
                    fact = fact.copy_to_deck(subscriber_deck, synchronize=True)
        return fact


    def with_synchronized(self, user, deck=None, tags=None):
        '''Returns a queryset of all Facts which the user owns, or which 
        the user is subscribed to (via a subscribed deck).
        Optionally filter by deck and tags too.
        '''
        from decks import Deck
        user_facts = self.filter(deck__owner=user)

        if deck:
            #if not deck.synchronized_with:
            #    return self.none()
            decks = Deck.objects.filter(id=deck.id)
            user_facts = user_facts.filter(deck__in=decks)
        else:
            decks = Deck.objects.filter(owner=user, active=True)
        if tags:
            tagged_facts = usertagging.models.UserTaggedItem.objects.get_by_model(Fact, tags)
            user_facts = user_facts.filter(fact__in=tagged_facts)
        subscriber_decks = decks.filter(synchronized_with__isnull=False)
        subscribed_decks = [deck.synchronized_with for deck in subscriber_decks]
        #shared_facts = self.filter(deck_id__in=shared_deck_ids)
        copied_subscribed_fact_ids = [fact.synchronized_with_id for fact in user_facts]
        subscribed_facts = self.filter(deck__in=subscribed_decks).exclude(id__in=copied_subscribed_fact_ids) # should not be necessary.exclude(id__in=user_facts)
        return user_facts | subscribed_facts


    def search(self, fact_type, query, query_set=None):
        '''Returns facts which have FieldContents containing the query.
        `query` is a substring to match on
        '''
        #TODO or is in_bulk() faster?
        query = query.strip()
        if not query_set:
            query_set = self.all()

        subscriber_facts = Fact.objects.filter(synchronized_with__in=query_set)

        matches = FieldContent.objects.filter(
                Q(content__icontains=query)
                | Q(cached_transliteration_without_markup__icontains=query)
                & (Q(fact__in=query_set) | Q(fact__synchronized_with__in=subscriber_facts)))
                #& Q(fact__fact_type=fact_type)).all()

        #TODO use values_list to be faster
        match_ids = matches.values_list('fact', flat=True)
        return query_set.filter(Q(id__in=match_ids) | Q(synchronized_with__in=match_ids))
        #return query_set.filter(id__in=set(field_content.fact_id for field_content in matches))


    @transaction.commit_on_success    
    def add_new_facts_from_synchronized_decks(self, user, count, deck=None, tags=None):
        '''Returns a limited queryset of the new facts added, after adding them for the user.
        '''
        from cards import Card
        from decks import Deck
        if deck:
            if not deck.synchronized_with:
                return self.none()
            decks = Deck.objects.filter(id=deck.id)
        else:
            decks = Deck.objects.synchronized_decks(user)
        user_facts = self.filter(deck__owner=user, deck__in=decks)
        if tags:
            tagged_facts = usertagging.models.UserTaggedItem.objects.get_by_model(Fact, tags)
            user_facts = user_facts.filter(fact__in=tagged_facts)
        #shared_deck_ids = [deck.synchronized_with_id for deck in decks if deck.synchronized_with_id]
        new_shared_facts = self.filter(deck__in=decks.filter(synchronized_with__isnull=False)).exclude(id__in=user_facts)
        new_shared_facts = new_shared_facts.order_by('new_fact_ordinal')
        new_shared_facts = new_shared_facts[:count]
        #FIXME handle 0 ret
        
        # copy each fact
        for shared_fact in new_shared_facts:
            shared_fact.copy_to_deck(deck, synchronize=True)

        return new_shared_facts





#TODO citation/fact source class


class AbstractFact(models.Model):
    fact_type = models.ForeignKey(FactType)
    
    active = models.BooleanField(default=True, blank=True)
    #suspended = models.BooleanField(default=False, blank=True)
    priority = models.IntegerField(default=0, null=True, blank=True) #TODO how to reconcile with card priorities?
    notes = models.CharField(max_length=1000, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    modified_at = models.DateTimeField(auto_now=True, editable=False)


    class Meta:
        app_label = 'flashcards'
        abstract = True



class SharedFact(AbstractFact):
    deck = models.ForeignKey('flashcards.SharedDeck', blank=True, null=True, db_index=True)
    
    #child facts (e.g. example sentences for a Japanese fact)
    parent_fact = models.ForeignKey('self', blank=True, null=True, related_name='child_facts')

    class Meta:
        app_label = 'flashcards'

usertagging.register(SharedFact)



class Fact(AbstractFact):
    objects = FactManager()
    deck = models.ForeignKey('flashcards.Deck', blank=True, null=True, db_index=True)
    synchronized_with = models.ForeignKey('self', null=True, blank=True, related_name='subscriber_facts')
    new_fact_ordinal = models.PositiveIntegerField(null=True, blank=True)

    #child facts (e.g. example sentences for a Japanese fact)
    parent_fact = models.ForeignKey('self', blank=True, null=True, related_name='child_facts')


    def save(self, *args, **kwargs):
        if not self.new_fact_ordinal:
            self.new_fact_ordinal = random.randrange(0, MAX_NEW_CARD_ORDINAL)
        super(Fact, self).save(*args, **kwargs)

    
    @transaction.commit_on_success
    def delete(self, *args, **kwargs):
        if self.deck.shared_at and self.subscriber_facts.all():
            # don't bother with users who don't have this fact yet - we can safely (according to guidelines) delete at this point.
            # if subscriber facts have reviewed or edited anything within this fact,
            # don't delete it for those subscribers.
            from cards import Card

            # get active subscriber facts
            active_cards = Card.objects.filter(fact__in=self.subscriber_facts.all(), active=True, suspended=False, last_reviewed_at__isnull=False)

            updated_fields = FieldContent.objects.filter(fact__in=self.subscriber_facts.all())

            active_subscribers = self.subscriber_facts.filter(
                    Q(id__in=active_cards.values_list('fact_id', flat=True)) |
                    Q(id__in=updated_fields.values_list('fact_id', flat=True)))

            # de-synchronize the facts which users have updated or reviewed,
            # after making sure they contain the field contents.
            for fact in active_subscribers.iterator():
                # unsynchronize each fact by copying field contents
                fact.copy_subscribed_field_contents()
                fact.synchronized_with = None
                fact.save()

            other_subscriber_facts = self.subscriber_facts.exclude(id__in=active_subscribers)
            other_subscriber_facts.delete()
        super(Fact, self).delete(*args, **kwargs)


    @property
    def owner(self):
        return self.deck.owner




    @property
    def field_contents(self):
        '''Returns a queryset of field contents for this fact. #dict of {field_type_id: field_content}
        '''
        fact = self
        field_contents = self.fieldcontent_set.all().order_by('field_type__ordinal')
        if self.synchronized_with:
            # first see if the user has updated this fact's contents.
            # this would override the synced fact's.
            #TODO only override on a per-field basis when the user updates field contents
            if not len(field_contents):
                field_contents = self.synchronized_with.fieldcontent_set.all().order_by('field_type__ordinal')
        #return dict((field_content.field_type_id, field_content) for field_content in field_contents)
        return field_contents


    @property
    def has_updated_content(self):
        '''Only call this for subscriber facts.
        Returns whether the subscriber user has edited any 
        field contents in this fact.
        '''
        if not self.synchronized_with:
            raise TypeError('This is not a subscriber fact.')
        return self.fieldcontent_set.all().counter() > 0 #.exists()


    @transaction.commit_on_success
    def copy_subscribed_field_contents(self):
        '''Only call this for subscriber facts.
        Copies all the field contents for the synchronized fact,
        so that it will not longer receive updates to field 
        contents when the subscribed fact is updated. (including deletes)
        Effectively unsubscribes just for this fact.
        '''
        if not self.synchronized_with:
            raise TypeError('This is not a subscriber fact.')
        for field_content in self.synchronized_with.fieldcontent_set.all():
            # copy if it doesn't already exist
            if not self.fieldcontent_set.filter(field_type=field_content.field_type):
                field_content.copy_to_fact(self)


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
    def copy_to_deck(self, deck, copy_field_contents=False, synchronize=False):
        '''Creates a copy of this fact and its cards and (optionally, if `synchronize` is False) field contents.
        If `synchronize` is True, the new fact will be subscribed to this one.
        Also copies its tags.
        Returns the newly copied fact.
        '''
        copy = Fact(deck=deck, fact_type=self.fact_type, active=self.active, notes=self.notes, new_fact_ordinal=self.new_fact_ordinal)
        if synchronize:
            if self.synchronized_with:
                raise TypeError('Cannot synchronize with a fact that is already a synschronized fact.')
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

        return copy


    class Meta:
        app_label = 'flashcards'
        unique_together = (('deck', 'synchronized_with'),)


    def __unicode__(self):
        field_content_contents = []
        for field_content in self.fieldcontent_set.all():
            field_content_contents.append(field_content.content)
        return u' - '.join(field_content_contents)

usertagging.register(Fact)




# formerly fields.py
OPTIONAL_CHARACTER_RESTRICTIONS = (
    ('num','Numeric',),
    ('knj','Kanji',),
    ('kna','Kana',),
    ('hir','Hiragana',),
    ('kat','Katakana',),
)

#FIXME grab from some other backup
ISO_639_2_LANGUAGES = (
    ('eng','English',),
    ('jpn','Japanese',),
)

OPTIONAL_MEDIA_TYPE_RESTRICTIONS = (
    ('img','Image'),
    ('vid','Video'),
    ('snd','Sound'),
)


class FieldType(models.Model):
    name = models.CharField(max_length=50)
    fact_type = models.ForeignKey('flashcards.FactType')

    #fk to the FieldType which contains a transliteration of this FieldType
    transliteration_field_type = models.OneToOneField('self', blank=True, null=True)
    
    #constraints
    unique = models.BooleanField(default=True)
    blank = models.BooleanField(default=False)
    editable = models.BooleanField(default=True)
    numeric = models.BooleanField(default=False)
    multi_line = models.BooleanField(default=True, blank=True)
    choices = models.CharField(blank=True, max_length=1000, help_text='Use a pickled choices tuple. The "none" value is used to indicate no selection, so don\'t use it in the choices tuple.')

    help_text = models.CharField(blank=True, max_length=500)

    language = models.CharField(max_length=3, choices=ISO_639_2_LANGUAGES, blank=True, null=True)
    character_restriction = models.CharField(max_length=3, choices=OPTIONAL_CHARACTER_RESTRICTIONS, blank=True, null=True)
    
    accepts_media = models.BooleanField(default=False, blank=True) # only allow media without any text
    media_restriction = models.CharField(max_length=3, choices=OPTIONAL_MEDIA_TYPE_RESTRICTIONS, blank=True, null=True)

    hidden_in_form = models.BooleanField(default=False) #hide this field when adding/editing a fact, unless the user wants to see extra, optional fields
    disabled_in_form = models.BooleanField(default=False, help_text="Disable this field when adding/editing a fact. If hidden_in_form is also True, then it will supress the Add `name` link in the form.")
    hidden_in_grid = models.BooleanField(default=False)
    grid_column_width = models.CharField(blank=True, max_length=10)
    #hidden_when_reviewing = models.BooleanField(default=False) #hide this field during review, click to see it (like extra notes maybe) #handle in templates

    ordinal = models.IntegerField(null=True, blank=True)

    active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    modified_at = models.DateTimeField(auto_now=True, editable=False)
    
    def is_transliteration_field_type(self):
        '''Returns whether this field type is the transliteration of another field.'''
        try:
            self.fact_type.fieldtype_set.get(transliteration_field_type=self)
            return True
        except FieldType.DoesNotExist:
            return False

    @property
    def choices_as_tuple(self):
        return pickle.loads(str(self.choices)) #it gets stored as unicode, but this breaks unpickling

    @choices_as_tuple.setter
    def choices_as_tuple(self, value):
        self.choices = pickle.dumps(value)


    def __unicode__(self):
        return self.fact_type.name + ': ' + self.name
    
    class Meta:
        unique_together = (('name', 'fact_type'), ('ordinal', 'fact_type'), )
        app_label = 'flashcards'


class AbstractFieldContent(models.Model):
    field_type = models.ForeignKey(FieldType)

    content = models.CharField(max_length=1000, blank=True) #used as a description for media, too
    
    media_uri = models.URLField(blank=True)
    media_file = models.FileField(upload_to='/card_media/', null=True, blank=True) #TODO upload to user directory, using .storage

    #if this Field is a transliteration, then we will cache the non-marked up transliteration
    #for example, for '<TA|ta>beru', we will cache 'taberu' in this field.
    cached_transliteration_without_markup = models.CharField(max_length=1000, blank=True)


    @property
    def transliteration_field_content(self):
        '''
        Returns the transliteration field for this field.
        If one doesn't exist, returns None.
        '''
        if self.field_type.transliteration_field_type:
            #this field is supposed to have a matching transliteration field
            try:
                return self.fact.fieldcontent_set.get(field_type=self.field_type.transliteration_field_type)
            except self.DoesNotExist:
                return None
        else:
            return None

    @property
    def human_readable_content(self):
        '''
        Returns content, but if this is a multi-choice field, 
        returns the name of the choice rather than its value.

        If this is a transliteration field, this returns 
        the transliteration with the bottom part of any 
        ruby text removed.
        '''
        if self.field_type.choices:
            choices = dict(self.field_type.choices_as_tuple)
            return choices.get(self.content) or ''
        elif self.field_type.is_transliteration_field_type:
            return self.strip_ruby_bottom()
        else:
            return self.content
            
    def strip_ruby_text(self):
        '''
        Returns this field's content with any ruby text removed.
        <ta|ta>beru becomes taberu
        '''
        return strip_ruby_text(self.content)

    def strip_ruby_bottom(self):
        '''
        Returns this field's content, with just the ruby text instead of
        what's beneath it, and the other text.
        <TA|ta>beru becomes taberu
        '''
        return strip_ruby_bottom(self.content)


    def has_identical_transliteration_field(self):
        '''
        Returns True if the corresponding transliteration field is 
        identical, once any ruby text markup is removed.
        '''
        return self.content.strip() == self.transliteration_field_content.strip_ruby_text().strip()

    def __unicode__(self):
        return self.content

    class Meta:
        app_label = 'flashcards'
        abstract = True


class SharedFieldContent(AbstractFieldContent):
    fact = models.ForeignKey('flashcards.SharedFact', db_index=True)

    class Meta:
        #TODO unique_together = (('fact', 'field_type'), ) #one field content per field per fact
        app_label = 'flashcards'
    

class FieldContent(AbstractFieldContent):
    fact = models.ForeignKey('flashcards.Fact', db_index=True)
    
    def save(self, *args, **kwargs):
        # If this is a transliteration field,
        # update the transliteration cache.
        if self.field_type.is_transliteration_field_type():
            self.cached_transliteration_without_markup = self.strip_ruby_bottom()
        super(FieldContent, self).save(*args, **kwargs)

    class Meta:
        #TODO unique_together = (('fact', 'field_type'), ) #one field content per field per fact
        app_label = 'flashcards'


    def copy_to_fact(self, fact):
        '''Returns a new FieldContent copy which belongs 
        to the given fact.
        '''
        #TODO use meta fields instead
        copy = FieldContent(
                fact=fact,
                content=self.content,
                field_type=self.field_type,
                media_uri=self.media_uri,
                media_file=self.media_file,
                cached_transliteration_without_markup=self.cached_transliteration_without_markup)
        copy.save()
        return copy



