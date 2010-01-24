from django.db import models
from django.contrib.auth.models import User
from django.forms import ModelForm
from django.forms.util import ErrorList
from dbtemplates.models import Template
from itertools import chain

import random

from math import cos, pi

import datetime

from facts import Fact, FactType, SharedFact
from cardtemplates import CardTemplate
from reviews import ReviewStatistics

import usertagging

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

# When intervals are set, they are fuzzed by at most this value, -/+
INTERVAL_FUZZ_MAX = 0.035

NEW_CARDS_PER_DAY = 20 #TODO this should at least be an option, but should also scale to use

#number of failed cards before failed cards are shown earlier than any due cards
#TODO MAX_FAILED_CARDS = 20 #TODO should be option.

#show failed cards in 10 mins, but if all due are done and timer/quota isn't, show early

# 1: mature due (-interval)
# 2: young due
# 3: failed, not due


def timedelta_to_float(timedelta_obj):
    '''Returns a float of days.'''
    return float(timedelta_obj.days) + timedelta_obj.seconds / 86400.0


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

    def due_cards(self, user, deck=None):
        due_cards = self.filter(fact__deck__owner=user, due_at__lte=datetime.datetime.utcnow()).order_by('-interval')
        if deck:
            due_cards = due_cards.filter(fact__deck=deck)
        return due_cards


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


    def _space_cards(self, card_query, count, review_time, excluded_ids=[], early_review=False):
        '''
        Check if any of these are from the same fact,
        or if other cards from their facts have been
        reviewed recently. If so, push their due date up.

        `excluded_ids` is included for avoiding showing sibling 
        cards of cards which the user is already currently reviewing.

        if `early_review` == True:
        Doesn't actually delay cards.
        If all cards in query end up being "spaced", then 
        it will return the spaced cards, since early review
        shouldn't ever run out of cards.
        '''
        delayed_cards = [] # Keep track of new cards we want to skip, since we shouldn't set their due_at (via delay())
        while True:
            cards_delayed = 0
            cards = card_query.exclude(id__in=[card.id for card in delayed_cards])[:count]
            if early_review and len(cards) == 0:
                return delayed_cards[:count]
            for card in cards:
                min_space = card.min_space_from_siblings()
                for sibling_card in card.siblings():
                    if sibling_card.is_due(review_time) \
                            or sibling_card.id in excluded_ids \
                            or (sibling_card.last_reviewed_at \
                            and review_time - sibling_card.last_reviewed_at <= min_space):
                        # Delay the card. It's already sorted by priority, so we delay
                        # this one instead of its sibling.
                        if card.is_new() or early_review:
                            delayed_cards.append(card)
                        else:
                            card.delay(min_space)
                            card.save()
                        cards_delayed += 1
                        break
            if not cards_delayed:
                break
        return cards


    def _next_failed_due_cards(self, initial_query, count, review_time, excluded_ids=[]):
        if not count:
            return []
        cards = initial_query.filter(last_review_grade=GRADE_NONE, due_at__lte=review_time).order_by('due_at')
        return cards[:count] #don't space these #self._space_cards(cards, count, review_time)


    def _next_not_failed_due_cards(self, initial_query, count, review_time, excluded_ids=[]):
        '''
        Returns the first [count] cards from initial_query which are due,
        weren't failed the last review, and  taking spacing of cards from
        the same fact into account.
        
        review_time should be datetime.datetime.utcnow()
        '''
        if not count:
            return []
        due_cards = initial_query.exclude(last_review_grade=GRADE_NONE).filter(due_at__lte=review_time).order_by('-interval')
        #TODO Also get cards that aren't quite due yet, but will be soon, and depending on their maturity (i.e. only mature cards due soon). Figure out some kind of way to prioritize these too.
        return self._space_cards(due_cards, count, review_time)


    def _next_failed_not_due_cards(self, initial_query, count, review_time, excluded_ids=[]):
        if not count:
            return []
        #TODO prioritize certain failed cards, not just by due date
        # We'll show failed cards even if they've been reviewed recently.
        # This is because failed cards are set to be shown 'soon' and not just 
        # in 10 minutes. Special rules.
        #TODO we shouldn't show mature failed cards so soon though!
        card_query = initial_query.filter(last_review_grade=GRADE_NONE, \
                due_at__gt=review_time).order_by('due_at')
        return card_query[:count]


    def _next_new_cards(self, initial_query, count, review_time, excluded_ids=[]):
        if not count:
            return []
        #TODO prioritize certain failed cards, not just by due date
        card_query = initial_query.filter(due_at__isnull=True).order_by('new_card_ordinal')
        new_cards = []
        for card in card_query.iterator(): #TODO iterator() necessary?
            min_space = card.min_space_from_siblings()
            eligible = True
            for sibling_card in card.siblings():
                if sibling_card in new_cards:
                    # sibling card is already included as a new card to be shown - disqualify
                    eligible = False
                    break
                elif sibling_card.id in excluded_ids:
                    # sibling card is currently in the client-side review queue - disqualify
                    eligible = False
                    break
                elif sibling_card.is_due(review_time):
                    # sibling card is due - disqualify
                    eligible = False
                    break
                elif sibling_card.last_reviewed_at:
                    if review_time - sibling_card.last_reviewed_at <= min_space:
                        # sibling card was reviewed recently - disqualify
                        eligible = False
                        break
                elif sibling_card.last_review_grade == GRADE_NONE:
                    # sibling card is failed - disqualify
                    # Either it's due, or it's not due and
                    # it's shown before new cards.
                    eligible = False
                    break
            if eligible:
                new_cards.append(card)
        # Return a query containing the eligible cards.
        eligible_ids = [card.id for card in new_cards]
        return self.filter(id__in=eligible_ids)


    def _next_due_soon_cards(self, initial_query, count, review_time, excluded_ids=[]):
        '''
        Used for early review.
        Ordered by due date.
        '''
        if not count:
            return []
        cards = initial_query.exclude(last_review_grade=GRADE_NONE).filter(due_at__gt=review_time).order_by('due_at')
        return self._space_cards(cards, count, review_time)


    def next_cards(self, user, count, excluded_ids, session_start, deck=None, tags=None, early_review=False):
        '''
        Returns `count` cards to be reviewed, in order.
        count should not be any more than a short session of cards
        set `early_review` to True for reviewing cards early (following any due cards)
        The return format is
        '''
        card_queries = []
        now = datetime.datetime.utcnow()

        user_cards = self.of_user(user)

        if deck:
            user_cards = user_cards.filter(fact__deck=deck)

        if tags:
            facts = usertagging.models.TaggedItem.objects.get_by_model(Fact, tags)
            user_cards = user_cards.filter(fact__in=facts)

        if excluded_ids:
            user_cards = user_cards.exclude(id__in=excluded_ids)

        card_funcs = [
                self._next_failed_due_cards,        #due, failed
                self._next_not_failed_due_cards,    #due, not failed
                self._next_failed_not_due_cards]    #failed, not due

        if early_review:
            card_funcs.extend([self._next_due_soon_cards])      #due soon, not yet, but next in the future
        else:
            card_funcs.extend([self._next_new_cards]) #new cards at end
            #TODO somehow spread some new cards into the early review cards if early_review==True

        cards_left = count
        for card_func in [
                self._next_failed_due_cards,        #due, failed
                self._next_not_failed_due_cards,    #due, not failed
                self._next_failed_not_due_cards,    #failed, not due
                self._next_new_cards]:              #new
            if not cards_left:
                break
            cards = card_func(user_cards, count, now, excluded_ids)
            cards_left -= len(cards)
            if len(cards):
                card_queries.append(cards)

        #FIXME decide what to do with this #if session_start:
        #FIXME add new cards into the mix when there's a defined new card per day limit
        #for now, we'll add new ones to the end
        return chain(*card_queries)



#used for randomizing new card insertion
MAX_NEW_CARD_ORDINAL = 10000000
                      #4294967295 is the upper bound
#FIXME how to order new cards



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
    last_failed_at = models.DateTimeField(null=True, blank=True)
    
    review_count = models.PositiveIntegerField(default=0, editable=False) #TODO use this for is_new()
    
    class Meta:
        unique_together = (('fact', 'template'), )
        app_label = 'flashcards'


    def __unicode__(self):
        from django.utils.html import strip_tags
        field_content = dict((field_content.field_type_id, field_content,) for field_content in self.fact.fieldcontent_set.all())
        card_context = {'fields': field_content}
        front = render_to_string(self.template.front_template_name, card_context)
        back = render_to_string(self.template.back_template_name, card_context)
        return strip_tags(u'{0} | {1}'.format(front, back))


    def save(self):
        self.new_card_ordinal = random.randrange(0, MAX_NEW_CARD_ORDINAL)
        super(Card, self).save()

    @property
    def owner(self):
        return self.fact.deck.owner

    def siblings(self):
        '''Returns the other cards from this card's fact.'''
        return self.fact.card_set.exclude(id=self.id)

    def min_space_from_siblings(self, sibling_cards=None):
        '''
        Calculate the minimum space between this card and its siblings.
        Returns a timedelta.
        '''
        if not sibling_cards:
            sibling_cards = self.fact.card_set.exclude(id=self.id)
        space_factor  = self.fact.fact_type.space_factor
        min_card_space = self.fact.fact_type.min_card_space
        sibling_intervals = [card.interval for card in sibling_cards if card.interval != None]
        if sibling_intervals:
            min_interval  = min(sibling_intervals) #days as float
            min_space = max(self.fact.fact_type.min_card_space, \
                    min_interval * space_factor)
        else:
            min_space = min_card_space
        return datetime.timedelta(days=min_space)

    def is_new(self):
        ''''Returns True if this is a new card.'''
        return self.last_reviewed_at is None #self.due_at is None

    def is_mature(self):
        return self.interval >= MATURE_INTERVAL_MIN

    def is_due(self, time=None):
        '''Returns True if this card's due date is in the past.'''
        if self.is_new():
            return False
        if not self.due_at:
            return False
        if not time:
            time = datetime.datetime.utcnow()
        return self.due_at < time


    def delay(self, delay_duration):
        '''
        This card's due date becomes delay_duration days from now,
        or from its due date if not yet due.
        This is for when this card is due at the same time as a
        sibling card (a card from the same fact).

        delay_duration should be a timedelta
        '''
        now = datetime.datetime.utcnow()
        if self.due_at >= now:
            from_date = self.due_at
        else:
            from_date = now
        self.due_at = from_date + delay_duration


    def _adjustment_curve(self, percentage):
        '''
        Returns adjusted percentage
        where percentage is between 0 and 1
        curve mid_point is between 0 and 1, the x value at which the curve slope rate of change is 0
        '''
        # ((1-cos(.88*pi*.79))/2)/((1-cos(pi*.79))/2)
        upper_x_bound = .79 #midpoint is around .88
        max_value = ((1 - cos(pi * upper_x_bound)))
        return ((1 - cos(percentage * pi * upper_x_bound))) / max_value


    def is_being_learned(self):
        '''Returns whether this card is still being learned.'''
        return self.interval > (self.fact.deck.schedulingoptions.easy_interval_max + INTERVAL_FUZZ_MAX)


    def _last_sibling_review(self):
        last_sibling_review = None
        for sibling in self.siblings():
            if not last_sibling_review \
                    or sibling.last_reviewed_at > last_sibling_review:
                last_sibling_review = sibling.last_reviewed_at
        return last_sibling_review


    def _time_since_last_sibling_review(self):
        '''
        Returns the time elapsed since the latest review of 
        a sibling card.
        '''
        last_sibling_review = self._last_sibling_review()
        return datetime.datetime.utcnow() - last_sibling_review
            

    def _next_interval(self, grade, ease_factor, reviewed_at):
        '''Returns an interval, measured in days.'''
        #TODO shouldnt be a private function, maybe

        # New card.
        if self.interval is None:
            #get this card's deck, which has the initial interval durations
            #(initial intervals are configured at the deck level)
            next_interval = self.fact.deck.schedulingoptions.initial_interval(grade)

            # Lessen the interval if this card is reviewed shortly after a sibling card
            # (for Early Review)
            if grade > GRADE_NONE:
                time_since_last_sibling_review = self._time_since_last_sibling_review()
                if time_since_last_sibling_review \
                        and time_since_last_sibling_review < datetime.timedelta(minutes=60): #TODO don't hardcode here
                    percentage_early = timedelta_to_float(time_since_last_sibling_review) / timedelta_to_float(datetime.timedelta(minutes=60))
                    next_interval *= self._adjustment_curve(percentage_early)
        # Old card.
        else:
            current_interval = self.interval

            # Treat like a new card since it was failed last review.
            if self.last_review_grade == GRADE_NONE:
                #TODO treat mature failed cards differently
                next_interval = self.fact.deck.schedulingoptions.initial_interval(grade)

                # Lessen the effect if this card was reviewed successfully very soon after failing
                if grade > GRADE_NONE:
                    time_since_last_review = reviewed_at - self.last_reviewed_at
                    if time_since_last_review < datetime.timedelta(minutes=60): #TODO don't hard code this value here
                        next_interval /= 1.6 #TODO don't hardcode this here
            else:
                # Review failure.
                if grade == GRADE_NONE:
                    # Reset the interval to an initial value.
                    #TODO how to handle failures on new cards? should it keep its 'new' status, and should the EF change?
                    #TODO handle failures of cards that are reviewed early differently somehow
                    #TODO penalize even worse if it was reviewed early and still failed
                    if self.is_mature():
                        #failure on a mature card
                        next_interval = MATURE_FAILURE_INTERVAL
                    else:
                        #failure on a young or new card
                        #reset the interval
                        next_interval = YOUNG_FAILURE_INTERVAL
                # Successful review.
                else:
                    interval_bonus = 0

                    # Late review.
                    if reviewed_at > self.due_at:
                        # Give a bonus to the current interval for successfully recalling later than due date.
                        interval_bonus = timedelta_to_float(reviewed_at - self.due_at) #(reviewed_at - self.last_reviewed_at)
                        # Less bonus for non-easy grades.
                        if grade == GRADE_HARD:
                            interval_bonus /= 4.0
                        elif grade == GRADE_GOOD:
                            interval_bonus /= 2.0
                        #current_interval += interval_bonus
                        # Cap the bonus.
                        if grade < GRADE_EASY:
                            interval_bonus = min(interval_bonus, timedelta_to_float(datetime.timedelta(4 * current_interval)))

                    current_interval += interval_bonus

                    # Penalize hard grades.
                    if grade == GRADE_HARD:
                        ease_factor = 1.2

                    next_interval = current_interval * ease_factor

                    # Give a bonus for easy grades.
                    if grade == GRADE_EASY:
                        next_interval += next_interval * GRADE_EASY_BONUS_FACTOR

                    # Early review.
                    if reviewed_at < self.due_at:
                        # Lessen the interval increase, proportionate to how early it was reviewed.
                        percentage_early = timedelta_to_float(self.due_at - reviewed_at) \
                                / timedelta_to_float(self.due_at - self.last_reviewed_at) # e.g. if due in 10 days, reviewed in 4, 40%

                        # If reviewed really early, don't add much to the interval.
                        # If reviewed close to due date, add most of the interval.
                        #adjusted_interval_increase = (next_interval - current_interval) * ((1 - cos(percentage_early * pi / 1.5)) / 2)
                        adjusted_interval_increase = (next_interval - current_interval) * self._adjustment_curve(percentage_early)
                        interval = current_interval + adjusted_interval_increase
                        
        # Fuzz the result. Conservatively favor shorter intervals.
        next_interval += next_interval * random.triangular(-INTERVAL_FUZZ_MAX, INTERVAL_FUZZ_MAX, (-INTERVAL_FUZZ_MAX) / 4.5)

        return next_interval


    def _next_ease_factor(self, grade, reviewed_at):
        # New card.
        if self.ease_factor is None:
            # Default to the average for this deck
            next_ease_factor = self.fact.deck.average_ease_factor() + EASE_FACTOR_MODIFIERS[grade]

            # Lessen the ease if this card was reviewed very soon after a sibling card.
            last_sibling_review = self._last_sibling_review()
            if last_sibling_review:
                time_since_last_sibling_review = datetime.datetime.utcnow() - last_sibling_review
                if time_since_last_sibling_review < datetime.timedelta(minutes=60): #TODO don't hardcode here
                    last_sibling_grade = last_sibling_review.last_review_grade

                    percentage_early = timedelta_to_float(time_since_last_sibling_review) / timedelta_to_float(datetime.timedelta(minutes=60))
                    percentage_early = self._adjustment_curve(percentage_early)

                    if grade <= last_sibling_grade:
                        # Rated lower than expected since sibling was reviewed recently,
                        # yet rated higher than this.
                        next_ease_factor -= (1 - percentage_early) * 0.1 #TODO don't hardcode here
                    else:
                        # This was probably rated higher than needed, 
                        # so let's bring it down 1 grade for calculating ease.
                        next_ease_factor = self.fact.deck.average_ease_factor + EASE_FACTOR_MODIFIERS[grade - 1]
        # Old card.
        else:
            # Only make the ease factor harder if the last review grade was better than this review (for young cards only)
            if EASE_FACTOR_MODIFIERS[grade] <= 0 and self.is_being_learned() and grade >= self.last_review_grade:
                #TODO is_being_learned might not cut it for later when mature failures are taken into account (it would return false?)
                next_ease_factor = self.ease_factor
            else:
                next_ease_factor = self.ease_factor + EASE_FACTOR_MODIFIERS[grade]

                # Lessen the effect if this card was reviewed successfully soon after failing
                if grade > GRADE_NONE \
                        and self.last_review_grade == GRADE_NONE \
                        and (reviewed_at - self.last_reviewed_at) < datetime.timedelta(minutes=30): #TODO don't hard code this value here
                    #FIXME lessen it even more if this is an early review due to spacing from siblings
                    #TODO different adjustment for 'hard' grades vs good/too easy
                    percentage_early = timedelta_to_float(reviewed_at - self.last_reviewed_at) \
                            / timedelta_to_float(datetime.timedelta(minutes=60)) #force it to be under 50%
                    adjustment = (next_ease_factor - self.ease_factor) * self._adjustment_curve(percentage_early)
                    next_ease_factor = self.ease_factor + adjustment
                # Early Review, and not right after a failure (failure reviews will often be 'early').
                elif reviewed_at < self.due_at and self.last_review_grade != GRADE_NONE:
                    # Lessen the EF adjustment, proportionate to how early it was reviewed.
                    percentage_early = timedelta_to_float(self.due_at - reviewed_at) \
                            / timedelta_to_float(self.due_at - self.last_reviewed_at) # e.g. if due in 10 days, reviewed in 4, 40% (so actually kind of inverse)
                    # If reviewed really early, don't add much to the interval.
                    # If reviewed close to due date, add most of the interval.
                    adjustment = (next_ease_factor - self.ease_factor) * self._adjustment_curve(percentage_early)
                    next_ease_factor = self.ease_factor + adjustment

        if next_ease_factor < MINIMUM_EASE_FACTOR:
            next_ease_factor = MINIMUM_EASE_FACTOR
        return next_ease_factor


    def _update_statistics(self, grade, reviewed_at):
        '''Updates this card's stats. Call this for each review.'''
        #TODO update CardStatistics
        card_history_item = CardHistory(card=self, response=grade, reviewed_at=reviewed_at)
        card_history_item.save()

        self.review_count += 1


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
        was_new = self.interval is None

        #adjust ease factor
        last_ease_factor = self.ease_factor
        self.ease_factor = self._next_ease_factor(grade, reviewed_at)
        self.last_ease_factor = last_ease_factor

        #adjust interval
        last_interval = self.interval
        self.interval = self._next_interval(grade, self.ease_factor, reviewed_at)
        self.last_interval = last_interval
    
        #determine next due date
        self.last_due_at = self.due_at
        self.due_at = self._next_due_at(grade, reviewed_at, self.interval)

        #update this card's statistics
        self._update_statistics(grade, reviewed_at)

        self.last_review_grade = grade
        self.last_reviewed_at = reviewed_at
        if grade == GRADE_NONE:
            self.last_failed_at = reviewed_at

        # Update the overall review statistics for this user
        review_stats = self.owner.reviewstatistics #ReviewStatistics.objects.get_or_create(user=self.owner)[0]
        if was_new:
            review_stats.increment_new_reviews()
        if grade == GRADE_NONE:
            review_stats.increment_failed_reviews()
        review_stats.save()


        #TODO add this review to this card's history
        #self.cardhistory.






#TODO tags or this?
#class CardFlag(models.Model):
#  pass


class CardStatistics(models.Model):
    card = models.ForeignKey(Card)


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





