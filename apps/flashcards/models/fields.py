from django.db import models
from django.contrib.auth.models import User
from django.forms import ModelForm
from django.forms.util import ErrorList
from dbtemplates.models import Template

from utils.templatetags.japanese import strip_ruby_bottom, strip_ruby_text

#from facts import Fact, FactType, SharedFact

import pickle

import flashcards.partsofspeech

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
    fact_type = models.ForeignKey('FactType')

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
    fact = models.ForeignKey('SharedFact', db_index=True)

    class Meta:
        #TODO unique_together = (('fact', 'field_type'), ) #one field content per field per fact
        app_label = 'flashcards'
    

class FieldContent(AbstractFieldContent):
    fact = models.ForeignKey('Fact', db_index=True)
    
    def save(self):
        # If this is a transliteration field,
        # update the transliteration cache.
        if self.field_type.is_transliteration_field_type():
            self.cached_transliteration_without_markup = self.strip_ruby_bottom()
        super(FieldContent, self).save()

    class Meta:
        #TODO unique_together = (('fact', 'field_type'), ) #one field content per field per fact
        app_label = 'flashcards'
        order_with_respect_to = 'field_type'



