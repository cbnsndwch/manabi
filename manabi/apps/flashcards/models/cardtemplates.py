from django.db import models
from django.db.models.query import QuerySet


class CardTemplateQuerySet(QuerySet):
    # Unfortunately hard-coded for now, since we have a ton of
    # extensability built into the system, but very little usage of it.
    @property
    def recognition(self):
        return self.get(name='Recognition')

    @property
    def production(self):
        return self.get(name='Production')

    @property
    def kanji_reading(self):
        return self.get(name='Kanji Reading')

    @property
    def kanji_writing(self):
        return self.get(name='Kanji Writing')


# TODO delete
class CardTemplate(models.Model):
    objects = CardTemplateQuerySet.as_manager()

    fact_type = models.ForeignKey('flashcards.FactType')

    name = models.CharField(max_length=50)
    description = models.TextField(max_length=200, blank=True)

    front_template_name = models.CharField(max_length=50)
    back_template_name = models.CharField(max_length=50) #TODO-OLD use a template marker for 'answer' fields to be typed in, optionally

    front_prompt = models.CharField(max_length=200, blank=True)
    back_prompt = models.CharField(max_length=200, blank=True)

    # Used to render card previews live -- a simplified version of the full templates
    # This is fed through dojo.string.substitute
    js_template = models.TextField(max_length=600, blank=True)

    #used for generating/enabling cards for a fact which is missing certain fields
    #can show validation errors to the user based on this (e.g. "Enter a reading if you want to do kanji writing")
    requisite_field_types = models.ManyToManyField('flashcards.FieldType',
        blank=True) #TODO-OLD implement

    #sometimes multiple cards should share intervals if they're similar enough.
    #use this group ID (not a foreignkey though) to synchronize among other cards within a fact.
    #this group is per fact type.
    card_synchronization_group = models.SmallIntegerField(blank=True, null=True)

    generate_by_default = models.BooleanField(default=True)
    ordinal = models.IntegerField(null=True, blank=True)
    hide_front = models.BooleanField(default=False, blank=True) #hide front when showing back
    allow_blank_back = models.BooleanField(default=True, blank=True) #don't activate cards with missing answers #TODO-OLD implement this
    active = models.BooleanField(default=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    modified_at = models.DateTimeField(auto_now=True, editable=False)

    def __unicode__(self):
        return self.name

    class Meta:
        app_label = 'flashcards'
        unique_together = (('name', 'fact_type'), ('ordinal', 'fact_type'), )
        ordering = ['ordinal']
