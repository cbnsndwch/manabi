from django.db import models
from django.contrib.auth.models import User
from django.forms import ModelForm
from django.forms.util import ErrorList
from dbtemplates.models import Template
from django.db.models import Avg

import random
from django.db import transaction

from itertools import chain

from fields import FieldContent, SharedFieldContent
import cards
from facts import Fact, SharedFact

import usertagging


class DeckManager(models.Manager):
    def values_of_all_with_stats_and_totals(self, user, fields=None):
        '''
        Returns all decks of a user (as a list of dictionaries), 
        with stats for each deck, 
        and an "All decks" item on top with totals
        '''
        decks = self.filter(owner=user).order_by('name').values() #TODO fields
        if fields:
            decks = decks.values(*fields)
        deck_values = []
        for deck in decks:
            #add stats for each deck
            deck_instance = Deck.objects.get(id=deck['id'])
            for property in ['card_count', 'due_card_count', 'new_card_count']:
                deck[property] = getattr(deck_instance, property)
            deck_values.append(deck)

        #add "All decks" top item with totals
        #TODO optimize by keeping totals above
        all_decks_option = {'id': -1, 
                            'name': 'All decks',
                            'card_count': cards.Card.objects.of_user(user).count(),
                            'due_card_count': cards.Card.objects.cards_due_count(user),
                            'new_card_count': cards.Card.objects.cards_new_count(user)}

        deck_values.insert(0, all_decks_option)

        return deck_values


#TODO use this
class Textbook(models.Model):
    name = models.CharField(max_length=100)
    edition = models.CharField(max_length=50, blank=True)
    description = models.TextField(max_length=2000, blank=True)
    purchase_url = models.URLField(blank=True) #TODO amazon referrals
    isbn = models.CharField(max_length=20, blank=True)
    cover_picture = models.FileField(upload_to='/textbook_media/', null=True, blank=True)
    #TODO student level field

    class Meta:
        app_label = 'flashcards'

    def __unicode__(self):
        return self.name


class AbstractDeck(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(max_length=2000, blank=True)
    owner = models.ForeignKey(User, db_index=True)

    textbook_source = models.ForeignKey(Textbook, null=True, blank=True)

    picture = models.FileField(upload_to='/deck_media/', null=True, blank=True) #TODO upload to user directory, using .storage

    priority = models.IntegerField(default=0, blank=True)

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    modified_at = models.DateTimeField(auto_now=True, editable=False)

    def get_absolute_url(self):
        return '/flashcards/decks/{0}'.format(self.id)
    

    class Meta:
        app_label = 'flashcards'
        abstract = True

    @property
    def card_count(self):
        return cards.Card.objects.of_user(self.owner).count()


class SharedDeck(AbstractDeck):
    downloads = models.PositiveIntegerField(default=0, blank=True)

    def __unicode__(self):
        return self.name
    
    class Meta:
        app_label = 'flashcards'
        #TODO unique_together = (('owner', 'name'), )

    #FIXME delete cascading
    
usertagging.register(SharedDeck)


class Deck(AbstractDeck):
    #manager
    objects = DeckManager()

    def __unicode__(self):
        return self.name
    
    class Meta:
        app_label = 'flashcards'
        #TODO unique_together = (('owner', 'name'), )
    

    @property
    def new_card_count(self):
        return cards.Card.objects.cards_new_count(self.owner, deck=self)

    @property
    def due_card_count(self):
        return cards.Card.objects.cards_due_count(self.owner, deck=self)

    def average_ease_factor(self):
        deck_cards = cards.Card.objects.filter(id__in=self.fact_set.all(), active=True, suspended=False, ease_factor__isnull=False)
        if deck_cards.count():
            average_ef = deck_cards.aggregate(average_ease_factor=Avg('ease_factor'))['average_ease_factor']
            if average_ef:
                return average_ef
        return 2.5
    
    @transaction.commit_on_success    
    def delete_cascading(self):
        for fact in self.fact_set.all():
            for card in fact.card_set.all():
                card.delete()
            fact.delete()
        self.schedulingoptions.delete()
        self.delete()

usertagging.register(Deck)



class SchedulingOptions(models.Model):
    deck = models.OneToOneField(Deck)
    
    mature_unknown_interval_min = models.FloatField(default=0.333)
    mature_unknown_interval_max = models.FloatField(default=0.333)
    unknown_interval_min = models.FloatField(default=20.0/(24.0*60.0))  # 
    unknown_interval_max = models.FloatField(default=25.0/(24.0*60.0))  #TODO more? 0.5)
    hard_interval_min = models.FloatField(default=0.333)       #  8 hours
    hard_interval_max = models.FloatField(default=0.5)         # 12 hours
    medium_interval_min = models.FloatField(default=3.0)       #  3 days
    medium_interval_max = models.FloatField(default=5.0)       #  5 days
    easy_interval_min = models.FloatField(default=7.0)         #  7 days
    easy_interval_max = models.FloatField(default=9.0)         #  9 days

    def __unicode__(self):
        return self.deck.name

    class Meta:
        app_label = 'flashcards'
    
    #TODO should be classmethod
    def _generate_interval(self, min_duration, max_duration):
        return random.uniform(min_duration, max_duration) #TODO favor (random.triangular) conservatism

    def initial_interval(self, grade, do_fuzz=True):
        '''
        Generates an initial interval duration for a new card that's been reviewed.
        '''
        if grade == cards.GRADE_NONE:
            min, max = self.unknown_interval_min, self.unknown_interval_max
        if grade == cards.GRADE_HARD:
            min, max = self.hard_interval_min, self.hard_interval_max
        elif grade == cards.GRADE_GOOD:
            min, max = self.medium_interval_min, self.medium_interval_max
        elif grade == cards.GRADE_EASY:
            min, max = self.easy_interval_min, self.easy_interval_max
        
        if do_fuzz:
            return self._generate_interval(min, max)
        else:
            return (min + max) / 2.0




@transaction.commit_on_success    
def share_deck(deck):
    '''Creates a SharedDeck containing all the facts and cards and their contents, given a user's Deck.''' 
    
    #copy the deck
    shared_deck = SharedDeck(
        name=deck.name,
        description=deck.description,
        #TODO implement textbook_source=deck.textbook_source, #TODO picture too
        priority=deck.priority,
        owner_id=deck.owner_id)
    shared_deck.save()

    # Copy the tags
    shared_deck.tags = usertagging.utils.edit_string_for_tags(deck.tags)

    #copy the facts and child facts
    fact_to_shared_fact = {} #maps fact to shared_fact
    for fact in chain(deck.fact_set.all(), Fact.objects.filter(parent_fact__deck=deck)):
        if fact.parent_fact:
            #child fact
            shared_fact = SharedFact(
                fact_type=fact.fact_type,
                active=fact.active) #TODO should it be here?
            shared_fact.save()
            shared_fact.parent_fact = fact_to_shared_fact[fact.parent_fact]
        else:
            #regular fact
            shared_fact = SharedFact(
                deck=shared_deck,
                fact_type_id=fact.fact_type_id,
                active=fact.active, #TODO should it be here?
                priority=fact.priority,
                notes=fact.notes)
            shared_fact.save()
            fact_to_shared_fact[fact] = shared_fact

        #copy the field contents for this fact
        for field_content in fact.fieldcontent_set.all():
            shared_field_content = SharedFieldContent(
                fact=shared_fact,
                field_type_id=field_content.field_type_id,
                content=field_content.content,
                cached_transliteration_without_markup=field_content.cached_transliteration_without_markup,
                media_uri=field_content.media_uri,
                media_file=field_content.media_file)
            shared_field_content.save()

        #copy the cards
        for card in fact.card_set.filter(active=True):
            shared_card = cards.SharedCard(
                fact=shared_fact,
                template=card.template,
                priority=card.priority,
                leech=card.leech,
                active=True,#card.active,
                suspended=card.suspended,
                new_card_ordinal=card.new_card_ordinal)
            shared_card.save()

    #done!
    return shared_deck


@transaction.commit_on_success    
def download_shared_deck(user, shared_deck):
    '''Copies a shared deck and all its contents to a user's own deck library.'''

    #copy the deck
    deck = Deck(
        name=shared_deck.name,
        description=shared_deck.description,
        #TODO implement textbook=shared_deck.textbook, #picture too...
        priority=shared_deck.priority,
        owner_id=user.id)
    deck.save()

    # Copy the tags
    deck.tags = usertagging.utils.edit_string_for_tags(shared_deck.tags)

    #create default deck scheduling options
    scheduling_options = SchedulingOptions(deck=deck)
    scheduling_options.save()

    #copy the facts
    shared_fact_to_fact = {}
    for shared_fact in chain(shared_deck.sharedfact_set.all(), SharedFact.objects.filter(parent_fact__deck=shared_deck)):
        if shared_fact.parent_fact:
            #child fact
            fact = Fact(
                fact_type=shared_fact.fact_type,
                active=shared_fact.active) #TODO should it be here?
            fact.parent_fact = shared_fact_to_fact[shared_fact.parent_fact]
            fact.save()
        else:
            #regular fact
            fact = Fact(
                deck=deck,
                fact_type_id=shared_fact.fact_type_id,
                active=shared_fact.active, #TODO should it be here?
                priority=shared_fact.priority,
                notes=shared_fact.notes)
            fact.save()
            shared_fact_to_fact[shared_fact] = fact

        #copy the field contents for this fact
        for shared_field_content in shared_fact.sharedfieldcontent_set.all():
            field_content = FieldContent(
                fact=fact,
                field_type_id=shared_field_content.field_type_id,
                content=shared_field_content.content,
                cached_transliteration_without_markup=shared_field_content.cached_transliteration_without_markup,
                media_uri=shared_field_content.media_uri,
                media_file=shared_field_content.media_file)
            field_content.save()
                                                      
        #copy the cards
        for shared_card in shared_fact.sharedcard_set.filter(active=True):
            card = cards.Card(
                fact=fact,
                template_id=shared_card.template_id,
                priority=shared_card.priority,
                leech=shared_card.leech,
                active=True,# shared_card.active,
                suspended=shared_card.suspended,
                new_card_ordinal=shared_card.new_card_ordinal)
            card.save()

    #done!
    return deck

