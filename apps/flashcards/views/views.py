from flashcards.models import FactType, Fact, Deck, CardTemplate, FieldType, FieldContent, Card, SharedDeck, GRADE_NONE, GRADE_HARD, GRADE_GOOD, GRADE_EASY, SchedulingOptions, NEW_CARDS_PER_DAY
from flashcards.models.constants import MAX_NEW_CARD_ORDINAL
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
from django.contrib.humanize.templatetags.humanize import naturalday
#from flashcards.models.decks import download_shared_deck, share_deck
from flashcards.models.undo import UndoCardReview
from apps.utils import japanese
import random

from flashcards.contextprocessors import study_options_context
from django.template.loader import render_to_string

import usertagging

import datetime
import string
import subprocess
import jcconv

from django.db import transaction

from django.views.generic.list_detail import object_list, object_detail
from django.views.generic.create_update import update_object, delete_object, create_object

from decorators import all_http_methods



#todo:
# respond with a better failure message if an xhr request is made from an unauthenticated user


#def _validate_deck_ownership(user, deck_id):


# New layout views

@login_required
def add_decks(request):
    '''Starting point for adding a deck, whether by creating or by downloading a shared deck.'''
    #shared_decks = SharedDeck.objects.all()
    shared_decks = Deck.objects.shared_decks()
    context = {'shared_deck_list': shared_decks}
    return render_to_response('flashcards/add.html', context, context_instance=RequestContext(request))
    #return object_list(request, queryset=shared_decks, template_object_name='shared_deck')
    


@login_required
@json_response
@all_http_methods
def rest_deck_subscribe(request, deck_id):
    try:
        deck = Deck.objects.get(id=deck_id)
        if deck.owner_id == request.user.id: #and not request.User.is_staff():
            raise forms.ValidationError('You cannot subscribe to a deck which you created yourself. Subscription is for other users.')
        elif not deck.shared:
            raise forms.ValidationError('This deck is not shared, so you cannot subscribe to it.')
    except Deck.DoesNotExist:
        raise Http404

    if request.method == 'POST':
        new_deck = deck.subscribe(request.user)
        return {'success':True, 'deck_id': new_deck.id, 'post_redirect': new_deck.get_absolute_url()}
    else:
        raise Http404


def deck_detail(request, deck_id=None):
    detail_args = {
        'queryset': Deck.objects.filter(active=True),
        'template_object_name': 'deck',
        'extra_context': {
            'field_types': FactType.objects.get(id=1).fieldtype_set.all().order_by('ordinal'),
        },
        'object_id': deck_id,
    }
    detail_args['extra_context'].update(study_options_context(request, deck_id=deck_id))
    return object_detail(request, **detail_args)




#HTML views

@login_required
def facts_editor(request):
    #assume Japanese for now (model 1)
    #get the fieldtypes for Japanese
    
    fact_type = FactType.objects.get(id=1)
    field_types = fact_type.fieldtype_set.all().order_by('ordinal')
    card_templates = fact_type.cardtemplate_set.all()
    decks = Deck.objects.filter(owner=request.user, active=True)
    context = {'field_types': field_types,
               'card_templates': card_templates,
               'decks': decks}
    return render_to_response('flashcards/facts_editor.html', context)


@login_required
def fact_update(request, fact_id):
    if request.method == 'GET':
        # if this is a subscribed fact that the subscriber hasn't copied yet, copy the fact (without its field contents) first
        fact = Fact.objects.get_for_owner_or_subscriber(fact_id, request.user)
        fact.edit_string_for_tags = usertagging.utils.edit_string_for_tags(fact.tags)
        fact_type = FactType.objects.get(id=1) #assume japanese for now
        decks = Deck.objects.filter(owner=request.user, active=True)
        card_templates = []
        activated_card_templates = [e.template for e in fact.card_set.filter(active=True)]
        for card_template in fact_type.cardtemplate_set.all():
            #TODO only send the id(uri)/name/status
            #card_templates.append({'card_template': card_template, 'activated_for_fact': (card_template in activated_card_templates)})
            card_template.activated_for_fact = (card_template in activated_card_templates)
            card_templates.append(card_template)
        context = {'fact': fact, 'card_templates': card_templates, 'decks': decks, 'field_contents': fact.field_contents}
        return render_to_response('flashcards/fact_form.html', context)


#CRUD forms
#TODO refactor into HTML/AJAX CRUD pattern
@login_required
def deck_list(request):
  decks = Deck.objects.filter(owner=request.user, active=True)
  context = {'container_id': 'deckDialog'}
  context['only_one_deck_exists'] = (len(decks) == 1)

  return object_list(request, queryset=decks, extra_context=context, template_object_name='deck')


@login_required
def deck_update(request, deck_id):
  deck = Deck.objects.get(id=deck_id)
  if deck.owner_id != request.user.id: #and not request.User.is_staff():
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
  if obj.owner_id != request.user.id: #and not request.User.is_staff():
    raise forms.ValidationError('You do not have permission to access this flashcard deck.')
  if request.method == 'POST':
    #DO ALLOW #don't allow the last deck to be deleted
    #if Deck.objects.filter(owner=request.user, active=True).count() == 1:
    #    return HttpResponse(json_encode({'success':False}, mimetype='text/javascript')) #TODO error message

    if obj.subscriber_decks.filter(active=True).count() > 0: #exists():
        obj.active = False
        obj.save()
    else:
        obj.delete_cascading()
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
      if 'tags' in deck_form.cleaned_data:
        new_deck.tags = deck_form.cleaned_data['tags']

      scheduling_options = SchedulingOptions(deck=new_deck)
      scheduling_options.save()
      #request.user.message_set.create(message=ugettext("The %(verbose_name)s was created successfully.") % {"verbose_name": model._meta.verbose_name})
      return HttpResponse(json_encode({'success': True, 'post_redirect': new_deck.get_absolute_url()}), mimetype='text/javascript')#HttpResponseRedirect(post_save_redirect)
    else:
      #FIXME post_redirect for failure? handle in ajax?
      return HttpResponse(json_encode({'success': False}), mimetype='text/javascript')
  else:
    deck_form = DeckForm()
  return render_to_response('flashcards/deck_form.html', {'form': deck_form,
                                                          'post_save_redirect': post_save_redirect}) #todo:post/pre redirs


#shared decks


@login_required
def deck_share(request, deck_id, post_redirect='/flashcards/shared_decks'): #todo: pass post_*_redirect from urls.py
  obj = Deck.objects.get(id=deck_id)
  if obj.owner_id != request.user.id: #and not request.User.is_staff():
    raise forms.ValidationError('You do not have permission to access this flashcard deck.')
  if request.method == 'POST':
    obj.share()
    return HttpResponse(json_encode({'success': True}), mimetype='text/javascript')
  else:
    return render_to_response('flashcards/deck_share_form.html', {'deck': obj,
                                                                  'post_redirect': post_redirect,
                                                                  'container_id': 'deckDialog'})

#REST views

def rest_entry_point(request):
    pass


@login_required
@json_response
def rest_generate_reading(request):
    if request.method == 'POST':
        expression = request.POST['expression']
        ret = japanese.generate_reading(expression)
        return {'success':True, 'reading': ret}
        


@login_required
@json_response
def rest_decks_with_totals(request):
    if request.method == "GET":
        try:
            #decks = Deck.objects.filter(owner=request.user).values() #TODO fields
            decks = Deck.objects.values_of_all_with_stats_and_totals(request.user, 
                    fields=['id', 'name'])
        except Deck.DoesNotExist:
            decks = []

        return to_dojo_data(decks, label='name')

@login_required
@json_response
def rest_decks(request):
    if request.method == "POST":
        pass
    elif request.method == "GET":
        try:
            ret = Deck.objects.filter(owner=request.user, active=True).values('id', 'name', 'description')
        except Deck.DoesNotExist:
            ret = []
        return to_dojo_data(ret, label='name')
    

@login_required
@json_response
@all_http_methods
def rest_deck(request, deck_id):
    try:
        deck = Deck.objects.get(id=deck_id)
        if deck.owner_id != request.user.id: #and not request.User.is_staff():
            raise forms.ValidationError('You do not have permission to access this flashcard deck.')
    except Deck.DoesNotExist:
        raise Http404

    if request.method == 'DELETE':
        if deck.subscriber_decks.filter(active=True).count() > 0: #exists():
            deck.active = False
            deck.save()
        else:
            deck.delete_cascading()
        #request.user.message_set.create(message=ugettext("The %(verbose_name)s was deleted.") % {"verbose_name": model._meta.verbose_name})
        return {'success':True}
    elif request.method == 'PUT':
        #TODO replace update_object to get rid of post_save_redirect, it's useless for ajax
        pass#return update_object(request, form_class=DeckForm, object_id=deck_id, post_save_redirect='/flashcards/decks', extra_context={'container_id': 'deckDialog', 'post_save_redirect': '/flashcards/decks'}, template_object_name='deck')
    elif request.method == 'POST':
        # change shared status
        if 'shared' in request.POST:
            shared = request.POST['shared'].lower() == 'true'
            if shared:
                if deck.synchronized_with:
                    return {'success':False}
                deck.share()
            else:
                if not deck.shared:
                    return {'success':False}
                deck.unshare()
        else:
            raise Http404


@login_required
@json_response
@all_http_methods
def rest_card_templates(request, fact_type_id):
    "Returns list of CardTemplate objects given a parent FactType id"
    if request.method == 'GET':
        try:
            fact_type = FactType.objects.get(id=fact_type_id) #todo: error handling
            ret = fact_type.cardtemplate_set.all()
        except FactType.DoesNotExist:
            ret = []
        return to_dojo_data(ret)


@login_required
@json_response
@all_http_methods
def rest_fields(request, fact_type_id):
    "Returns list of Field objects given a FactType id"
    if request.method == 'GET':
        try:
            fact_type = FactType.objects.get(id=fact_type_id) #todo: error handling
            ret = fact_type.fieldtype_set.all().order_by('ordinal')
        except FactType.DoesNotExist:
            ret = []
        return to_dojo_data(ret)


@login_required
@json_response
@all_http_methods
def rest_fact_types(request):
    if request.method == 'GET':
        fact_types = FactType.objects.all()#SOMEDAY filter(deck__owner=request.user)
        return to_dojo_data(fact_types)


#FIXME add validation for every method, like if obj.owner.id != request.user.id: #and not request.User.is_staff():      raise forms.ValidationError('You do not have permission to access this flashcard deck.')

#TODO add 'success':True where missing

@login_required
@json_response
@all_http_methods
def rest_cards(request): #todo:refactor into facts (no???)
    if request.method == 'GET':
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
@all_http_methods
def rest_card_templates_for_fact(request, fact_id):
  'Returns a list of card templates for which the given fact has corresponding cards activated'
  if request.method == 'GET':
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
def rest_facts_tags(request):
  if request.method == 'GET':
      tags = Fact.objects.all_tags_per_user(request.user)
      tags = [{'name': tag.name, 'id': tag.id} for tag in tags]
      return to_dojo_data(tags)


@login_required
@json_response
@all_http_methods
@transaction.commit_on_success
def rest_facts(request): #todo:refactor into facts (no???)
    if request.method == 'GET':
        if request.GET['fact_type']:
            fact_type_id = request.GET['fact_type'] #TODO allow omitting this option
            ret = {}
            try:
                #facts = Fact.objects.filter(fact_type=FactType.objects.get(id=fact_type_id))
                fact_type = FactType.objects.get(id=fact_type_id)

                #filtering by deck
                if 'deck' in request.GET and request.GET['deck'].strip():
                   try:
                       deck = Deck.objects.get(id=int(request.GET['deck']))
                   except Deck.DoesNotExist:
                       raise Http404
                else:
                    deck = None
                #    user_facts = fact_type.fact_set.filter(deck=deck)
                #else:
                #    user_facts = fact_type.fact_set.filter(deck__owner=request.user)

                #facts = user_facts

                #filtering by tags
                if 'tags' in request.GET and request.GET['tags'].strip():
                    tag_ids = [int(tag_id) for tag_id in request.GET['tags'].split(',')]
                    tags = usertagging.models.Tag.objects.filter(id__in=tag_ids)
                    #facts = usertagging.models.UserTaggedItem.objects.get_by_model(user_facts, tags)
                else:
                    tags = None

                if deck:
                    user = deck.owner
                else:
                    user = request.user

                facts = Fact.objects.with_synchronized(user, deck=deck, tags=tags).filter(active=True)

                #is the user searching his facts?
                if 'search' in request.GET and request.GET['search'].strip():
                    search_query = request.GET['search']
                    facts = Fact.objects.search(fact_type, search_query, query_set=facts)
                    #FIXME add search for synchronized facts too!

                if not facts:
                    ret = {}
                else:
                    preret = []
                    for fact in facts:
                        row = {
                                'fact-id': fact.id, 
                                'suspended': len(fact.card_set.filter(active=True)) and all([card.suspended for card in fact.card_set.filter(active=True)])
                        }
                        ident, name = '', ''
                        for field_content in fact.field_contents: #.all():
                            key = 'id{0}'.format(field_content.field_type_id) #TODO rename to be clearer, like field_id or SOMETHING
                            if not ident:
                                ident = key
                            elif not name:
                                name = key
                            row[key] = field_content.human_readable_content
                            row['{0}_field-content-id'.format(key)] = field_content.id
                        if not name:
                            name = ident

                        preret.append(row)
                    ret = to_dojo_data(preret)
                    ret['identifier'] = 'fact-id'#ident
                    #ret['name'] = name #todo:for <2 cols/fields...?
                    return ret
            except FactType.DoesNotExist:
                ret = {}
            return to_dojo_data(ret)
    elif request.method == 'POST':
        return _facts_create(request)

#@login_required
#@json_response
#def rest_card_suspend(request, card_id):
#    if request.method == 'POST':
#        try:
#            fact = Card.objects.get(id=card_id)
#            
#            card.suspended = True
#            card.save()
#            return {'success': True}
#        except Card.DoesNotExist:
#            return {'success': False}


@login_required
@json_response
@transaction.commit_on_success
def rest_fact_suspend(request, fact_id):
    if request.method == 'POST':
        try:
            fact = Fact.objects.get_for_owner_or_subscriber(fact_id, request.user)
            #fact.suspended = True
            #fact.save()
            for card in fact.card_set.all():
                card.suspended = True
                card.save()
            return {'success': True}
        except Fact.DoesNotExist:
            return {'success': False}


@login_required
@json_response
@transaction.commit_on_success
def rest_fact_unsuspend(request, fact_id):
    if request.method == 'POST':
        try:
            fact = Fact.objects.get_for_owner_or_subscriber(fact_id, request.user)
            #fact.suspended = False
            #fact.save()
            for card in fact.card_set.all():
                card.suspended = False
                card.save()
            return {'success': True}
        except Fact.DoesNotExist:
            return {'success': False}


@login_required
@json_response
@all_http_methods
@transaction.commit_on_success
def rest_fact(request, fact_id): #todo:refactor into facts
  if request.method == 'PUT':
    return _fact_update(request, fact_id)
  elif request.method == 'DELETE':
    return _fact_delete(request, fact_id)


def _fact_delete(request, fact_id):
  try:
    fact = Fact.objects.get_for_owner_or_subscriber(fact_id, request.user)
    if fact.synchronized_with:
        fact.active = False
        fact.save()
    else:
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
    
    # if this fact is a shared fact which the current subscribing user hasn't copied yet, copy it first
    fact = Fact.objects.get_for_owner_or_subscriber(fact_id, request.user)

    fact_form = FactForm(post_data, prefix='fact', instance=fact)
    
    CardFormset = modelformset_factory(Card, exclude=('fact', 'ease_factor', )) #TODO make from CardForm
    card_formset = CardFormset(post_data, prefix='card', queryset=fact.card_set.get_query_set())
    
    FieldContentFormset = modelformset_factory(FieldContent, form=FieldContentForm)
    field_content_queryset = fact.fieldcontent_set.get_query_set() or None
    if field_content_queryset:
        #FieldContentFormset = formset_factory(FieldContentForm)
        field_content_formset = FieldContentFormset(post_data, prefix='field_content', queryset=field_content_queryset)
    else:
        #FieldContentFormset = modelformset_factory(FieldContent, form=FieldContentForm)
        field_content_formset = FieldContentFormset(post_data, prefix='field_content')


    #fact_form = FactForm(post_data, prefix='fact', instance=fact) #this isn't updated
    if card_formset.is_valid() and field_content_formset.is_valid() and fact_form.is_valid():
        fact = fact_form.save() #TODO needed in future?
        
        #update the fact's assigned deck
        #FIXME catch error if does not exist
        #deck_id = int(post_data['fact-deck'])
        #fact.deck = Deck.objects.get(id=deck_id)
        #fact.save()

        for field_content_form in field_content_formset.forms:
            field_content = field_content_form.save(commit=False)
            field_content.fact = fact
            field_content_form.save()

        # disable any existing cards that weren't selected in the update, or enable if selected and create if needed
        #
        # do for subscribers too
        facts = Fact.objects.filter(id=fact.id)
        if fact.subscriber_facts.all():
            facts = facts | fact.subscriber_facts.all()
        for fact2 in facts.iterator():
            card_form_template_ids = dict((card_form.cleaned_data['template'].id, card_form) for card_form in card_formset.forms)
            for card_template in fact.fact_type.cardtemplate_set.all():
                if card_template.id in card_form_template_ids.keys():
                    try:
                        card = fact2.card_set.get(template=card_template)
                        card.active = True
                        card.save()
                    except Card.DoesNotExist:
                        #card_form = card_form_template_ids[card_template.id]
                        #new_card = card_form.save(commit=False)
                        new_card = Card(template=card_template)
                        new_card.fact = fact2
                        new_card.active = True
                        new_card.new_card_ordinal = random.randrange(0, MAX_NEW_CARD_ORDINAL)
                        new_card.save()
                else:
                    #card was not selected in update, so disable it if it exists
                    try:
                        card = fact2.card_set.get(template=card_template)
                        if not card.active:
                            continue
                        elif fact2.synchronized_with and card.review_count:
                            # don't disable subscriber cards which have already been reviewed
                            continue
                        card.active = False
                        card.save()
                    except Card.DoesNotExist:
                        pass
                        
        ret['success'] = True
    else:
        ret['success'] = False
        ret['errors'] = {'card': card_formset.errors,
                        'field_content': field_content_formset.errors, }
                        #'fact': [fact_form.errors]}
    return ret


def _facts_create(request):
  #create fact in deck, including its fields and cards. POST method.
  #todo: unicode support
  #TODO refactor into other module probably
  ret = {}
  deck_id = request.POST['fact-deck'] #TODO just get this from the form
  
  # make sure the logged-in user owns this deck
  if Deck.objects.get(id=deck_id).owner_id != request.user.id: #and not request.User.is_staff():
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
    new_fact = fact_form.save() #TODO automate the tag saving in forms.py
    new_fact.active = True
    new_fact.save()

    for field_content_form in field_content_formset.forms:
      #TODO don't create fieldcontent objects for optional fields which were left blank
      new_field_content = field_content_form.save(commit=False)
      new_field_content.fact = new_fact
      new_field_content.save()
    
    for card_form in card_formset.forms:
      new_card = card_form.save(commit=False)
      new_card.fact = new_fact
      new_card.active = True
      new_card.new_card_ordinal = random.randrange(0, MAX_NEW_CARD_ORDINAL)
      new_card.priority = 0
      new_card.save()
  else:
    print field_content_formset.errors
    ret['success'] = False
    ret['errors'] = {'card': card_formset.errors,
                     'field_content': field_content_formset.errors,
                     'fact': [fact_form.errors]}
  return ret


  








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

        # Deck.
        try:
            deck_id = int(request.GET.get('deck', -1))
        except ValueError:
            deck_id = -1
        deck = None
        if deck_id != -1:
            try:
                deck = Deck.objects.get(id=deck_id)
            except Deck.DoesNotExist:
                pass #TODO return error instead

        # Tags.
        try:
            tag_id = int(request.GET.get('tag', -1))
        except ValueError:
            tag_id = -1
        if tag_id != -1:
            tag_ids = [tag_id] #TODO support multiple tags
            tags = usertagging.models.Tag.objects.filter(id__in=tag_ids)
        else:
            tags = None

        # New cards per day limit.
        #TODO implement this to be user-configurable instead of hard-coded
        daily_new_card_limit = NEW_CARDS_PER_DAY

        # Early Review
        early_review = request.GET.get('early_review', 'false').lower() == 'true'

        # Learn More new cards. Usually this will be combined with early_review.
        learn_more = request.GET.get('learn_more', 'false').lower() == 'true'
        if learn_more:
            daily_new_card_limit = None

        # Beginning of review session?
        session_start = string.lower(request.GET.get('session_start', 'false')) == 'true'

        try:
            excluded_card_ids = [int(e) for e in request.GET.get('excluded_cards', '').split()]
        except ValueError:
            excluded_card_ids = []

        next_cards = Card.objects.next_cards(request.user, count, excluded_card_ids, session_start, \
                deck=deck, tags=tags, early_review=early_review, daily_new_card_limit=daily_new_card_limit)
        #FIXME need to account for 0 cards returned 

        # format into json object
        formatted_cards = []
        reviewed_at = datetime.datetime.utcnow()
        for card in next_cards:
            #field_contents = dict((field_content.field_type_id, field_content) for field_content in card.fact.fieldcontent_set.all())
            #card_context = {'fields': field_contents}
            formatted_cards.append({
                'id': card.id,
                'fact_id': card.fact_id,
                'front': card.render_front(),
                'back': card.render_back(),
                'next_due_at_per_grade': card.due_at_per_grade(reviewed_at=reviewed_at),
             })

        ret = {'success': True, 'cards': formatted_cards}

        # New card count for today.
        new_reviews_today = request.user.reviewstatistics.get_new_reviews_today()
        if daily_new_card_limit:
            new_cards_left_for_today = daily_new_card_limit - new_reviews_today
            if new_cards_left_for_today < 0:
                new_cards_left_for_today = 0
            ret['new_cards_left_for_today'] = new_cards_left_for_today

            # New cards left for this query. #TODO rename it
            ret['new_cards_left'] = Card.objects.new_cards_count(request.user, excluded_card_ids, deck=deck, tags=tags)
        ret['total_card_count_for_query'] = Card.objects.count(request.user, deck=deck, tags=tags)

        return ret


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


    #(r'^rest/cards_for_review/due_tomorrow_count$', 'views.cards_due_tomorrow_count'),
    #(r'^rest/cards_for_review/next_card_due_at$', 'views.next_card_due_at'),

@json_response
@login_required
def cards_due_tomorrow_count(request):
    if request.method == 'GET':
        #TODO refactor request parameters somehow
        # Deck.
        try:
            deck_id = int(request.GET.get('deck', -1))
        except ValueError:
            deck_id = -1
        deck = None
        if deck_id != -1:
            try:
                deck = Deck.objects.get(id=deck_id)
            except Deck.DoesNotExist:
                pass #TODO return error instead

        # Tags.
        try:
            tag_id = int(request.GET.get('tag', -1))
        except ValueError:
            tag_id = -1
        if tag_id != -1:
            tag_ids = [tag_id] #TODO support multiple tags
            tags = usertagging.models.Tag.objects.filter(id__in=tag_ids)
        else:
            tags = None
        
        count = Card.objects.count_of_cards_due_tomorrow(request.user, deck=deck, tags=tags)
        return {'cards_due_tomorrow_count': count}

@json_response
@login_required
def hours_until_next_card_due(request):
    if request.method == 'GET':
        #TODO refactor request parameters somehow
        # Deck.
        try:
            deck_id = int(request.GET.get('deck', -1))
        except ValueError:
            deck_id = -1
        deck = None
        if deck_id != -1:
            try:
                deck = Deck.objects.get(id=deck_id)
            except Deck.DoesNotExist:
                pass #TODO return error instead

        # Tags.
        try:
            tag_id = int(request.GET.get('tag', -1))
        except ValueError:
            tag_id = -1
        if tag_id != -1:
            tag_ids = [tag_id] #TODO support multiple tags
            tags = usertagging.models.Tag.objects.filter(id__in=tag_ids)
        else:
            tags = None
        
        due_at = Card.objects.next_card_due_at(request.user, deck=deck, tags=tags)
        difference = due_at - datetime.datetime.utcnow()
        hours_from_now = difference.days * 24 + difference.seconds / (60 * 60)
        minutes_from_now = difference.days * 24 + difference.seconds / 60
        return {'hours_until_next_card_due': hours_from_now, 'minutes_until_next_card_due': minutes_from_now}


@json_response
@login_required
def next_card_due_at(request):
    '''Returns a human-readable format of the next date that the card is due.'''
    if request.method == 'GET':
        #TODO refactor request parameters somehow
        # Deck.
        try:
            deck_id = int(request.GET.get('deck', -1))
        except ValueError:
            deck_id = -1
        deck = None
        if deck_id != -1:
            try:
                deck = Deck.objects.get(id=deck_id)
            except Deck.DoesNotExist:
                pass #TODO return error instead

        # Tags.
        try:
            tag_id = int(request.GET.get('tag', -1))
        except ValueError:
            tag_id = -1
        if tag_id != -1:
            tag_ids = [tag_id] #TODO support multiple tags
            tags = usertagging.models.Tag.objects.filter(id__in=tag_ids)
        else:
            tags = None
        
        due_at = Card.objects.next_card_due_at(request.user, deck=deck, tags=tags)
        due_at = naturalday(due_at.date())
        return {'next_card_due_at': due_at}


@all_http_methods
def _rest_review_card(request, card_id):
    '''
    '''
    if request.method == 'POST':
        try:
            card = Card.objects.get(id=card_id) #FIXME make sure this user owns this card
            card.review(int(request.POST['grade']))
            return {'success': True}
        except Card.DoesNotExist:
            return {'success': False}



@login_required
@json_response
@all_http_methods
def rest_card(request, card_id): #todo:refactor into facts (no???)
  if request.method == 'GET':
    ret = {}
    try:
      card = Card.objects.get(id=int(card_id))

      #TODO refactor the below into a model - it's not DRY
      reviewed_at = datetime.datetime.utcnow()

      field_contents = dict((field_content.field_type_id, field_content,) for field_content in card.fact.fieldcontent_set.all())
      card_context = {'fields': field_contents}
      due_times = {}
      for grade in [GRADE_NONE, GRADE_HARD, GRADE_GOOD, GRADE_EASY,]:
          due_at = card._next_due_at(grade, reviewed_at, card._next_interval(grade, card._next_ease_factor(grade, reviewed_at), reviewed_at))
          duration = due_at - reviewed_at
          days = duration.days + (duration.seconds / 86400.0)
          due_times[grade] = days
      formatted_card = {
          'id': card.id,
          'fact_id': card.fact_id,
          'front': render_to_string(card.template.front_template_name, card_context),
          'back': render_to_string(card.template.back_template_name, card_context),
          'next_due_at_per_grade': due_times
      }

      return {'success': True, 'card': formatted_card}
      #return to_dojo_data(formatted_card)
    except Card.DoesNotExist:
      return {'success': False}
  elif request.method == 'POST':
    if 'grade' in request.POST:
        # this is a card review
        return _rest_review_card(request, int(card_id))



# Undo stack for card reviews

@json_response
@login_required
def undo_review(request):
    if request.method == 'POST':
        UndoCardReview.objects.undo(request.user)
        return {'success': True}


@json_response
@login_required
def reset_review_undo_stack(request):
    if request.method == 'POST':
        UndoCardReview.objects.reset(request.user)
        return {'success': True}

