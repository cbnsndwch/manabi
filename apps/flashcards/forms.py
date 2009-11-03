from django.db import models
from django.contrib.auth.models import User
from django.forms import ModelForm
from django.forms.util import ErrorList
from dbtemplates.models import Template
from django.db.models.signals import post_save  


from models import Card, CardHistory, Fact, FactType, FieldType, FieldContent, Deck, CardTemplate

#Forms
#todo:row-level authentication (subclassing formset)

class CardForm(ModelForm):
    class Meta:
        model = Card
        exclude = ('fact', 'ease_factor', )
        
class DeckForm(ModelForm):
    class Meta:
        model = Deck
        exclude = ('owner', )
        
class FactTypeForm(ModelForm):
    class Meta:
        model = FactType

class CardTemplateForm(ModelForm):
    class Meta:
        model = CardTemplate
        
class FactForm(ModelForm):
    class Meta:
        model = Fact


class FieldContentForm(ModelForm):
    def clean(self): #TODO if any(self.errors):return NO:thats just for formsets
        cleaned_data = self.cleaned_data
        contents = cleaned_data.get('contents') or ''
        field_type = cleaned_data.get('field_type')#FieldType.objects.get(id=field_type_id)
        blank = field_type.blank
        unique = field_type.unique
        error_list = []

        if not field_type.multi_line and '\n' in contents:
            msg = u'This is a single-line field.'
            error_list.append(msg)
            if 'contents' in cleaned_data:
              del cleaned_data['contents'] #TODO why do I do this?
        if not blank and not contents.strip():#contents.strip() == '':
            msg = u'This field is required.'
            #self._errors['contents'] = ErrorList([msg])
            error_list.append(msg)
            if 'contents' in cleaned_data:
                del cleaned_data['contents']
        elif field_type: #TODO why check if field_type?
            if contents.strip(): #if it's blank, don't bother checking if it's unique
                if unique: #TODO can a field be blank and unique? probably yes, since blank is like null
                    #dirty hack to get this deck's owner
                    owner = Deck.objects.get(id=self.data['fact-deck'])
                    other_field_contents = FieldContent.objects.filter(fact__deck__owner=owner, field_type=field_type, contents__exact=contents)
                    if cleaned_data.get('id'): #exclude the existing field content if this is an update
                        other_field_contents = other_field_contents.exclude(id=cleaned_data.get('id'))
                    if other_field_contents.count() > 0:
                        msg = u'This field must be unique for all facts.'
                        error_list.append(msg)
                        if 'contents' in cleaned_data:
                            del cleaned_data['contents']
        if error_list:
            if 'contents' in self._errors:
                for error_item in error_list:
                    self._errors['contents'].append(error_item)
            else:
                self._errors['contents'] = ErrorList(error_list)
        return cleaned_data

    #def __init__(self, *args, **kwargs):
    #    #self.queryset = Author.objects.filter(name__startswith='O')
    #    import pdb;pdb.set_trace() #FIXME #fact_deck=
    #    super(FieldContentForm, self).__init__(*args, **kwargs)
    #
    #    #self.fields['user'].queryset = user
    

    class Meta:
        model = FieldContent
        exclude = ('fact',)


