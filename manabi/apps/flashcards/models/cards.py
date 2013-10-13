from datetime import timedelta, datetime
import random

from django.core.cache import cache
from django.db import models
from django.db.models import Count, Min, Max, Sum, Avg
from django.template.loader import render_to_string
from cachecow.decorators import cached_function

from constants import (GRADE_NONE, GRADE_HARD, GRADE_GOOD, GRADE_EASY,
                       MAX_NEW_CARD_ORDINAL, EASE_FACTOR_MODIFIERS,
                       YOUNG_FAILURE_INTERVAL, MATURE_FAILURE_INTERVAL,
                       MATURE_INTERVAL_MIN, GRADE_EASY_BONUS_FACTOR,
                       DEFAULT_EASE_FACTOR, INTERVAL_FUZZ_MAX,
                       ALL_GRADES, GRADE_NAMES)
from cardtemplates import CardTemplate
from manabi.apps.flashcards.cachenamespaces import (deck_review_stats_namespace,
                                        fact_grid_namespace)
from managers.cardmanager import CardManager
from repetitionscheduler import repetition_algo_dispatcher
from undo import UndoCardReview
    

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
        from BeautifulSoup import BeautifulSoup

        fields = dict((field.field_type.name, field)
                      for field in self.fact.field_contents)
        card_context = {'fields': fields}
        def format_(content):
            page = BeautifulSoup(content)
            for tag in page.findAll('script'):
                tag.extract() # Remove the tag.
            return u''.join(page.findAll(text=True)).replace('\n', '').strip()

        front = format_(render_to_string(
            self.template.front_template_name, card_context))
        back = format_(render_to_string(
            self.template.back_template_name, card_context))
        return u'{0} | {1}'.format(front, back)

    def copy(self, target_fact):
        ''' Returns a new Card object. '''
        return Card(fact=target_fact,
                    template_id=self.template_id,
                    priority=self.priority,
                    leech=False, active=True, suspended=False,
                    new_card_ordinal=self.new_card_ordinal)

    @property
    def redis(self):
        from manabi.apps.flashcards.models.redis_models import RedisCard
        return RedisCard(self)

    @property
    def owner(self):
        return self.fact.owner

    @property
    def deck(self):
        return self.fact.owner_deck

    @property
    def siblings(self):
        '''Returns the other cards from this card's fact.'''
        return self.fact.card_set.exclude(id=self.id)

    @property
    def first_reviewed_at(self):
        key = '.'.join(['Card', self.id, 'first_reviewed_at'])
        val = cache.get(key)
        if val is None:
            val = self.cardhistory_set.aggregate(
                    Min('reviewed_at'))['reviewed_at__min']
            cache.set(key, val)
        return val

    @property
    def last_review_grade_name(self):
        '''Returns a string version of the last review grade.'''
        return GRADE_NAMES.get(self.last_review_grade)

    def update_due_at(self, due_at, update_last_due_at=True):
        if update_last_due_at:
            self.last_due_at, self.due_at = (
                self.due_at, due_at)
        else:
            self.due_at = due_at

    def randomize_new_order(self):
        '''
        Randomizes the order of this card, for selecting new cards.
        '''
        self.new_card_ordinal = random.randrange(0, MAX_NEW_CARD_ORDINAL)
        self.save()

    def activate(self):
        from manabi.apps.flashcards.signals import card_active_field_changed
        self.active = True
        self.save()
        card_active_field_changed.send(self, instance=self)

    def deactivate(self):
        from manabi.apps.flashcards.signals import card_active_field_changed
        self.active = False
        self.save()
        card_active_field_changed.send(self, instance=self)

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

    @cached_function(namespace=deck_review_stats_namespace)
    def average_duration(self):
        '''
        The average duration spent on the card each time it is shown
        (seconds, floating-point).
        '''
        return self.cardhistory_set.aggregate(
                Avg('duration'))['duration__avg']

    @cached_function(namespace=deck_review_stats_namespace)
    def total_duration(self):
        '''
        Total duration spent on the card each time it is shown.
        '''
        return self.cardhistory_set.aggregate(
                Sum('duration'))['duration__sum']

    @cached_function(namespace=deck_review_stats_namespace)
    def average_question_duration(self):
        '''
        Returns the average duration spent looking at the question side of 
        this card before viewing the answer (in seconds, floating point).
        '''
        return self.cardhistory_set.aggregate(
                Avg('question_duration'))['question_duration__avg']

    @cached_function(namespace=deck_review_stats_namespace)
    def total_question_duration(self):
        '''
        The total time spent thinking of the answer.
        '''
        return self.cardhistory_set.aggregate(
                Sum('question_duration'))['question_duration__sum']

    @cached_function(namespace=lambda c, *args, **kwargs:
                               fact_grid_namespace(c.deck.pk))
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
        return self._render('flashcards/card_front.html')

    def render_back(self):
        '''Returns a string of the rendered card back.'''
        return self._render('flashcards/card_back.html')

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
        self.update_due_at(from_date + duration, update_last_due_at=False)
        #self.redis.update_due_at()

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

    def _update_statistics(self, grade, reviewed_at,
                           duration=None, question_duration=None):
        '''
        Updates this card's stats. Call this for each review,
        before applying the new review. After applying the new review,
        some other CardHistory fields can be filled in. The reason we do 
        this in 2 parts is that our undo system needs to know about this 
        object, but it creates the undo object before the card object gets 
        updated with the new review stats, so that we can rollback to it.

        See the `self.review` docstring for info on `duration` 
        and `question_duration`.
        '''
        from cardhistory import CardHistory
        #TODO update CardStatistics
        was_new = self.is_new()

        card_history_item = CardHistory(
            card=self, response=grade, reviewed_at=reviewed_at, was_new=was_new,
            duration=duration, question_duration=question_duration)
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
        self.last_ease_factor, self.ease_factor = (
            self.ease_factor, next_repetition.ease_factor)
        self.last_interval, self.interval = (
            self.interval, next_repetition.interval)
        self.update_due_at(next_repetition.due_at)

        self.redis.update_ease_factor()

    def review(self, grade, duration=None, question_duration=None):
        '''
        Commits a review rated with `grade`.

        `question_duration` is an optional parameter which contains the 
        time (in seconds, floating point) that the user spent looking at the 
        question/front side of the card, before hitting "Show Answer" to 
        see the back. It is in effect the time spent thinking of the answer.

        `duration` is the same, but for each entire duration of viewing 
        this card (so, the time taken for the front and back of the card.)
        '''
        from manabi.apps.flashcards.signals import pre_card_reviewed, post_card_reviewed
        pre_card_reviewed.send(self, instance=self)

        reviewed_at = datetime.utcnow()
        was_new = self.is_new()

        # Update this card's statistics
        card_history_item = self._update_statistics(
            grade, reviewed_at,
            duration=duration, question_duration=question_duration)

        # Create Undo stack item
        UndoCardReview.objects.add_undo(card_history_item)

        # Compute and apply updated card repetition values.
        repetition_algo = repetition_algo_dispatcher(
            self, grade, reviewed_at=reviewed_at)
        repetition_algo.next_repetition.delete_cache(repetition_algo)
        next_repetition = repetition_algo.next_repetition()
        self._apply_updated_schedule(next_repetition)

        self.last_review_grade = grade
        self.last_reviewed_at  = reviewed_at

        if grade == GRADE_NONE:
            self.last_failed_at = reviewed_at

        # Finish up the card history item record
        card_history_item.ease_factor = self.ease_factor
        card_history_item.interval    = self.interval
        card_history_item.save()

        self.save()
        self.redis.after_review()
        post_card_reviewed.send(self, instance=self)

