from django.db import models
from django.contrib.auth.models import User
from django.forms import ModelForm
from django.forms.util import ErrorList
from dbtemplates.models import Template
from itertools import chain

import random

import datetime

from facts import Fact, FactType, SharedFact
from cardtemplates import CardTemplate

from django.template.loader import render_to_string

#grade IDs (don't change these once they're set)
GRADE_NONE = 0
#GRADE_BAD = 1
#GRADE_MISTAKE = 2
GRADE_HARD = 3
GRADE_GOOD = 4
GRADE_EASY = 5

#below is used in the EF equation, but we're going to precompute the EF factors
#GRADE_FACTORS = {GRADE_NONE: 0, GRADE_HARD: 3, GRADE_GOOD: 4, GRADE_EASY: 5}

#this is the EF algorithm from which the EF factors are computed:
#ease_factor = self.ease_factor + (0.1 - (max_grade - grade_factor) * (0.08 + (max_grade - grade_factor) * 0.02))

#constants:
#max_grade = 3
#MAX_EASE_FACTOR_STEP = 0.1

#these are the precomputed values, so that we can modify them independently later to test their effectiveness:
EASE_FACTOR_MODIFIERS = {GRADE_NONE: -0.3, GRADE_HARD: -0.1401, GRADE_GOOD: 0.0, GRADE_EASY: 0.1} #FIXME accurate grade_none value

MINIMUM_EASE_FACTOR = 1.3

YOUNG_FAILURE_INTERVAL = (1.0 / (24.0 * 60.0)) * 10.0 #10 mins, expressed in days
#MATURE_FAILURE_INTERVAL = (1.0 / (24 * 60)) * 10 #10 mins, expressed in days
MATURE_FAILURE_INTERVAL = 1.0 #1 day#(1.0 / (24 * 60)) * 10 #10 mins, expressed in days
#TODO MATURE_FAILURE_INTERVAL should not be a constant value, but dependent on other factors of a given card
#TODO 'tomorrow' should also be dependent on the current time, instead of just 1 day from now

MATURE_INTERVAL_MIN = 20 #days an interval is required to meet or exceed for a card to be considered mature

GRADE_EASY_BONUS_FACTOR = 0.2
DEFAULT_EASE_FACTOR = 2.5

#TODO make _next_interval/ease_factor into class methods?


NEW_CARDS_PER_DAY = 20 #TODO this should at least be an option, but should also scale to use

#number of failed cards before failed cards are shown earlier than any due cards
#TODO MAX_FAILED_CARDS = 20 #TODO should be option.

#show failed cards in 10 mins, but if all due are done and timer/quota isn't, show early

# 1: mature due (-interval)
# 2: young due
# 3: failed, not due




class CardManager(models.Manager):
    
    ##set the base query set to only include cards of this user
    #def get_query_set(self):
    #    return super(UserCardManager, self).get_query_set().filter(

    def of_user(self, user):
        #TODO this is probably really slow
        return self.filter(fact__deck__owner=user)

    def new_cards(self, user, deck=None):
        new_cards = self.filter(fact__deck__owner=user, due_at__isnull=True)
        if deck:
            new_cards = new_cards.filter(fact__deck=deck)
        return new_cards

    #def failed_cards(self):
    #    failed_cards = self.filter(last_review_grade=GRADE_NONE)

    #def mature_cards(self):
    #    return self.filter(interval__gt=MATURE_INTERVAL_MIN)

    def cards_new_count(self, user, deck=None):
        new_cards_count = len(self.new_cards(user, deck)) #TODO refactor, make this faster (use aggregate)
        return new_cards_count

    def cards_due_count(self, user, deck=None):
        due_cards_count = len(self.due_cards(user, deck)) #TODO refactor, make this faster (use aggregate)
        return due_cards_count

    def due_cards(self, user, deck=None):
        #TODO Define an ordering
        # possible orderings:
        #   due date
        #   priorities, then due date
        #   taking maturity levels into account
        due_cards = self.filter(fact__deck__owner=user, due_at__lt=datetime.datetime.utcnow())#FIXME

        if deck:
            due_cards = due_cards.filter(fact__deck=deck)

        ordered_cards = due_cards.order_by('-interval')

        return ordered_cards

    def next_cards(self, user, count, excluded_ids, session_start, deck=None):
        '''
        Returns {count} cards to be reviewed, in order.
        The return format is a list of dictionaries.
        '''
        card_queries = []
        now = datetime.datetime.utcnow()

        user_cards = self.of_user(user)


        if excluded_ids:
            user_cards = user_cards.exclude(id__in=excluded_ids)

        #due cards
        due_cards = user_cards.filter(due_at__lte=now).order_by('-interval')
        card_queries.append(due_cards)

        #followed by failed, not due, but not if this isn't the start of a review session
        #FIXME decide what to do with this #if session_start:
        failed_not_due_cards = user_cards.filter(last_review_grade=GRADE_NONE, due_at__gt=now).order_by('due_at')
        card_queries.append(failed_not_due_cards)

        #FIXME add new cards into the mix
        #for now, we'll add new ones to the end
        new_cards = user_cards.filter(due_at__isnull=True).order_by('new_card_ordinal')
        card_queries.append(new_cards)

        card_queries_ret = []
        cards_left = count
        for card_query in card_queries:
            if cards_left > 0:
                if deck:
                    card_query = card_query.filter(fact__deck=deck)

                card_query_limited = card_query[:cards_left]
                if len(card_query_limited) > 0:
                    card_queries_ret.append(card_query_limited)
                    cards_left -= len(card_query_limited)

        return chain(*card_queries_ret) #chain(due_cards, failed_not_due_cards, new_cards)


#used for randomizing new card insertion
MAX_NEW_CARD_ORDINAL = 10000000
                      #4294967295


class AbstractCard(models.Model):
    template = models.ForeignKey(CardTemplate)

    #TODO how to have defaults without null (gives a 'may not be NULL' error)
    priority = models.IntegerField(default=0, null=True, blank=True) #negatives for lower priority, positives for higher
    
    leech = models.BooleanField() #TODO add leech handling
    
    active = models.BooleanField(default=True) #False when the card is removed from the Fact. This way, we can keep card statistics if enabled later
    suspended = models.BooleanField(default=False) #Not used right now. 'active' is more like a deletion, this is lighter

    new_card_ordinal = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        app_label = 'flashcards'
        abstract = True
    

class SharedCard(AbstractCard):
    fact = models.ForeignKey(SharedFact)
    
    class Meta:
        unique_together = (('fact', 'template'), )
        app_label = 'flashcards'


class Card(AbstractCard):
    #manager
    objects = CardManager()

    fact = models.ForeignKey(Fact)
    
    synchronized_with = models.ForeignKey('self', null=True, blank=True) #for owner cards, part of synchronized decks, not used yet

    ease_factor = models.FloatField(null=True, blank=True)
    interval = models.FloatField(null=True, blank=True) #days
    due_at = models.DateTimeField(null=True, blank=True) #null means this card is 'new'
    
    last_ease_factor = models.FloatField(null=True, blank=True)
    last_interval = models.FloatField(null=True, blank=True)
    last_due_at = models.DateTimeField(null=True, blank=True)

    last_reviewed_at = models.DateTimeField(null=True, blank=True)
    last_review_grade = models.PositiveIntegerField(null=True, blank=True)
    
    
    class Meta:
        unique_together = (('fact', 'template'), )
        app_label = 'flashcards'


    def __unicode__(self):
        field_content = dict((field_content.field_type_id, field_content.content,) for field_content in self.fact.fieldcontent_set.all())
        card_context = {'fields': field_content}
        front = render_to_string(self.template.front_template_name, card_context)
        back = render_to_string(self.template.back_template_name, card_context)
        return u'{0} | {1}'.format(front, back)


    def save(self):
        self.new_card_ordinal = random.randrange(0, MAX_NEW_CARD_ORDINAL)
        super(Card, self).save()


    def is_new(self):
        ''''Returns True if this is a new card.'''
        return self.due_at is None

    
    def is_mature(self):
        return self.interval >= MATURE_INTERVAL_MIN


    def is_due(self):
        '''Returns True if this card's due date is in the past.'''
        return self.due_at < datetime.datetime.utcnow()


    def _next_interval(self, grade, ease_factor):
        '''Returns an interval, measured in days.'''
        if self.interval is None: #self.is_new(): #TODO verify this is a good approach
            #get this card's deck, which has the initial interval durations
            #(initial intervals are configured at the deck level)
            interval = self.fact.deck.schedulingoptions.initial_interval(grade)
        elif self.last_review_grade == GRADE_NONE: #card was already failing
            #TODO treat mature failed cards differently
            interval = self.fact.deck.schedulingoptions.initial_interval(grade)
        else:
            if grade == GRADE_NONE:
                #review failure
                #reset the interval to an initial value
                #TODO how to handle failures on new cards? should it keep its 'new' status, and should the EF change?
                if self.is_mature():
                    #failure on a mature card
                    interval = MATURE_FAILURE_INTERVAL
                else:
                    #failure on a young or new card
                    #reset the interval
                    interval = YOUNG_FAILURE_INTERVAL
            else:
                interval = self.interval * ease_factor

                if grade == GRADE_EASY:
                    interval += interval * GRADE_EASY_BONUS_FACTOR
                    
        return interval
   

    def _next_ease_factor(self, grade):
        if self.ease_factor is None:#self.is_new() or self: #TODO verify this is a good approach
            #default to the average for this deck
            #FIXME card.deck. how 2 average???
            ease_factor = DEFAULT_EASE_FACTOR + EASE_FACTOR_MODIFIERS[grade] #temp solution
        else:
            #if grade == GRADE_NONE:
            if self.last_review_grade == GRADE_NONE:
                #if this was already a failed card, don't continue to make ease factor harder, (for young cards only?)
                ease_factor = self.ease_factor
            else:
                ease_factor = self.ease_factor + EASE_FACTOR_MODIFIERS[grade]

        if ease_factor < MINIMUM_EASE_FACTOR:
            ease_factor = MINIMUM_EASE_FACTOR

        return ease_factor


    def _update_statistics(self, grade, reviewed_at):
        #TODO update CardStatistics
        card_history_item = CardHistory(card=self, response=grade, reviewed_at=reviewed_at)
        card_history_item.save()


    def _next_due_at(self, grade, reviewed_at, interval):
        return reviewed_at + datetime.timedelta(days=interval)

    
    def review(self, grade):
        #if grade == GRADE_NONE:
        #    #review failure
        #    #don't affect the ease factor
        #    #reset the interval to an initial value
        #    #TODO how to handle failures on new cards? should it keep its 'new' status, and should the EF change?
        #    if self.is_mature():
        #        #failure on a mature card
        #        self.interval = MATURE_FAILURE_INTERVAL
        #    else:
        #        #failure on a young or new card
        #        #reset the interval
        #        self.interval = YOUNG_FAILURE_INTERVAL
        #    self.due_at = datetime.datetime.utcnow() + self.interval
        #else:

        reviewed_at = datetime.datetime.utcnow()

        #adjust ease factor
        last_ease_factor = self.ease_factor
        self.ease_factor = self._next_ease_factor(grade)
        self.last_ease_factor = last_ease_factor

        #adjust interval
        last_interval = self.interval
        self.interval = self._next_interval(grade, self.ease_factor)
        self.last_interval = last_interval
    
        #determine next due date
        self.last_due_at = self.due_at
        self.due_at = self._next_due_at(grade, reviewed_at, self.interval)

        #update this card's statistics
        self._update_statistics(grade, reviewed_at)

        self.last_review_grade = grade

        #TODO add this review to this card's history
        #self.cardhistory.






#TODO tags or this?
#class CardFlag(models.Model):
#  pass


class CardStatistics(models.Model):
    card = models.ForeignKey(Card)

    success_count = models.PositiveIntegerField(default=0, editable=False)
    failure_count = models.PositiveIntegerField(default=0, editable=False)

    #TODO review stats depending on how card was rated, and how mature it is

    #apparently needed for synchronization/import purposes
    yes_count = models.PositiveIntegerField(default=0, editable=False)
    no_count = models.PositiveIntegerField(default=0, editable=False)

    average_thinking_time = models.PositiveIntegerField(null=True, editable=False)

    #initial_ease 
    
    successive_count = models.PositiveIntegerField(default=0, editable=False) #incremented at each success, zeroed at failure
    successive_streak_count = models.PositiveIntegerField(default=0, editable=False) #incremented at each failure after a success
    average_successive_count = models.PositiveIntegerField(default=0, editable=False) #

    skip_count = models.PositiveIntegerField(default=0, editable=False)
    total_review_time = models.FloatField(default=0) #s
    first_reviewed_at = models.DateTimeField()
    first_success_at = models.DateTimeField()
    
    
    #these take into account short-term memory effects
    #they ignore any more than a single review per day (or 8 hours - TBD)
    #adjusted_review_count = models.PositiveIntegerField(default=0, editable=False)
    #adjusted_success_count = models.PositiveIntegerField(default=0, editable=False)
    #first_adjusted_success_at = models.DateTimeField()
    #failures_in_a_row = models.PositiveIntegerField(default=0, editable=False)
    #adjusted_failures_in_a_row = models.PositiveIntegerField(default=0, editable=False)

    class Meta:
        app_label = 'flashcards'



class CardHistory(models.Model):
    card = models.ForeignKey(Card)
    response = models.PositiveIntegerField(editable=False)
    reviewed_at = models.DateTimeField()

    class Meta:
        app_label = 'flashcards'





