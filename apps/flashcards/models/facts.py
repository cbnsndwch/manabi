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
        shared_decks = decks.filter(synchronized_with__isnull=False)
        #shared_facts = self.filter(deck_id__in=shared_deck_ids)
        shared_facts = self.filter(deck__in=shared_decks)# should not be necessary.exclude(id__in=user_facts)
        return shared_facts | user_facts


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
        '''Returns a limited queryset of the new facts added, after adding them for the user.
        '''
        if deck:
            if not deck.synchronized_with:
                return self.none()
            decks = [deck]
        else:
            decks = Deck.objects.synchronized_decks(user)
        user_facts = self.filter(deck__owner=user, deck__in=decks)
        if tags:
            tagged_facts = usertagging.models.UserTaggedItem.objects.get_by_model(Fact, tags)
            user_facts = user_facts.filter(fact__in=tagged_facts)
        shared_deck_ids = [deck.synchronized_with_id for deck in decks if deck.synchronized_with_id]
        new_shared_facts = self.filter(deck_id__in=shared_deck_ids).exclude(id__in=user_facts)
        new_shared_facts = new_shared_facts.order_by('new_fact_ordinal')
        new_shared_facts = new_shared_facts[:count]
        #FIXME handle 0 ret
        
        # copy each fact
        for shared_fact in new_shared_facts:
            if shared_fact.parent_fact:
                #child fact
                fact = Fact(
                    fact_type_id=shared_fact.fact_type_id,
                    synchronized_with=shared_fact,
                    active=shared_fact.active) #TODO should it be here?
                fact.parent_fact = shared_fact_to_fact[shared_fact.parent_fact]
                fact.save()
            else:
                #regular fact
                fact = Fact(
                    deck=deck,
                    fact_type_id=shared_fact.fact_type_id,
                    synchronized_with=shared_fact,
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
        return new_shared_facts





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


    def save(self):
        if not self.new_fact_ordinal:
            self.new_fact_ordinal = random.randrange(0, MAX_NEW_CARD_ORDINAL)
        super(Fact, self).save()

    
    @transaction.commit_on_success    
    def delete(self):
        if self.subscriber_facts.exists():
            # if subscriber facts have reviewed or edited anything within this fact,
            # don't delete it for those subscribers.
            active_subscriber_cards = Card.objects.filter(
                    Q(active=True) & 
                    Q(suspended=False) & 
                    Q(last_reviewed_at__isnull=True)).values_list('fact_id', flat=True)


            updated_subscriber_fields = FieldContent.objects.filter(fact__in=self.subscriber_facts.filter()).distinct().values_list('fact_id', flat=True)

            active_subscriber_facts = self.subscriber_facts.filter(
                    Q(id__in=updated_subscriber_fields) |
                    Q(id__in=active_subscriber_cards))

            # de-synchronize the facts which users have updated or reviewed,
            # after making sure they contain the field contents.
            for fact in active_subscriber_facts:
                # unsynchronize each fact by copying field contents
                fact.copy_subscribed_field_contents()
            active_subscriber_facts.update(synchronized_with=None).save()

            other_subscriber_facts = self.subscriber_decks.exclude(id__in=active_subscriber_facts)
            other_subscriber_facts.delete()

            #Q(fact__in=self.subscriber_facts.filter(active=True)))
            #self.subscriber_facts.clear()
        super(Fact, self).delete()


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
            #TODO only override on a per-field basis when the user updates field contents
            if not len(field_contents):
                field_contents = self.synchronized_with.fieldcontent_set.all()
        return dict((field_content.field_type_id, field_content) for field_content in field_contents)


    @property
    def has_updated_content(self):
        '''Only call this for subscriber facts.
        Returns whether the subscriber user has edited any 
        field contents in this fact.
        '''
        if not self.synchronized_with:
            raise TypeError('This is not a subscriber fact.')
        return self.fieldcontent_set.all().exists()


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
            if not self.fieldcontent_set.filter(field_type=field_content.field_type).exists():
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
    
    def save(self):
        # If this is a transliteration field,
        # update the transliteration cache.
        if self.field_type.is_transliteration_field_type():
            self.cached_transliteration_without_markup = self.strip_ruby_bottom()
        super(FieldContent, self).save()

    class Meta:
        #TODO unique_together = (('fact', 'field_type'), ) #one field content per field per fact
        app_label = 'flashcards'


    def copy_to_fact(self, fact):
        '''Returns a new FieldContent copy which belongs 
        to the given fact.
        '''
        copy = FieldContent(
                fact=fact,
                field_type=self.field_type,
                media_uri=self.media_uri,
                media_file=self.media_file,
                cached_transliteration_without_markup=self.cached_transliteration_without_markup)
        copy.save()
        return copy





