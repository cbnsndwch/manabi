# Some views which should be considered part of the REST API are contained 
# in the reviews.py module. This module contains the rest of them.

from apps.utils import japanese
from apps.utils.querycleaner import clean_query
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.forms import forms
from django.forms.models import modelformset_factory, formset_factory
from django.http import Http404, HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext, loader
from django.utils import simplejson
from django.views.decorators.http import require_GET
from django.views.generic.create_update \
    import update_object, delete_object, create_object
from dojango.decorators import json_response
from dojango.util import to_dojo_data, json_decode, json_encode
from flashcards.forms import DeckForm, FactForm, FieldContentForm, CardForm
from flashcards.models import FactType, Fact, Deck, CardTemplate, FieldType
from flashcards.models import FieldContent, Card
from flashcards.models.constants import MAX_NEW_CARD_ORDINAL
from flashcards.views.decorators import all_http_methods
from flashcards.views.decorators import flashcard_api as api
from flashcards.views.decorators import \
    flashcard_api_with_dojo_data as api_dojo_data, \
    ApiException
        
from flashcards.views.decorators import has_card_query_filters
import apps.utils.querycleaner
import random
#import jcconv
from flashcards.views.shortcuts import get_deck_or_404


#FIXME add permissions validation for every method

        
        


@api
def rest_deck_subscribe(request, deck_id):
    print 'rest_deck_subscribe'
    if request.method == 'POST':
        print 'rest_deck_subscribe 0'
        deck = get_deck_or_404(request.user, deck_id)
        print deck.id
        new_deck = deck.subscribe(request.user)
        print new_deck.id
        print new_deck.get_absolute_url()

        return {'deckId': new_deck.id,
                'postRedirect': new_deck.get_absolute_url()}

@api
def rest_generate_reading(request):
    if request.method == 'POST':
        return japanese.generate_reading(request.POST['expression'])

#@api_dojo_data
#def rest_decks(request):
#    #if request.method == 'GET':
#    ret = Deck.objects.filter(
#        owner=request.user,
#        active=True).values('id', 'name', 'description')
#    return to_dojo_data(ret, label='name')

@api
def rest_deck(request, deck_id):
    deck = get_deck_or_404(request.user, deck_id)

    if request.method == 'DELETE':
        if deck.subscriber_decks.filter(active=True).exists(): 
            deck.active = False
            deck.save()
        else:
            deck.delete_cascading()
    elif request.method == 'PUT':
        params = clean_query(request.POST, {'shared': bool})
        # change shared status
        if params.get('shared') is not None:
            if params['shared']:
                if deck.synchronized_with:
                    raise ApiException
                deck.share()
            else:
                if not deck.shared:
                    raise ApiException
                deck.unshare()
        return {'shared': deck.shared}

@api
def rest_deck_name(request, deck_id):
    deck = get_deck_or_404(request.user, deck_id)

    if request.method == 'GET':
        return deck.name
    elif request.method == 'POST':
        deck.name = request.POST['name']
        deck.save()

@api
def rest_deck_description(request, deck_id):
    deck = get_deck_or_404(request.user, deck_id)

    if request.method == 'GET':
        return deck.description
    elif request.method == 'POST':
        deck.description = request.POST['description']
        deck.save()


@api_dojo_data
def rest_card_templates(request, fact_type_id):
    '''Returns list of CardTemplate objects given a parent FactType id'''
    fact_type = get_object_or_404(FactType, pk=fact_type_id)
    return to_dojo_data(fact_type.cardtemplate_set.all())


@api_dojo_data
def rest_fields(request, fact_type_id):
    '''Returns list of Field objects given a FactType id'''
    fact_type = get_object_or_404(FactType, pk=fact_type_id)
    return to_dojo_data(fact_type.fieldtype_set.all().order_by('ordinal'))

@api_dojo_data
def rest_fact_types(request):
    return to_dojo_data(FactType.objects.all())




@api_dojo_data
def rest_cards(request): #todo:refactor into facts (no???)
    '''
    Returns the cards for a given fact. Accepts `fact` in the GET params.
    '''
    if request.GET['fact']:
        fact = get_object_or_404(Fact, pk=request.GET['fact'])
        return to_dojo_data(fact.card_set.get_query_set())


@api_dojo_data
def rest_card_templates_for_fact(request, fact_id):
    '''
    Returns a list of card templates for which the given fact 
    has corresponding cards activated.
    '''
    fact = get_object_or_404(Fact, pk=fact_id)
    activated_card_templates = list(
        e.template for e in fact.card_set.filter(active=True))

    card_templates = []
    for card_template in fact.fact_type.cardtemplate_set.all():
        #TODO only send the id(uri)/name/status
        card_templates.append({
            'card_template': card_template,
            'activated_for_fact': 
                (card_template in activated_card_templates),
        })
    return to_dojo_data(card_templates, identifier=None)


@login_required
@require_GET
def rest_facts_tags(request):
    '''
    Returns a JSON list of tags. Nothing more.
    '''
    term = request.GET.get('term', None)
    tags = Fact.objects.all_tags_per_user(request.user)
    ret = [tag.name for tag in tags if (term and tag.name.startswith(term))]
    return HttpResponse(simplejson.dumps(ret), mimetype='application/json')

    #TODO we can use `term` which jquery's autocomplete gives us to search prefixes -- an optimization
    #for now we just give back all the tags
    #term = request.GET.get('term', None)

    #tags = [{'name': tag.name, 'id': tag.id} for tag in tags]
    #return to_dojo_data(tags)


@api_dojo_data
@has_card_query_filters
@transaction.commit_on_success
#TODO refactor into facts (no???)
def rest_facts(request, deck=None, tags=None): 
    if request.method == 'GET':
        ret = []
        if request.GET['fact_type']:
            #TODO allow omitting this option
            fact_type_id = request.GET['fact_type'] 
            fact_type = get_object_or_404(FactType, pk=fact_type_id)

            user = deck.owner if deck else request.user

            facts = Fact.objects.with_upstream(
                user, deck=deck, tags=tags).filter(active=True)

            #is the user searching his facts?
            if ('search' in request.GET
                    and request.GET['search'].strip()):
                search_query = request.GET['search']
                facts = Fact.objects.search(
                    fact_type, search_query, query_set=facts)
                #FIXME add search for synchronized facts too!

            for fact in facts.iterator():
                row = {
                    'fact-id': fact.id, 
                    'suspended':
                        (len(fact.card_set.filter(active=True)) and
                            all([card.suspended for card
                                in fact.card_set.filter(active=True)])),
                }

                ident, name = '', ''
                for field_content in fact.field_contents:
                    #TODO rename to be clearer, like field_id, or ???
                    key = 'id{0}'.format(field_content.field_type_id) 

                    if not ident:
                        ident = key
                    elif not name:
                        name = key

                    row[key] = field_content.human_readable_content
                    row['{0}_field-content-id'.format(key)] = \
                        field_content.id

                if not name:
                    name = ident

                ret.append(row)
            ret = to_dojo_data(ret)
            ret['identifier'] = 'fact-id'
            #ret['name'] = name #todo:for <2 cols/fields...?
            return ret
    elif request.method == 'POST':
        # Create fact in deck, including its fields and cards. POST method.
        #TODO unicode support
        #TODO refactor into other module probably
        ret = {}
        #TODO just get this from the form
    
        deck = get_deck_or_404(request.user, request.POST['fact-deck'])

        # Override the submitted deck ID with the ID from the URL, 
        # since this is a RESTful interface.
        post_data = request.POST.copy()
        #post_data['fact-deck'] = deck_id
    
        #todo: refactor this into model code
    
        #CardFormset = modelformset_factory(Card, exclude=('fact', 'ease_factor', )) #TODO make from CardForm
        #card_formset = CardFormset(post_data, prefix='card')
        card_templates = CardTemplate.objects.filter(id__in=[e[1] for e in post_data.items() if e[0].find('card_template') == 0])
    
        #FieldContentFormset = modelformset_factory(FieldContent, exclude=('fact', ))
        FieldContentFormset = modelformset_factory(
            FieldContent, form=FieldContentForm)
        field_content_formset = FieldContentFormset(
            post_data, prefix='field_content')
    
        fact_form = FactForm(post_data, prefix='fact')
    
        if field_content_formset.is_valid() and fact_form.is_valid():
            #TODO automate the tag saving in forms.py
            new_fact = fact_form.save() 
            new_fact.active = True
            new_fact.save()

            # maps subfact group numbers to the subfact object
            group_to_subfact = {} 
            for field_content_form in field_content_formset.forms:
                #TODO don't create fieldcontent objects for 
                # optional fields which were left blank.
                new_field_content = field_content_form.save(commit=False)
                # is this a field of the parent fact, or a subfact?
                if (new_field_content.field_type.fact_type
                    == new_fact.fact_type):
                    # parent fact
                    new_field_content.fact = new_fact
                else:
                    # subfact
                    group = field_content_form\
                            .cleaned_data['subfact_group']
                    if group not in group_to_subfact.keys():
                        # create the new subfact
                        new_subfact = Fact(
                                fact_type=new_field_content\
                                          .field_type.fact_type,
                                active=True,
                                #deck=new_fact.deck,
                                parent_fact=new_fact,
                        )
                        new_subfact.save()
                        group_to_subfact[group] = new_subfact
                    new_field_content.fact = group_to_subfact[group]
                new_field_content.save()
        
            for card_template in card_templates: 
                #card_form in card_formset.forms:
                new_card = Card(
                    template=card_template,
                    fact=new_fact,
                    active=True,
                    new_card_ordinal=random.randrange(
                        0, MAX_NEW_CARD_ORDINAL),
                    priority = 0)
                new_card.save()
        else:
            raise ApiException({
                #'card': card_formset.errors,
                'field_content': field_content_formset.errors,
                'fact': [fact_form.errors]
            })
        return ret

@api
@transaction.commit_on_success
def rest_fact_suspend(request, fact_id):
    if request.method == 'POST':
        Fact.objects.get_for_owner_or_subscriber(
            fact_id, request.user).suspend()

@api
@transaction.commit_on_success
def rest_fact_unsuspend(request, fact_id):
    if request.method == 'POST':
        Fact.objects.get_for_owner_or_subscriber(
            fact_id, request.user).unsuspend()

@api
@transaction.commit_on_success
def rest_fact(request, fact_id): #todo:refactor into facts
    if request.method == 'PUT':
        # Update fact
        ret = {}
        #FIXME make sure the logged-in user owns this FACT

        #override the submitted deck ID with the ID from the URL, since this is a RESTful interface
        post_data = request.POST.copy()

        #todo: refactor this into model code
        
        # if this fact is a shared fact which the current subscribing user hasn't copied yet, copy it first
        fact = Fact.objects.get_for_owner_or_subscriber(fact_id, request.user)

        #fact_form = FactForm(post_data, prefix='fact', instance=fact)
        FactFormset = modelformset_factory(Fact, fields=('id', 'fact_type',), can_delete=True)
        fact_formset = FactFormset(post_data, prefix='fact', queryset=Fact.objects.filter(id=fact.id)|fact.subfacts)
        
        #TODO make from CardForm
        CardFormset = modelformset_factory(
            Card, exclude=('fact', 'ease_factor', )) 
        card_formset = CardFormset(
            post_data, prefix='card',
            queryset=fact.card_set.get_query_set())
        
        FieldContentFormset = modelformset_factory(
            FieldContent, form=FieldContentForm)
        field_content_queryset = (fact.fieldcontent_set.get_query_set() 
                                  or None)
        field_content_formset = FieldContentFormset(
            post_data, prefix='field_content') 
        #, queryset=field_content_queryset)

        #fact_form = FactForm(post_data, prefix='fact', instance=fact)
        # ^^^^^^^ this isn't updated
        if (card_formset.is_valid()
                and field_content_formset.is_valid()
                and fact_formset.is_valid()):
            #fact = fact_form.save() #TODO needed in future?
            
            #update the fact's assigned deck
            #FIXME catch error if does not exist
            #deck_id = int(post_data['fact-deck'])
            #fact.deck = Deck.objects.get(id=deck_id)
            #fact.save()

            # maps subfact group numbers to the subfact object
            group_to_subfact = {} 
            for field_content_form in field_content_formset.forms:
                field_content = field_content_form.save(commit=False)

                # is this a field of the parent fact, or a subfact?
                if field_content.field_type.fact_type == fact.fact_type:
                    # Parent fact.
                    field_content.fact = fact
                    field_content.save()
                else:
                    # Subfact.
                    # Does this subfact already belong to the user?
                    # If not, create it, only if anything's changed.
                    # Or, create it, if it's new.
                    if field_content_form.cleaned_data['id']:
                        # existing field content

                        # if it's part of a subfact that's being 
                        # deleted in this form, ignore the field.
                        if field_content_form.cleaned_data['id'].fact in\
                            [fact_form.cleaned_data['id'] for fact_form
                             in fact_formset.deleted_forms]:
                            continue

                        if field_content_form.cleaned_data['id'].fact.owner == request.user:
                            field_content.fact = field_content_form.cleaned_data['id'].fact #TODO is this necessary?
                            field_content.save()
                        else:
                            original = field_content_form.cleaned_data['id']
                            if field_content_form['content'] != original.content:
                                # user updated subscribed subfact content - so create his own subscriber subfact to hold it
                                new_subfact = original.fact.copy_to_parent_fact(fact, copy_field_contents=True)
                                new_field_content = new_subfact.fieldcontent_set.get(field_type=field_content_form.cleaned_data['field_type'])
                                new_field_content.content = field_content_form.cleaned_data['content']
                                new_field_content.save()
                            else:
                                # not user's own, but he didn't update it anyway
                                pass
                    else:
                        # new field content
                        # this means new subfact.
                        # otherwise, this doesn't make sense unless the subfact model changed - which isn't supported yet.
                        # or subscriber fields are optimized to not copy over until modified
                        group = field_content_form.cleaned_data['subfact_group']
                        if group not in group_to_subfact.keys():
                            # create the new subfact
                            new_subfact = Fact(
                                    fact_type=field_content.field_type.fact_type,
                                    active=True,
                                    parent_fact=fact
                            )
                            new_subfact.save()
                            group_to_subfact[group] = new_subfact
                        field_content.fact = group_to_subfact[group]
                        field_content.save()


            # delete any subfacts as needed
            for subfact_form in fact_formset.deleted_forms:
                subfact = subfact_form.cleaned_data['id']
                # make sure it's a subfact
                if subfact.parent_fact:# == fact:
                    if subfact.synchronized_with or subfact.parent_fact != fact:
                        # this is a subscriber fact
                        if subfact.synchronized_with:
                            subfact.active = False
                            subfact.save()
                        else:
                            # the user doesn't have his own copy of this subfact yet
                            new_subfact = subfact.copy_to_parent_fact(fact, copy_field_contents=False)
                            new_subfact.active = False
                            new_subfact.save()
                    else:
                        subfact.delete()


            # disable any existing cards that weren't selected in the update, or enable if selected and create if needed
            # do all this for subscribers too, if this is in a shared deck
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
        else:
            raise ApiException({
                'card': card_formset.errors,
                'fact': fact_formset.errors,
                'field_content': field_content_formset.errors,
            })
        return ret
    elif request.method == 'DELETE':
        fact = Fact.objects.get_for_owner_or_subscriber(fact_id, request.user)
        if fact.synchronized_with:
            fact.active = False
            fact.save()
        else:
            fact.delete()


