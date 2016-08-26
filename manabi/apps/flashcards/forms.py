from django.db import models
from django.contrib.auth.models import User
from django import forms
from django.forms.util import ErrorList
from django.db.models.signals import post_save

# from manabi.apps import usertagging
# from manabi.apps.usertagging.forms import TagField


from models import Card, CardHistory, Fact, Deck

#Forms
#todo:row-level authentication (subclassing formset)



class CardForm(forms.ModelForm):
    class Meta:
        model = Card
        exclude = ('fact', 'ease_factor', )


class DeckForm(forms.ModelForm):
    #tags = usertagging.forms.TagField(required=False)

    def __init__(self, *args, **kwargs):
        super(DeckForm, self).__init__(*args, **kwargs)
        if 'id' in self.initial and self.initial['id']: #deck object already exists
            deck = Deck.objects.get(id=self.initial['id'])
            # self.initial['tags'] = usertagging.utils.edit_string_for_tags(deck.tags)

    def save(self, force_insert=False, force_update=False, commit=True):
        m = super(DeckForm, self).save(commit=False)
        # do custom stuff
        if commit:
            m.save()
            m.tags = self.cleaned_data['tags']
        return m

    class Meta:
        model = Deck
        fields = ('name','description',)
        #exclude = ('owner', 'description', 'priority', 'textbook_source',)


class TextbookSourceForm(forms.ModelForm):
    '''
    Used for setting the textbook source of a deck.
    '''
    class Meta:
        model = Deck
        fields = ('textbook_source',)


class FactForm(forms.ModelForm):
    tags = TagField(required=False)

    def save(self, force_insert=False, force_update=False, commit=True):
        m = super(FactForm, self).save(commit=False)
        # do custom stuff
        if commit:
            m.save()
            m.tags = self.cleaned_data['tags']
        return m

    class Meta:
        model = Fact
        exclude = ('active', 'synchronized_with', 'new_fact_ordinal', 'parent_fact', 'suspended',)
