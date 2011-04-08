from apps.utils.templatetags.japanese import strip_ruby_bottom, strip_ruby_text
from constants import ISO_639_2_LANGUAGES
from django.db import models, transaction
import pickle


OPTIONAL_CHARACTER_RESTRICTIONS = (
    ('num','Numeric',),
    ('knj','Kanji',),
    ('kna','Kana',),
    ('hir','Hiragana',),
    ('kat','Katakana',),
)

OPTIONAL_MEDIA_TYPE_RESTRICTIONS = (
    ('img','Image'),
    ('vid','Video'),
    ('snd','Sound'),
)


class FieldType(models.Model):
    fact_type = models.ForeignKey('flashcards.FactType')

    # Used for referencing fields by name in code, instead of by id
    name = models.CharField(max_length=50, blank=False)

    display_name = models.CharField(max_length=50, blank=False)

    #fk to the FieldType which contains a transliteration of this FieldType
    transliteration_field_type = models.OneToOneField('self',
        blank=True, null=True,
        related_name='reverse_transliteration_field_type')
    
    #constraints
    unique = models.BooleanField(default=True)
    blank = models.BooleanField(default=False)
    editable = models.BooleanField(default=True)
    numeric = models.BooleanField(default=False)
    multi_line = models.BooleanField(default=True, blank=True)
    choices = models.CharField(blank=True, max_length=1000,
        help_text='Use a pickled choices tuple. The "none" value is used ' +
        'to indicate no selection, so don\'t use it in the choices tuple.')

    help_text = models.CharField(blank=True, max_length=500)

    language = models.CharField(
        max_length=3, choices=ISO_639_2_LANGUAGES, blank=True, null=True)

    character_restriction = models.CharField(
        max_length=3, choices=OPTIONAL_CHARACTER_RESTRICTIONS,
        blank=True, null=True)
    
    # only allow media without any text
    accepts_media = models.BooleanField(default=False, blank=True) 
    media_restriction = models.CharField(
        max_length=3, choices=OPTIONAL_MEDIA_TYPE_RESTRICTIONS,
        blank=True, null=True)

    # hide this field when adding/editing a fact, unless the user wants 
    # to see extra, optional fields
    hidden_in_form = models.BooleanField(default=False) 

    disabled_in_form = models.BooleanField(default=False,
        help_text='Disable this field when adding/editing a fact. ' +
                  'If hidden_in_form is also True, then it will supress ' +
                  'the Add `name` link in the form.')
    hidden_in_grid = models.BooleanField(default=False)
    grid_column_width = models.CharField(blank=True, max_length=10)
    #hidden_when_reviewing = models.BooleanField(default=False)
    #hide this field during review, click to see it (like extra notes maybe) 
    #handle in templates

    ordinal = models.IntegerField(null=True, blank=True)

    active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    modified_at = models.DateTimeField(auto_now=True, editable=False)
    
    def is_transliteration_field_type(self):
        '''
        Returns whether this field type is the transliteration of
        another field.
        '''
        try:
            self.fact_type.fieldtype_set.get(transliteration_field_type=self)
            return True
        except FieldType.DoesNotExist:
            return False

    @property
    def choices_as_tuple(self):
        # it gets stored as unicode, but this breaks unpickling
        return pickle.loads(str(self.choices)) 

    @choices_as_tuple.setter
    def choices_as_tuple(self, value):
        self.choices = pickle.dumps(value)

    def __unicode__(self):
        return self.fact_type.name + u': ' + self.name
    
    class Meta:
        unique_together = (('name', 'fact_type'),
                           ('ordinal', 'fact_type'),
                           ('display_name', 'fact_type'),)
        app_label = 'flashcards'



class FieldContent(models.Model):
    fact = models.ForeignKey('flashcards.Fact', db_index=True)
    field_type = models.ForeignKey(FieldType)

    # used as a description for media, too
    content = models.CharField(max_length=1000, blank=True) 
    
    media_uri = models.URLField(blank=True)
    #TODO upload to user directory, using .storage
    media_file = models.FileField(
        upload_to='/card_media/', null=True, blank=True) 

    # if this Field is a transliteration, then we will cache the 
    # non-marked up transliteration
    # for example, for '<TA|ta>beru', we will cache 'taberu' in this field.
    cached_transliteration_without_markup = models.CharField(
        max_length=1000, blank=True)


    @property
    def transliteration_field_content(self):
        '''
        Returns the transliteration field for this field.
        If one doesn't exist, returns None.
        '''
        # This field is supposed to have a matching transliteration field.
        if self.field_type.transliteration_field_type:
            try:
                return self.fact.fieldcontent_set.get(
                    field_type=self.field_type.transliteration_field_type)
            except self.DoesNotExist:
                return None

    @property
    def reverse_transliteration_field_content(self):
        '''
        Returns the field which this field is the transliteration of.
        If one doesn't exist, returns None.
        '''
        try:
            return self.fact.fieldcontent_set.get(
                field_type=self.field_type)
        except self.DoesNotExist:
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
        return self.content
            
    def strip_ruby_text(self):
        '''
        Returns this field's content with any ruby text removed.
        <TA|ta>beru becomes TAberu
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
        if self.transliteration_field_content:
            return self.content.strip() == \
                self.transliteration_field_content.\
                strip_ruby_text().strip()
        return False

    def kanji_list(self):
        '''
        Returns a list of each individual kanji in this field (if any).
        '''
        from apps.utils.unicodeblocks import block, KANJI_BLOCKS
        return [char for char in self.content \
                if block(char) in KANJI_BLOCKS]

    def __unicode__(self):
        return self.content
    
    def save(self, *args, **kwargs):
        # If this is a transliteration field,
        # update the transliteration cache.
        if self.field_type.is_transliteration_field_type():
            self.cached_transliteration_without_markup = \
                self.strip_ruby_bottom()
        super(FieldContent, self).save(*args, **kwargs)

    class Meta:
        #TODO unique_together = (('fact', 'field_type'), )
        # one field content per field per fact
        app_label = 'flashcards'


    def copy_to_fact(self, fact):
        '''
        Returns a new FieldContent copy which belongs 
        to the given fact.
        Returns None if a corresponding FieldContent already exists.
        '''
        #TODO use meta fields instead
        if fact.fieldcontent_set.filter(field_type=self.field_type):
            return None
        copy = FieldContent(
                fact=fact,
                content=self.content,
                field_type=self.field_type,
                media_uri=self.media_uri,
                media_file=self.media_file,
                cached_transliteration_without_markup=\
                    self.cached_transliteration_without_markup)
        copy.save()
        return copy

