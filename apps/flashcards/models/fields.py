from django.db import models
from django.contrib.auth.models import User
from django.forms import ModelForm
from django.forms.util import ErrorList
from dbtemplates.models import Template

from utils.templatetags.japanese import strip_ruby_bottom, strip_ruby_text

#from facts import Fact, FactType, SharedFact

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

    transliteration_field_type = models.OneToOneField('self', blank=True, null=True)
    
    #constraints
    unique = models.BooleanField(default=True)
    blank = models.BooleanField(default=False)
    editable = models.BooleanField(default=True)
    ordinal = models.IntegerField(null=True, blank=True)
    multi_line = models.BooleanField(default=True, blank=True)

    language = models.CharField(max_length=3, choices=ISO_639_2_LANGUAGES, blank=True, null=True)
    character_restriction = models.CharField(max_length=3, choices=OPTIONAL_CHARACTER_RESTRICTIONS, blank=True, null=True)
    
    accepts_media = models.BooleanField(default=False, blank=True) #TODO only allow media without any text, right?
    media_restriction = models.CharField(max_length=3, choices=OPTIONAL_MEDIA_TYPE_RESTRICTIONS, blank=True, null=True)

    hidden_when_editing = models.BooleanField(default=False) #hide this field when adding/editing a fact, unless the user wants to see extra, optional fields
    hidden_when_reviewing = models.BooleanField(default=False) #hide this field during review, click to see it (like extra notes maybe)

    active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    modified_at = models.DateTimeField(auto_now=True, editable=False)
    
    def __unicode__(self):
        return self.name
    
    class Meta:
        unique_together = (('name', 'fact_type'), ('ordinal', 'fact_type'), )
        app_label = 'flashcards'


class AbstractFieldContent(models.Model):
    field_type = models.ForeignKey(FieldType)

    content = models.CharField(max_length=1000, blank=True) #used as a description for media, too
    
    media_uri = models.URLField(blank=True)
    media_file = models.FileField(upload_to='/card_media/', null=True, blank=True) #TODO upload to user directory, using .storage

    def __unicode__(self):
        return self.content

    class Meta:
        app_label = 'flashcards'
        abstract = True


class SharedFieldContent(AbstractFieldContent):
    fact = models.ForeignKey('SharedFact')

    class Meta:
        #TODO unique_together = (('fact', 'field_type'), ) #one field content per field per fact
        app_label = 'flashcards'
    

class FieldContent(AbstractFieldContent):
    fact = models.ForeignKey('Fact')
    
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


    class Meta:
        #TODO unique_together = (('fact', 'field_type'), ) #one field content per field per fact
        app_label = 'flashcards'



