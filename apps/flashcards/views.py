from flashcards.models import FactType, Fact, Deck, CardTemplate, FieldType, FieldContent, Card, SharedDeck, GRADE_NONE, GRADE_HARD, GRADE_GOOD, GRADE_EASY, SchedulingOptions
from flashcards.forms import DeckForm, FactForm, FieldContentForm, CardTemplateForm, FactTypeForm, CardForm
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.forms import forms
from django.forms.models import modelformset_factory, formset_factory
from django.http import Http404
from dojango.decorators import json_response
from dojango.util import to_dojo_data, json_decode, json_encode
from django.template import RequestContext, loader
from django.contrib.auth.decorators import login_required

from flashcards.models.decks import download_shared_deck, share_deck

from django.template.loader import render_to_string

import datetime

from django.db import transaction

from django.views.generic.list_detail import object_list
from django.views.generic.create_update import update_object, delete_object, create_object


# todo:
# respond with a better failure message if an xhr request is made from an unauthenticated user


#@login_required
#def base(request):
#    fact_types = FactType.objects.all()
#    card_templates = CardTemplate.objects.all()
#    fields = FieldType.objects.all()
#    fact_form = FactForm(instance=Fact())
#    fact_type_form = FactTypeForm(instance=FactType())
#    card_template_form = CardTemplateForm(instance=CardTemplate())
#    fact_type_formset = modelformset_factory(FactType)
#    field_content_forms = [FieldContentForm(prefix=str(x), instance=FieldContent()) for x in range(0,3)]
#    return render_to_response('flashcards/base.html',
#                              {'fact_form': fact_form,
#                               'field_content_forms': field_content_forms,
#                               #'fact_type_form': fact_type_form,
#                               'card_template_form': card_template_form,
#                               'fact_types': fact_types,
#                               'fact_type_formset': fact_type_formset,
#                               'card_templates': card_templates},
#                               context_instance=RequestContext(request))

#def _validate_deck_ownership(user, deck_id):

#TODO refactor into other module and into middleware or decorator
def _request_type(request):
  if request.method == 'GET':
    return 'GET'
  elif request.method == 'POST':
    if '_method' in request.POST:
      method = request.POST['_method']
      if method in ['PUT', 'DELETE', 'GET', 'POST']:
        return method
    else:
        return 'POST' #TODO throw error?



#HTML views
#CRUD forms
#TODO refactor into HTML/AJAX CRUD pattern
@login_required
def deck_list(request):
  decks = Deck.objects.filter(owner=request.user)
  return object_list(request, queryset=decks, extra_context={'container_id': 'deckDialog'}, template_object_name='deck')

@login_required
def deck_update(request, deck_id):
  deck = Deck.objects.get(id=deck_id)
  if deck.owner.id != request.user.id: #and not request.User.is_staff():
    raise forms.ValidationError('You do not have permission to access this flashcard deck.')
  #return update_object(request, form_class=DeckForm, object_id=deck_id, post_save_redirect='../decks', extra_context={'container_id': 'deckDialog'}, template_object_name='deck')
  if request.method == 'POST':
    deck_form = DeckForm(request.POST, instance=deck)
    if deck_form.is_valid():
      deck = deck_form.save()
      #request.user.message_set.create(message=ugettext("The %(verbose_name)s was created successfully.") % {"verbose_name": model._meta.verbose_name})
      return HttpResponse(json_encode({'success':True}), mimetype='text/javascript')#return HttpResponseRedirect(post_save_redirect)
  else:
    deck_form = DeckForm(instance=deck)
  return render_to_response('flashcards/deck_form.html', {'form': deck_form,
                                                          'deck': deck,
                                                          'container_id': 'deckDialog',
                                                          'post_save_redirect': '/flashcards/decks'}) #todo:post/pre redirs

@login_required
def deck_delete(request, deck_id, post_delete_redirect='/flashcards/decks'): #todo: pass post_*_redirect from urls.py
  obj = Deck.objects.get(id=deck_id)
  if obj.owner.id != request.user.id: #and not request.User.is_staff():
    raise forms.ValidationError('You do not have permission to access this flashcard deck.')
  if request.method == 'POST':
    obj.delete()
    #request.user.message_set.create(message=ugettext("The %(verbose_name)s was deleted.") % {"verbose_name": model._meta.verbose_name})
    return HttpResponse(json_encode({'success':True}), mimetype='text/javascript')
  else:
    return render_to_response('flashcards/deck_confirm_delete.html', {'deck': obj,
                                                                      'post_delete_redirect': post_delete_redirect,
                                                                      'container_id': 'deckDialog'})

@login_required
def deck_create(request, post_save_redirect='/flashcards/decks'):
  if request.method == 'POST':
    deck_form = DeckForm(request.POST)
    if deck_form.is_valid():
      new_deck = deck_form.save(commit=False)
      new_deck.owner = request.user
      new_deck.save()
      scheduling_options = SchedulingOptions(deck=new_deck)
      scheduling_options.save()
      #request.user.message_set.create(message=ugettext("The %(verbose_name)s was created successfully.") % {"verbose_name": model._meta.verbose_name})
      return HttpResponse(json_encode({'success':True}), mimetype='text/javascript')#HttpResponseRedirect(post_save_redirect)
  else:
    deck_form = DeckForm()
  return render_to_response('flashcards/deck_form.html', {'form': deck_form,
                                                          'container_id': 'deckDialog',
                                                          'post_save_redirect': post_save_redirect}) #todo:post/pre redirs


#shared decks

@login_required
def shared_deck_list(request):
  shared_decks = SharedDeck.objects.all()
  return object_list(request, queryset=shared_decks, extra_context={'container_id': 'deckDialog'}, template_object_name='shared_deck')


@login_required
def shared_deck_download(request, shared_deck_id, post_download_redirect='/flashcards/decks'): #todo: pass post_*_redirect from urls.py
  obj = SharedDeck.objects.get(id=shared_deck_id)
  if request.method == 'POST':
    download_shared_deck(request.user, obj)
    return HttpResponse(json_encode({'success':True}), mimetype='text/javascript')
  else:
    return render_to_response('flashcards/shareddeck_download_form.html', {'shared_deck': obj,
                                                                            'post_download_redirect': post_download_redirect,
                                                                            'container_id': 'deckDialog'})

@login_required
def deck_share(request, deck_id, post_redirect='/flashcards/shared_decks'): #todo: pass post_*_redirect from urls.py
  obj = Deck.objects.get(id=deck_id)
  if obj.owner.id != request.user.id: #and not request.User.is_staff():
    raise forms.ValidationError('You do not have permission to access this flashcard deck.')
  if request.method == 'POST':
    share_deck(obj)
    return HttpResponse(json_encode({'success':True}), mimetype='text/javascript')
  else:
    return render_to_response('flashcards/deck_share_form.html', {'deck': obj,
                                                                  'post_redirect': post_redirect,
                                                                  'container_id': 'deckDialog'})

#REST views

def rest_entry_point(request):
  pass

@login_required
@json_response
def rest_decks(request):
  if request.method == "POST":
    pass
  elif request.method == "GET":
    try:
      ret = Deck.objects.filter(owner=request.user)
    except Deck.DoesNotExist:
      ret = []
    return to_dojo_data(ret)
    

@login_required
@json_response
def rest_deck(request, deck_id):
  method = _request_type(request)
  if method == 'DELETE':
    obj = Deck.objects.get(id=deck_id)
    if obj.owner.id != request.user.id: #and not request.User.is_staff():
      raise forms.ValidationError('You do not have permission to access this flashcard deck.')
    obj.delete()
    #request.user.message_set.create(message=ugettext("The %(verbose_name)s was deleted.") % {"verbose_name": model._meta.verbose_name})
    return {'success':True}
  if method == 'PUT':
    if Deck.objects.get(id=deck_id).owner.id != request.user.id: #and not request.User.is_staff():
      raise forms.ValidationError('You do not have permission to access this flashcard deck.')
    #TODO replace update_object to get rid of post_save_redirect, it's useless for ajax
    pass#return update_object(request, form_class=DeckForm, object_id=deck_id, post_save_redirect='/flashcards/decks', extra_context={'container_id': 'deckDialog', 'post_save_redirect': '/flashcards/decks'}, template_object_name='deck')
  elif method == 'POST':
    pass


@login_required
@json_response
def rest_card_templates(request, fact_type_id):
  "Returns list of CardTemplate objects given a parent FactType id"
  method = _request_type(request)
  if method == 'GET':
    try:
      fact_type = FactType.objects.get(id=fact_type_id) #todo: error handling
      ret = fact_type.cardtemplate_set.all()
    except FactType.DoesNotExist:
      ret = []
    return to_dojo_data(ret)


@login_required
@json_response
def rest_fields(request, fact_type_id):
  "Returns list of Field objects given a FactType id"
  method = _request_type(request)
  if method == 'GET':
    try:
      fact_type = FactType.objects.get(id=fact_type_id) #todo: error handling
      ret = fact_type.fieldtype_set.all()
    except FactType.DoesNotExist:
      ret = []
    return to_dojo_data(ret)


@login_required
@json_response
def rest_fact_types(request):
  method = _request_type(request)
  if method == 'GET':
    fact_types = FactType.objects.all()#SOMEDAY filter(deck__owner=request.user)
    return to_dojo_data(fact_types)


#FIXME add validation for every method, like if obj.owner.id != request.user.id: #and not request.User.is_staff():      raise forms.ValidationError('You do not have permission to access this flashcard deck.')

#TODO add 'success':True where missing

@login_required
@json_response
def rest_cards(request): #todo:refactor into facts (no???)
  method = _request_type(request)
  if method == 'GET':
    if request.GET['fact']:
      ret = {}
      try:
        fact = Fact.objects.get(id=request.GET['fact'])
        cards = fact.card_set.get_query_set()
        return to_dojo_data(cards)
      except Fact.DoesNotExist:
        return {'success': False}



@login_required
@json_response
def rest_card_templates_for_fact(request, fact_id):
  'Returns a list of card templates for which the given fact has corresponding cards activated'
  method = _request_type(request)
  if method == 'GET':
    ret = {}
    try:
      card_templates = []
      fact = Fact.objects.get(id=fact_id)
      activated_card_templates = [e.template for e in fact.card_set.filter(active=True)]
      for card_template in fact.fact_type.cardtemplate_set.all():
        #TODO only send the id(uri)/name/status
        card_templates.append({'card_template': card_template, 'activated_for_fact': (card_template in activated_card_templates)})
      return to_dojo_data(card_templates, identifier=None)
    except Fact.DoesNotExist:
      return {'success': False}


@login_required
@json_response
def rest_facts(request): #todo:refactor into facts (no???)
  method = _request_type(request)
  if method == 'GET':
    if request.GET['fact_type']:
      fact_type_id = request.GET['fact_type']
      ret = {}
      try:
        #facts = Fact.objects.filter(fact_type=FactType.objects.get(id=fact_type_id))
        #ret = to_dojo_data(facts.fieldcontent_set)
        fact_type = FactType.objects.get(id=fact_type_id)
        facts = fact_type.fact_set.filter(deck__owner=request.user)
        if not facts:
          ret = {}
        else:
          preret = []
          for fact in facts:
            row = {'fact-id': fact.id}
            ident, name = '', ''
            for field_content in fact.fieldcontent_set.all():
              key='id{0}'.format(field_content.field_type.id) #TODO rename to be clearer, like field_id or SOMETHING
              if not ident:
                ident = key
              elif not name:
                name = key
              row[key]=field_content.contents#field_content.field_type.id] = field_content.contents
              row['{0}_field-content-id'.format(key)] = field_content.id
            if not name:
              name = ident
            preret.append(row)
          ret=to_dojo_data(preret)
          ret['identifier'] = 'fact-id'#ident
          #ret['name'] = name #todo:for <2 cols/fields...?
          return ret
      except FactType.DoesNotExist:
          ret = {}
      return to_dojo_data(ret)
  elif method == 'POST':
    return _facts_create(request)


@login_required
@json_response
def rest_fact(request, fact_id): #todo:refactor into facts
  method = _request_type(request)
  if method == 'PUT':
    return _fact_update(request, fact_id)
  elif method == 'DELETE':
    return _fact_delete(request, fact_id)


def _fact_delete(request, fact_id):
  try:
    fact = Fact.objects.get(id=fact_id)
    fact.delete()
    return {'success': True}
  except Fact.DoesNotExist:
    return {'success': False} #TODO add error message


def _fact_update(request, fact_id):
  ret = {}
  #FIXME make sure the logged-in user owns this FACT
  #if Deck.objects.get(id=deck_id).owner.id != request.user.id: #and not request.User.is_staff():
  #  ret['success'] = False
  #  raise forms.ValidationError('You do not have permission to access this flashcard deck.')

  #override the submitted deck ID with the ID from the URL, since this is a RESTful interface
  post_data = request.POST.copy()

  #todo: refactor this into model code
  
  fact = Fact.objects.get(id=fact_id)
  
  CardFormset = modelformset_factory(Card, exclude=('fact', 'ease_factor', )) #TODO make from CardForm
  card_formset = CardFormset(post_data, prefix='card', queryset=fact.card_set.get_query_set())
  
  FieldContentFormset = modelformset_factory(FieldContent, form=FieldContentForm)
  field_content_formset = FieldContentFormset(post_data, prefix='field_content', queryset=fact.fieldcontent_set.get_query_set())

  #fact_form = FactForm(post_data, prefix='fact', instance=fact) #this isn't updated
  if card_formset.is_valid() and field_content_formset.is_valid(): #and fact_form.is_valid():
    #fact = fact_form.save() #TODO needed in future?
    
    for field_content_form in field_content_formset.forms:
      field_content = field_content_form.save()

    #disable any existing cards that weren't selected in the update, or enable if selected and create if needed
    card_form_template_ids = [card_form.cleaned_data['template'].id for card_form in card_formset.forms]
    for card_template in fact.fact_type.cardtemplate_set.all():
      if card_template.id in card_form_template_ids:
        try: 
          card = fact.card_set.get(template=card_template)
          card.active = True
          card.save()
        except Card.DoesNotExist:
          card_form = card_formset.get_queryset().get(template=card_template)
          new_card = card_form.save(commit=False)
          new_card.fact = fact
          new_card.active = True
          new_card.save()
      else:
        #card was not selected in update, so disable it if it exists
        try:
          card = fact.card_set.get(template=card_template)
          card.active = False
          card.save()
        except Card.DoesNotExist:
          pass
          
    ret['success'] = True

  else:
    print field_content_formset.errors
    ret['success'] = False
    ret['errors'] = {'card': card_formset.errors,
                     'field_content': field_content_formset.errors,
                     'fact': [fact_form.errors]}
  return ret


def _facts_create(request):
  #create fact in deck, including its fields and cards. POST method.
  #todo: unicode support
  #TODO refactor into other module probably
  ret = {}
  deck_id = request.POST['fact-deck'] #TODO just get this from the form
  
  # make sure the logged-in user owns this deck
  if Deck.objects.get(id=deck_id).owner.id != request.user.id: #and not request.User.is_staff():
    ret['success'] = False
    raise forms.ValidationError('You do not have permission to access this flashcard deck.')

  #override the submitted deck ID with the ID from the URL, since this is a RESTful interface
  post_data = request.POST.copy()
  #post_data['fact-deck'] = deck_id
  
  #todo: refactor this into model code
  
  CardFormset = modelformset_factory(Card, exclude=('fact', 'ease_factor', )) #TODO make from CardForm
  card_formset = CardFormset(post_data, prefix='card')
  
  #FieldContentFormset = modelformset_factory(FieldContent, exclude=('fact', ))
  FieldContentFormset = formset_factory(FieldContentForm)
  field_content_formset = FieldContentFormset(post_data, prefix='field_content')
  
  fact_form = FactForm(post_data, prefix='fact')
  
  if card_formset.is_valid() and field_content_formset.is_valid() and fact_form.is_valid():
    new_fact = fact_form.save()
      
    for field_content_form in field_content_formset.forms:
      new_field_content = field_content_form.save(commit=False)
      new_field_content.fact = new_fact
      new_field_content.save()
    
    for card_form in card_formset.forms:
      new_card = card_form.save(commit=False)
      new_card.fact = new_fact
      new_card.active = True
      new_card.priority = 0
      new_card.save()
  else:
    print field_content_formset.errors
    ret['success'] = False
    ret['errors'] = {'card': card_formset.errors,
                     'field_content': field_content_formset.errors,
                     'fact': [fact_form.errors]}
  return ret


  
                
        


#def add_fact(request):
#    pass
#    if request.method == "POST":
#        pform = PollForm(request.POST, instance=Poll())
#        cforms = [ChoiceForm(request.POST, prefix=str(x), instance=Choice()) for x in range(0,3)]
#        if pform.is_valid() and all([cf.is_valid() for cf in cforms]):
#            new_poll = pform.save()
#            for cf in cforms:
#                new_choice = cf.save(commit=False)
#                new_choice.poll = new_poll
#                new_choice.save()
#            return HttpResponseRedirect('/polls/add/')
#    else:
#        pform = PollForm(instance=Poll())
#        cforms = [ChoiceForm(prefix=str(x), instance=Choice()) for x in range(0,3)]
#    return render_to_response('add_poll.html', {'poll_form': pform, 'choice_forms': cforms})









     ################################
  ######################################  
 ##                                    ## 
###        > Flashcard Review <        ###
 ##                                    ## 
  ######################################  
     ###############################




@login_required
@json_response
def next_cards_for_review(request):
    if request.method == 'GET':
        count = int(request.GET.get('count', 5))

        try:
            excluded_card_ids = [int(e) for e in request.GET.get('excluded_cards', '').split()]
        except ValueError:
            excluded_card_ids = []

        next_cards = Card.objects.next_cards(request.user, count, excluded_card_ids)#[:count]
        #FIXME need to account for 0 cards returned 

        # format into json object
        formatted_cards = []
        reviewed_at = datetime.datetime.utcnow()
        for card in next_cards:
            field_contents = dict((field_content.field_type_id, field_content.contents,) for field_content in card.fact.fieldcontent_set.all())
            card_context = {'fields': field_contents}
            #front = render_to_string(card.template.front_template_name, 
            due_times = {}
            for grade in [GRADE_NONE, GRADE_HARD, GRADE_GOOD, GRADE_EASY,]:
                due_at = card._next_due_at(grade, reviewed_at, card._next_interval(grade, card._next_ease_factor(grade)))
                duration = due_at - reviewed_at
                days = duration.days + (duration.seconds / 86400.0)
                due_times[grade] = days
            formatted_cards.append({
                'id': card.id,
                'front': render_to_string(card.template.front_template_name, card_context),
                'back': render_to_string(card.template.back_template_name, card_context),
                'next_due_at_per_grade': due_times
            })

        return {'success': True, 'cards': formatted_cards}

@json_response
@login_required
def cards_due_count(request):
    if request.method == 'GET':
        count = Card.objects.cards_due_count(request.user)
        return {'cards_due_count': count}

@json_response
@login_required
def cards_new_count(request):
    if request.method == 'GET':
        count = Card.objects.cards_new_count(request.user)
        return {'cards_new_count': count}

def _rest_review_card(request, card_id):
    '''
    '''
    method = _request_type(request)
    if method == 'POST':
        try:
            card = Card.objects.get(id=card_id) #FIXME make sure this user owns this card
            card.review(int(request.POST['grade']))
            card.save()
            return {'success': True}
        except Card.DoesNotExist:
            return {'success': False}




@login_required
@json_response
def rest_card(request, card_id): #todo:refactor into facts (no???)
  method = _request_type(request)
  if method == 'GET':
    ret = {}
    try:
      card = Card.objects.get(id=int(card_id))
      return to_dojo_data(card)
    except Card.DoesNotExist:
      return {'success': False}
  elif method == 'POST':
    if 'grade' in request.POST:
        # this is a card review
        return _rest_review_card(request, int(card_id))



