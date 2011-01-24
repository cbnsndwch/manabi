from cardtemplates import CardTemplate
from constants import GRADE_NONE, GRADE_HARD, GRADE_GOOD, GRADE_EASY, \
    MAX_NEW_CARD_ORDINAL, EASE_FACTOR_MODIFIERS, \
    YOUNG_FAILURE_INTERVAL, MATURE_FAILURE_INTERVAL, MATURE_INTERVAL_MIN, \
    GRADE_EASY_BONUS_FACTOR, DEFAULT_EASE_FACTOR, INTERVAL_FUZZ_MAX, \
    NEW_CARDS_PER_DAY, ALL_GRADES
from datetime import timedelta, datetime
from dbtemplates.models import Template
from django.contrib.auth.models import User
from django.db import models
from django.db import transaction
from django.template.loader import render_to_string
from managers.cardmanager import CardManager
from model_utils.managers import manager_from
from repetitionscheduler import repetition_algo_dispatcher
from django.db.models import Avg, Sum
from undo import UndoCardReview
from utils import timedelta_to_float
import random
import usertagging
from django.db.models import Count



class Card(models.Model):
    objects = CardManager()

    fact = models.ForeignKey('flashcards.Fact', db_index=True)
    template = models.ForeignKey(CardTemplate)

    #TODO how to have defaults without null (gives a 'may not be NULL' error)
    # negatives for lower priority, positives for higher
    priority = models.IntegerField(default=0, null=True, blank=True) 
    
    leech = models.BooleanField() #TODO add leech handling
    
    # False when the card is removed from the Fact. This way, we can keep 
    # card statistics if enabled later.
    active = models.BooleanField(default=True, db_index=True) 

    # Not used right now. 'active' is more like a deletion, this is lighter.
    suspended = models.BooleanField(default=False, db_index=True) 

    new_card_ordinal = models.PositiveIntegerField(null=True, blank=True)

    #for owner cards, part of synchronized decks, not used yet
    #synchronized_with = models.ForeignKey('self', null=True, blank=True) 

    ease_factor = models.FloatField(null=True, blank=True)
    interval = models.FloatField(null=True, blank=True, db_index=True) #days
    due_at = models.DateTimeField(null=True, blank=True, db_index=True)
    
    last_ease_factor = models.FloatField(null=True, blank=True)
    last_interval = models.FloatField(null=True, blank=True)
    last_due_at = models.DateTimeField(null=True, blank=True)

    last_reviewed_at = models.DateTimeField(null=True, blank=True)
    last_review_grade = models.PositiveIntegerField(null=True, blank=True)
    last_failed_at = models.DateTimeField(null=True, blank=True)
    
    #TODO use this for is_new
    review_count = models.PositiveIntegerField(default=0, editable=False) 

    class Meta:
        unique_together = (('fact', 'template'), )
        app_label = 'flashcards'

    def __unicode__(self):
        from django.utils.html import strip_tags

        fields = dict((field.field_type.name, field)
                      for field in self.fact.field_contents)
        card_context = {'fields': fields}
        front = render_to_string(
            self.template.front_template_name, card_context)
        back = render_to_string(
            self.template.back_template_name, card_context)

        return strip_tags(u'{0} | {1}'.format(front, back))

    def to_api_dict(self):
        '''
        Returns a dictionary version of this model, to be used with 
        the JSON API. This is a dictionary that can be trivially 
        serialized into JSON.
        '''
        return {
            'id': self.id,
            'factId': self.fact_id,
            'front': self.render_front(),
            'back': self.render_back(),
            'nextDueAtPerGrade':
                dict((grade, rep.due_at)
                        for (grade, rep)
                        in self.next_repetition_per_grade().items())
        }

    @property
    def owner(self):
        return self.fact.deck.owner

    @property
    def siblings(self):
        '''Returns the other cards from this card's fact.'''
        return self.fact.card_set.exclude(id=self.id)

    @property
    def deck(self):
        return self.fact.deck

    def is_new(self):
        '''Returns whether this card has been reviewed before.'''
        return self.last_reviewed_at is None

    def is_mature(self):
        return self.interval >= MATURE_INTERVAL_MIN

    def is_due(self, time=None):
        '''Returns True if this card's due date is in the past.'''
        #TODO why would is_new ever be True and self.due_at be none?
        if time is None: time = datetime.utcnow()

        if self.is_new() or not self.due_at:
            return False
        return self.due_at < time

    def average_duration(self):
        '''
        Returns the average duration spent looking at the question side of 
        this card before viewing the answer (in seconds, floating point).
        '''
        return this.cardhistory_set.aggregate(
            Avg('duration'))['duration__avg']

    def total_duration(self):
        '''
        The total time spent thinking of the answer.
        '''
        return this.cardhistory_set.aggregate(
            Sum('duration'))['duration__sum']

    def _render(self, template_name):
        # map fieldtype-id to fieldcontents
        fields = dict((field.field_type.name, field)
                      for field in self.fact.field_contents)

        card_context = {
            'card': self,
            'fields': fields,
        }
        return render_to_string(template_name, card_context)

    def render_front(self):
        '''Returns a string of the rendered card front.'''
        return self._render('flashcards/card_front.html')#self.template.front_template_name)

    def render_back(self):
        '''Returns a string of the rendered card back.'''
        return self._render('flashcards/card_back.html')#self.template.back_template_name)

    def calculated_interval(self):
        '''
        The `interval` property of a card doesn't necessarily decide the 
        time between the review and the due date - it's used as a basis
        for calculating the due date, but other factors may apply.

        This returns the actual time between last review and due date.
        This is the time the user was supposed to wait.
        '''
        if not self.is_new() and self.due_at is not None:
            return self.due_at - self.last_reviewed_at

    def sibling_spacing(self):
        '''
        Calculate the minimum space between this card and its siblings
        that should be enforced (not necessarily actual, 
        if the user chooses to review early).

        The space is `space_factor` times this card's interval, 
        or `min_card_space` at minimum.

        Returns a timedelta.

        TODO: maybe this should be more dependent on each card or something
        TODO: also maybe a max space if dependent on other cards' intervals
        '''
        space_factor  = self.fact.fact_type.space_factor
        min_card_space = self.fact.fact_type.min_card_space

        min_space = max(min_card_space, 
                        space_factor * (self.interval or 0))

        return timedelta(days=min_space)

    def delay(self, duration):
        '''
        This card's due date becomes `duration` (a timedelta) days from
        now, or from its due date if not yet due.
        
        This is for when this card is due at the same time as a sibling 
        card (a card from the same fact).
        '''
        now = datetime.utcnow()
        from_date = self.due_at if self.due_at >= now else now
        self.due_at = from_date + duration

    def next_repetition_per_grade(self, reviewed_at=None):
        #FIXME disable fuzzing
        if not reviewed_at:
            reviewed_at = datetime.utcnow()

        reps = {}
        for grade in ALL_GRADES:
            repetition_algo = repetition_algo_dispatcher(
                self, grade, reviewed_at=reviewed_at)
            reps[grade] = repetition_algo.next_repetition()
        return reps

    def _update_statistics(self, grade, reviewed_at, duration=None):
        '''
        Updates this card's stats. Call this for each review,
        before applying the new review. After applying the new review,
        some other CardHistory fields can be filled in. The reason we do 
        this in 2 parts is that our undo system needs to know about this 
        object, but it creates the undo object before the card object gets 
        updated with the new review stats, so that we can rollback to it.

        See the `self.review` docstring for info on `duration`.
        '''
        #TODO update CardStatistics
        was_new = self.is_new()

        card_history_item = CardHistory(
            card=self,
            response=grade,
            reviewed_at=reviewed_at,
            was_new=was_new,
            duration=duration)
        card_history_item.save()

        self.review_count += 1

        return card_history_item

    def _apply_updated_schedule(self, next_repetition):
        '''
        Updates this card's scheduling with values for the next repetition.

        `next_repetition` should have the following fields:
            `interval`, `ease_factor`, `due_at`

        (See `NextRepetition` class)
        '''
        self.last_ease_factor, self.ease_factor = \
            self.ease_factor, next_repetition.ease_factor
        self.last_interval, self.interval = \
            self.interval, next_repetition.interval
        self.last_due_at, self.due_at = \
            self.due_at, next_repetition.due_at

    @transaction.commit_on_success
    def review(self, grade, duration=None):
        '''
        Commits a review rated with `grade`.

        `duration` is an optional parameter which contains the time (in 
        seconds, floating point) that the user spent looking at the 
        question/front side of the card, before hitting "Show Answer" to 
        see the back. It is in effect the time spent thinking of the answer.
        '''
        reviewed_at = datetime.utcnow()
        was_new = self.is_new()

        # Update this card's statistics
        card_history_item = self._update_statistics(
            grade, reviewed_at, duration=duration)

        # Update the overall review statistics for this user
        review_stats = self.owner.reviewstatistics
        if was_new:
            review_stats.increment_new_reviews()
        if grade == GRADE_NONE:
            review_stats.increment_failed_reviews()

        # Create Undo stack item
        UndoCardReview.objects.add_undo(card_history_item)

        # Compute and apply updated card repetition values
        repetition_algo = repetition_algo_dispatcher(
            self, grade, reviewed_at=reviewed_at)
        next_repetition = repetition_algo.next_repetition()
        self._apply_updated_schedule(next_repetition)

        self.last_review_grade = grade
        self.last_reviewed_at = reviewed_at

        if grade == GRADE_NONE:
            self.last_failed_at = reviewed_at

        # Finish up the card history item record
        card_history_item.ease_factor = self.ease_factor
        card_history_item.interval    = self.interval
        card_history_item.save()

        review_stats.save()
        self.save()


#TODO implement (remember to update UndoReview too)
# This can probably just be a proxy model for CardHistory or something.
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



class CardHistoryManagerMixin(object):
    def of_user(self, user):
        return self.filter(card__fact__deck__owner=user)

    def new(self):
        return self.filter(was_new=True)
    
    def young(self):
        return self.filter(was_new=False, interval__lt=MATURE_INTERVAL_MIN)

    def mature(self):
        return self.filter(interval__gte=MATURE_INTERVAL_MIN)

    def with_reviewed_on_dates(self):
        '''
        Adds a `reviewed_on` field to the selection which is extracted 
        from the `reviewed_at` datetime field.
        '''
        return self.extra(select={'reviewed_on': 'date(reviewed_at)'})


class CardHistoryStatsMixin(object):
    '''Stats data methods for use in graphs.'''
    def repetitions(self):
        '''
        Returns a list of dictionaries,
        with values 'date' and 'repetitions', the count of reps that day.
        '''
        return self.with_reviewed_on_dates().values(
            'reviewed_on').order_by().annotate(
            repetitions=Count('id'))



CardHistoryManager = lambda: manager_from(
    CardHistoryManagerMixin, CardHistoryStatsMixin)

class CardHistory(models.Model):
    objects = CardHistoryManager()

    card = models.ForeignKey(Card)

    response = models.PositiveIntegerField(editable=False)
    reviewed_at = models.DateTimeField()

    ease_factor = models.FloatField(null=True, blank=True)
    interval = models.FloatField(null=True, blank=True, db_index=True) #days

    # Was the card new when it was reviewed this time?
    was_new = models.BooleanField(default=False, db_index=True) 

    duration = models.FloatField(null=True, blank=True)

    class Meta:
        app_label = 'flashcards'


