from django.db import models
from django.contrib.auth.models import User
from django import forms
from django.forms.util import ErrorList
from dbtemplates.models import Template
from django.db.models.signals import post_save  

import usertagging


from models import Card, CardHistory, Fact, FactType, FieldType, FieldContent, Deck, CardTemplate

#Forms
#todo:row-level authentication (subclassing formset)



class CardForm(forms.ModelForm):
    class Meta:
        model = Card
        exclude = ('fact', 'ease_factor', )
        

class DeckForm(forms.ModelForm):
    tags = usertagging.forms.TagField(required=False)

    def __init__(self, *args, **kwargs):
        super(DeckForm, self).__init__(*args, **kwargs)
        if 'id' in self.initial and self.initial['id']: #deck object already exists
            deck = Deck.objects.get(id=self.initial['id'])
            self.initial['tags'] = usertagging.utils.edit_string_for_tags(deck.tags)
    
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
        #exclude = ('owner', 'description', 'priority', 'textbook_source', 'picture',)
        


class SubfactForm(forms.ModelForm):

    class Meta:
        model = Fact
        exclude = ('active', 'synchronized_with', 'new_fact_ordinal', 'parent_fact', 'suspended',)


class FactTypeForm(forms.ModelForm):
    class Meta:
        model = FactType


class CardTemplateForm(forms.ModelForm):
    class Meta:
        model = CardTemplate
        

class FactForm(forms.ModelForm):
    tags = usertagging.forms.TagField(required=False)

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


class FieldContentForm(forms.ModelForm):
    subfact_group = forms.IntegerField(required=False)

    def clean(self): #TODO if any(self.errors):return NO:thats just for formsets
        cleaned_data = self.cleaned_data
        content = cleaned_data.get('content') or ''
        field_type = cleaned_data.get('field_type')#FieldType.objects.get(id=field_type_id)
        blank = field_type.blank
        unique = field_type.unique
        error_list = []

        if field_type.choices:
            if content == 'none':
                #'none' indicates no selection for choice fields
                content = ''
                cleaned_data['content'] = ''
        if not field_type.multi_line and '\n' in content:
            msg = u'This is a single-line field.'
            error_list.append(msg)
            if 'content' in cleaned_data:
              del cleaned_data['content'] #TODO why do I do this?
        if not blank and not content.strip():
            msg = u'This field is required.'
            #self._errors['content'] = ErrorList([msg])
            error_list.append(msg)
            if 'content' in cleaned_data:
                del cleaned_data['content']
        elif field_type: #TODO why check if field_type?
            if content.strip(): #if it's blank, don't bother checking if it's unique
                if unique: #TODO can a field be blank and unique? probably yes, since blank is like null
                    #dirty hack to get this deck's owner
                    if 'fact-deck' in self.data:
                        deck_id = self.data['fact-deck']
                    elif 'fact-0-deck' in self.data:
                        deck_id = self.data['fact-0-deck']
                    else:
                        msg = u'Corresponding deck not found.'
                        error_list.append(msg)
                    other_field_contents = FieldContent.objects.filter(field_type=field_type, content__exact=content, fact__deck=deck_id)
                    if cleaned_data.get('id'): #exclude the existing field content if this is an update
                        #this is an update form (the FieldContent object already exists)
                        other_field_contents = other_field_contents.exclude(id=cleaned_data.get('id').id)
                        #owner = cleaned_data.get('id').fact.deck.owner #get('id') returns this FieldContent model instance, strangely enough
                    #else:
                    #    owner = Deck.objects.get(id=self.data['fact-deck']).owner
                    #other_field_contents = other_field_contents.filter(fact__deck__owner=owner)
                    if other_field_contents.count() > 0:
                        msg = u'This field must be unique for all facts.'
                        error_list.append(msg)
                        if 'content' in cleaned_data:
                            del cleaned_data['content']
        if error_list:
            if 'content' in self._errors:
                for error_item in error_list:
                    self._errors['content'].append(error_item)
            else:
                self._errors['content'] = ErrorList(error_list)
        return cleaned_data


    class Meta:
        model = FieldContent
        exclude = ('fact',)


