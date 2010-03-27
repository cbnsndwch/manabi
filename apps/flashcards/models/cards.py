from django.db import models
from django.contrib.auth.models import User
from django.forms import ModelForm
from django.forms.util import ErrorList
from dbtemplates.models import Template
from itertools import chain
from django.db.models import Avg, Max, Min, Count
import random
from math import cos, pi
import datetime
from facts import Fact, FactType, SharedFact
from cardtemplates import CardTemplate
from reviews import ReviewStatistics
from undo import UndoCardReview
import usertagging
from django.template.loader import render_to_string
from django.db import transaction

from constants import MAX_NEW_CARD_ORDINAL

#grade IDs (don't change these once they're set)
GRADE_NONE = 0
#GRADE_BAD = 1
#GRADE_MISTAKE = 2
GRADE_HARD = 3
GRADE_GOOD = 4
GRADE_EASY = 5
ALL_GRADES = [GRADE_NONE, GRADE_HARD, GRADE_GOOD, GRADE_EASY,] #{GRADE_NONE:GRADE_NONE, GRADE_HARD:GRADE_HARD, GRADE_GOOD:GRADE_GOOD, GRADE_EASY:GRADE_EASY}

#below is used in the EF equation, but we're going to precompute the EF factors
#GRADE_FACTORS = {GRADE_NONE: 0, GRADE_HARD: 3, GRADE_GOOD: 4, GRADE_EASY: 5}
#this is the EF algorithm from which the EF factors are computed:
#ease_factor = self.ease_factor + (0.1 - (max_grade - grade_factor) * (0.08 + (max_grade - grade_factor) * 0.02))

#MAX_EASE_FACTOR_STEP = 0.1

#these are the precomputed values, so that we can modify them independently later to test their effectiveness:
EASE_FACTOR_MODIFIERS = {GRADE_NONE: -0.3, GRADE_HARD: -0.1401, GRADE_GOOD: 0.0, GRADE_EASY: 0.1} #TODO accurate grade_none value

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

NEW_CARDS_PER_DAY = 200 #TODO this should at least be an option, but should also scale to use

#number of failed cards before failed cards are shown earlier than any due cards
#TODO MAX_FAILED_CARDS = 20 #TODO should be option.

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

    def count(self, user, deck=None, tags=None):
        cards = self.of_user(user)
        if deck:
            cards = cards.filter(fact__deck=deck)
        if tags:
            facts = usertagging.models.UserTaggedItem.objects.get_by_model(Fact, tags)
            cards = cards.filter(fact__in=facts)
        return cards.count()
            

    def of_user(self, user):
        #TODO this is probably really slow
        user_cards = self.filter(suspended=False, active=True)
        facts = Fact.objects.with_synchronized(user)
        user_cards = self.filter(fact__in=facts)
        return user_cards

    def new_cards(self, user, deck=None):
        new_cards = self.of_user(user).filter(last_reviewed_at__isnull=True)
        if deck:
            new_cards = new_cards.filter(fact__deck=deck)
        return new_cards

    def due_cards(self, user, deck=None):
        due_cards = self.of_user(user).filter(due_at__lte=datetime.datetime.utcnow()).order_by('-interval')
        if deck:
            due_cards = due_cards.filter(fact__deck=deck)
        return due_cards


    #def failed_cards(self):
    #    failed_cards = self.filter(last_review_grade=GRADE_NONE)

    #def mature_cards(self):
    #    return self.filter(interval__gt=MATURE_INTERVAL_MIN)
    

    def spaced_cards_new_count(self, user, deck=None):
        threshold_at = datetime.datetime.utcnow() - datetime.timedelta(minutes=30)
        recently_reviewed = self.filter(fact__deck__owner=user, fact__deck=deck, last_reviewed_at__lte=threshold_at)
        facts = Fact.objects.filter(id__in=recently_reviewed.values_list('fact', flat=True))
        new_cards_count = self.new_cards(user, deck).exclude(fact__in=facts).count()
        return new_cards_count


    def cards_new_count(self, user, deck=None):
        new_cards_count = self.new_cards(user, deck).count()
        return new_cards_count


    def cards_due_count(self, user, deck=None):
        due_cards_count = self.due_cards(user, deck).count()
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


    def _next_failed_due_cards(self, user, initial_query, count, review_time, excluded_ids=[], daily_new_card_limit=None, early_review=False, deck=None, tags=None):
        if not count:
            return []
        cards = initial_query.filter(last_review_grade=GRADE_NONE, due_at__lte=review_time).order_by('due_at')
        return cards[:count] #don't space these #self._space_cards(cards, count, review_time)


    def _next_not_failed_due_cards(self, user, initial_query, count, review_time, excluded_ids=[], daily_new_card_limit=None, early_review=False, deck=None, tags=None):
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


    def _next_failed_not_due_cards(self, user, initial_query, count, review_time, excluded_ids=[], daily_new_card_limit=None, early_review=False, deck=None, tags=None):
        if not count:
            return []
        #TODO prioritize certain failed cards, not just by due date
        # We'll show failed cards even if they've been reviewed recently.
        # This is because failed cards are set to be shown 'soon' and not just 
        # in 10 minutes. Special rules.
        #TODO we shouldn't show mature failed cards so soon though!
        card_query = initial_query.filter(last_review_grade=GRADE_NONE, \
                due_at__gt=review_time).order_by('due_at') #TODO randomize the order (once we fix the Undo)
        return card_query[:count]




    def _next_new_cards(self, user, initial_query, count, review_time, excluded_ids=[], daily_new_card_limit=None, early_review=False, deck=None, tags=None):
        '''Gets the next new cards for this user or deck.
        '''
        if not count:
            return []

        new_card_query = initial_query.filter(due_at__isnull=True).order_by('new_card_ordinal')

        if daily_new_card_limit:
            new_reviews_today = user.reviewstatistics.get_new_reviews_today()
            if new_reviews_today >= daily_new_card_limit:
                return []
            # Count the number of new cards in the `excluded_ids`, which the user already has queued up
            new_excluded_cards_count = Card.objects.filter(id__in=excluded_ids, due_at__isnull=True).count()
            new_count_left_for_today = daily_new_card_limit - new_reviews_today - new_excluded_cards_count
        else:
            new_count_left_for_today = None

        def _next_new_cards2():
            new_cards = []
            for card in new_card_query.iterator():
                min_space = card.min_space_from_siblings()
                for sibling_card in card.siblings():
                    # sibling card is already included as a new card to be shown or
                    # sibling card is currently in the client-side review queue or 
                    # sibling card is due or
                    # sibling card was reviewed recently or
                    # sibling card is failed. Either it's due, or it's not due and it's shown before new cards.
                    if sibling_card in new_cards or \
                       sibling_card.id in excluded_ids or \
                       sibling_card.is_due(review_time) or \
                       (sibling_card.last_reviewed_at and review_time - sibling_card.last_reviewed_at <= min_space) or \
                       sibling_card.last_review_grade == GRADE_NONE:
                        break
                else:
                    new_cards.append(card)
                    # Got enough cards?
                    if len(new_cards) == count or \
                       (new_count_left_for_today is not None and not early_review and len(new_cards) == new_count_left_for_today):
                        break
            return new_cards

        new_cards = _next_new_cards2()

        if len(new_cards) < count:
            # see if we can get new cards from synchronized decks
            facts_added = Fact.objects.add_new_facts_from_synchronized_decks(user, count - len(new_cards), deck=deck, tags=tags)
            if len(facts_added):
                # got new facts from a synchronized deck. get cards from them by re-getting new cards
                new_cards = _next_new_cards2()

        eligible_ids = [card.id for card in new_cards]

        if early_review and len(eligible_ids) < count:
            # queue up spaced cards if needed for early review
            eligible_ids.extend([card.id for card in new_card_query.exclude(id__in=eligible_ids)[:count - len(eligible_ids)]])

        # Return a query containing the eligible cards.
        ret = self.filter(id__in=eligible_ids).order_by('new_card_ordinal')
        ret = ret[:min(count, new_count_left_for_today)] if daily_new_card_limit else ret[:count]
        return ret
            


    def _next_due_soon_cards(self, user, initial_query, count, review_time, excluded_ids=[], daily_new_card_limit=None, early_review=False, deck=None, tags=None):
        '''
        Used for early review.
        Ordered by due date.
        '''
        if not count:
            return []
        priority_cutoff = review_time - datetime.timedelta(minutes=60)
        cards = initial_query.exclude(last_review_grade=GRADE_NONE).filter(due_at__gt=review_time).order_by('due_at')
        staler_cards = cards.filter(last_reviewed_at__gt=priority_cutoff).order_by('due_at')
        return self._space_cards(staler_cards, count, review_time, early_review=True)


    def _next_due_soon_cards2(self, user, initial_query, count, review_time, excluded_ids=[], daily_new_card_limit=None, early_review=False, deck=None, tags=None):
        if not count:
            return []
        priority_cutoff = review_time - datetime.timedelta(minutes=60)
        cards = initial_query.exclude(last_review_grade=GRADE_NONE).filter(due_at__gt=review_time).order_by('due_at')
        fresher_cards = cards.filter(last_reviewed_at__lte=priority_cutoff).order_by('due_at')
        return self._space_cards(fresher_cards, count, review_time, early_review=True)


    #FIXME distinguish from cards_new_count or merge or make some new kind of review optioned class
    #TODO consolidate with next_cards (see below)
    #FIXME make it work for synced decks
    def new_cards_count(self, user, excluded_ids, deck=None, tags=None):
        '''Returns the number of new cards for the given review parameters.'''
        now = datetime.datetime.utcnow()

        user_cards = self.of_user(user)

        if deck:
            user_cards = user_cards.filter(fact__deck=deck)

        if tags:
            facts = usertagging.models.UserTaggedItem.objects.get_by_model(Fact, tags)
            user_cards = user_cards.filter(fact__in=facts)

        if excluded_ids:
            user_cards = user_cards.exclude(id__in=excluded_ids)

        new_cards = user_cards.filter(last_reviewed_at__isnull=True) #due_at__isnull=True)
        return new_cards.count()

        
    #def _next_cards_initial_query(self, user, count, excluded_ids, session_start, deck=None, tags=None, early_review=False, daily_new_card_limit=None):


    def count_of_cards_due_tomorrow(self, user, deck=None, tags=None):
        '''
        Returns the number of cards due by tomorrow at the same time as now.
        Doesn't take future spacing into account though, so it's a somewhat rough estimate.
        '''
        cards = self.of_user(user)
        if deck:
            cards = cards.filter(fact__deck=deck)
        if tags:
            facts = usertagging.models.UserTaggedItem.objects.get_by_model(Fact, tags)
            cards = cards.filter(fact__in=facts)
        this_time_tomorrow = datetime.datetime.utcnow() + datetime.timedelta(days=1)
        cards = cards.filter(due_at__lt=this_time_tomorrow)
        due_count = cards.count()
        new_count = min(NEW_CARDS_PER_DAY, self.new_cards_count(user, [], deck=deck, tags=tags))
        return due_count + new_count


    def next_card_due_at(self, user, deck=None, tags=None):
        '''
        Returns the due date of the next due card.
        '''
        cards = self.of_user(user)
        if deck:
            cards = cards.filter(fact__deck=deck)
        if tags:
            facts = usertagging.models.UserTaggedItem.objects.get_by_model(Fact, tags)
            cards = cards.filter(fact__in=facts)
        try:
            card = cards.filter(due_at__isnull=False).order_by('due_at')[0]
        except IndexError:
            return None
        return card.due_at
        

    def _next_cards(self, early_review=False, daily_new_card_limit=None):
        card_funcs = [
            self._next_failed_due_cards,        # due, failed
            self._next_not_failed_due_cards,    # due, not failed
            self._next_failed_not_due_cards]    # failed, not due

        if early_review and daily_new_card_limit:
            card_funcs.extend([
                self._next_due_soon_cards,
                self._next_due_soon_cards2]) # due soon, not yet, but next in the future
        else:
            card_funcs.extend([self._next_new_cards]) # new cards at end
        return card_funcs


    def _user_cards(self, user, deck=None, tags=None, excluded_ids=None):
        user_cards = self.of_user(user)

        if deck:
            user_cards = user_cards.filter(fact__deck=deck)

        if tags:
            facts = usertagging.models.UserTaggedItem.objects.get_by_model(Fact, tags)
            user_cards = user_cards.filter(fact__in=facts)

        if excluded_ids:
            user_cards = user_cards.exclude(id__in=excluded_ids)
        return user_cards
    

    def next_cards_count(self, user, excluded_ids=[], session_start=False, deck=None, tags=None, early_review=False, daily_new_card_limit=None):
        now = datetime.datetime.utcnow()
        card_funcs = self._next_cards(early_review=early_review, daily_new_card_limit=daily_new_card_limit)
        user_cards = self._user_cards(user, deck=deck, excluded_ids=excluded_ids, tags=tags)
        count = 0
        cards_left = 99999 #TODO find a more elegant approach
        for card_func in card_funcs:
            cards = card_func(user, user_cards, cards_left, now, excluded_ids, daily_new_card_limit, \
                    early_review=early_review,
                    deck=deck,
                    tags=tags)
            count += cards.count()
        return count


    def next_cards(self, user, count, excluded_ids=[], session_start=False, deck=None, tags=None, early_review=False, daily_new_card_limit=None):
        '''
        Returns `count` cards to be reviewed, in order.
        count should not be any more than a short session of cards
        set `early_review` to True for reviewing cards early (following any due cards)

        If both early_review is True and daily_new_card_limit is None,
        new cards will be chosen even if they were spaced due to sibling reviews.
        "Due soon" cards won't be chosen in this case, contrary to early_review's normal behavior.
        (#TODO consider changing this to have a separate option)

        The return format is
        '''

        #TODO somehow spread some new cards into the early review cards if early_review==True
        #TODO use args instead, like *kwargs etc for these funcs
        now = datetime.datetime.utcnow()
        card_funcs = self._next_cards(early_review=early_review, daily_new_card_limit=daily_new_card_limit)
        user_cards = self._user_cards(user, deck=deck, excluded_ids=excluded_ids, tags=tags)
        cards_left = count
        card_queries = []
        for card_func in card_funcs:
            if not cards_left:
                break
            cards = card_func(user, user_cards, cards_left, now, excluded_ids, daily_new_card_limit, \
                    early_review=early_review,
                    deck=deck,
                    tags=tags)
            cards_left -= len(cards)
            if len(cards):
                card_queries.append(cards)


        #TODO decide what to do with this #if session_start:
        #FIXME add new cards into the mix when there's a defined new card per day limit
        #for now, we'll add new ones to the end
        return chain(*card_queries)






class AbstractCard(models.Model):
    template = models.ForeignKey(CardTemplate)

    #TODO how to have defaults without null (gives a 'may not be NULL' error)
    priority = models.IntegerField(default=0, null=True, blank=True) #negatives for lower priority, positives for higher
    
    leech = models.BooleanField() #TODO add leech handling
    
    active = models.BooleanField(default=True, db_index=True) #False when the card is removed from the Fact. This way, we can keep card statistics if enabled later
    suspended = models.BooleanField(default=False, db_index=True) #Not used right now. 'active' is more like a deletion, this is lighter

    new_card_ordinal = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        app_label = 'flashcards'
        abstract = True
    

class SharedCard(AbstractCard):
    fact = models.ForeignKey(SharedFact, db_index=True)
    
    class Meta:
        unique_together = (('fact', 'template'), )
        app_label = 'flashcards'


class Card(AbstractCard):
    objects = CardManager()

    fact = models.ForeignKey(Fact, db_index=True)
    
    #synchronized_with = models.ForeignKey('self', null=True, blank=True) #for owner cards, part of synchronized decks, not used yet

    ease_factor = models.FloatField(null=True, blank=True)
    interval = models.FloatField(null=True, blank=True, db_index=True) #days
    due_at = models.DateTimeField(null=True, blank=True, db_index=True) #null means this card is 'new'
    
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


    #def save(self, *args, **kwargs):
    #    if not self.new_card_ordinal:
    #        self.new_card_ordinal = random.randrange(0, MAX_NEW_CARD_ORDINAL)
    #    super(Card, self).save(*args, **kwargs)


    @property
    def owner(self):
        return self.fact.deck.owner

    
    def _render(self, template_name):
        # map fieldtype-id to fieldcontents
        fields = dict((field.field_type.id, field) for field in self.fact.field_contents)
        card_context = {'fields': fields}
        return render_to_string(template_name, card_context)


    def render_front(self):
        '''Returns a string of the rendered card front.
        '''
        return self._render(self.template.front_template_name)


    def render_back(self):
        '''Returns a string of the rendered card back.
        '''
        return self._render(self.template.back_template_name)


    def due_at_per_grade(self, reviewed_at=None):
        if not reviewed_at:
            reviewed_at = datetime.datetime.utcnow()
        due_times = {}
        for grade in [GRADE_NONE, GRADE_HARD, GRADE_GOOD, GRADE_EASY,]:
            # Disable fuzzing so that lower grades won't have later due times than higher grades
            # (although this can happen in practice, only due to this fuzzing).
            # It also makes grades appear more consistent.
            due_at = self._next_due_at(grade, reviewed_at, self._next_interval(grade, self._next_ease_factor(grade, reviewed_at), reviewed_at, do_fuzz=False))
            duration = due_at - reviewed_at
            days = duration.days + (duration.seconds / 86400.0)
            days = format(round(days, 4), '.4f')
            due_times[grade] = days
        due_times = dict((grade, due_time) for grade, due_time in due_times.items())
        return due_times


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
        sibling_intervals = [card.interval for card in sibling_cards if card.interval is not None]
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


    def _last_reviewed_sibling(self):
        last_reviewed_sibling = None
        for sibling in self.siblings():
            if sibling.last_reviewed_at and \
                    (not last_reviewed_sibling \
                    or (sibling.last_reviewed_at and sibling.last_reviewed_at > last_reviewed_sibling.last_reviewed_at)):
                last_reviewed_sibling = sibling#.last_reviewed_at
        return last_reviewed_sibling


    def _time_since_last_sibling_review(self):
        '''
        Returns the time elapsed since the latest review of 
        a sibling card.
        '''
        last_sibling_reviewed_at = self._last_reviewed_sibling().last_reviewed_at
        return datetime.datetime.utcnow() - last_sibling_reviewed_at
            

    @property
    def next_due_at(self):
        '''Returns a dict of {grade: {due_in:datetime, ease_factor:float} } for each grade.
        '''
        reviewed_at = datetime.datetime.utcnow()
        due_times = {}
        for grade in ALL_GRADES:
            next_ef = self._next_ease_factor(grade, reviewed_at)
            next_interval = self._next_interval(grade, next_ef, reviewed_at)
            due_at = self._next_due_at(grade, reviewed_at, next_interval)
            duration = due_at - reviewed_at
            days = duration.days + (duration.seconds / 86400.0)
            due_times[grade] = {'due_in': days, 'due_at': due_at, 'ease_factor': next_ef, 'interval': next_interval}
        return due_times

    def _next_interval(self, grade, ease_factor, reviewed_at, do_fuzz=True):
        '''
        Returns an interval, measured in days.

        Make sure any spacing delays due to sibling cards
        is already accounted for in this card's due_at
        by the time this is called.
        '''
        #TODO shouldnt be a private function, maybe

        # Early Review due to siblings.
        is_early_review_due_to_sibling = False
        last_reviewed_sibling = self._last_reviewed_sibling()
        if last_reviewed_sibling:
            time_since_last_sibling_review = datetime.datetime.utcnow() - last_reviewed_sibling.last_reviewed_at
            #print 'last_reviewed_sibling.last_reviewed_at: '+str(last_reviewed_sibling.last_reviewed_at)
            #print 'time_since_last_sibling_review: '+str(time_since_last_sibling_review)
            if time_since_last_sibling_review < datetime.timedelta(minutes=60): #TODO don't hardcode here
                last_sibling_grade = last_reviewed_sibling.last_review_grade
                percentage_waited_for_sibling = timedelta_to_float(time_since_last_sibling_review) / timedelta_to_float(datetime.timedelta(minutes=60))
                is_early_review_due_to_sibling = True

        # New card.
        if self.interval is None:
            #get this card's deck, which has the initial interval durations
            #(initial intervals are configured at the deck level)
            next_interval = self.fact.deck.schedulingoptions.initial_interval(grade, do_fuzz=do_fuzz)

            # Lessen the interval if this card is reviewed shortly after a sibling card
            # (for Early Review)
            #FIXME need a better solution for this. dependent on the status of the sibling card.
            if grade > GRADE_NONE:
                if is_early_review_due_to_sibling:
                    #print 'next_interval was to be: ' + str(next_interval)
                    #print 'percentage_waited_for_sibling: ' + str(percentage_waited_for_sibling)
                    #if grade < last_sibling_grade:
                    #    next_interval *= self._adjustment_curve(percentage_waited_for_sibling)
                    #else:
                    #    next_interval = min(next_interval, last_reviewed_sibling.interval)
                    #next_interval *= self._adjustment_curve(percentage_waited_for_sibling)
                    if grade > last_sibling_grade:
                        difference = next_interval - self.fact.deck.schedulingoptions.initial_interval(last_sibling_grade)
                        next_interval -= difference * self._adjustment_curve(1 - percentage_waited_for_sibling)
                    #print 'next_interval became: ' + str(next_interval)
        # Old card.
        else:
            current_interval = self.interval

            # Treat like a new card since it was failed last review.
            if self.last_review_grade == GRADE_NONE:
                #TODO treat mature failed cards differently
                next_interval = self.fact.deck.schedulingoptions.initial_interval(grade, do_fuzz=do_fuzz)

                # Lessen the effect if this card was reviewed successfully very soon after failing
                if grade > GRADE_NONE:
                    time_since_last_review = reviewed_at - self.last_reviewed_at
                    if time_since_last_review < datetime.timedelta(minutes=60): #TODO don't hard code this value here
                        next_interval /= 1.6 #TODO don't hardcode this here
                # Also lessen if it's right after a sibling card review

            else:
                # Review failure.
                if grade == GRADE_NONE:
                    # Reset the interval to an initial value.
                    #TODO how to handle failures on new cards? should it keep its 'new' status, and should the EF change?
                    #TODO handle failures of cards that are reviewed early differently somehow
                    #TODO penalize even worse if it was reviewed early and still failed
                    if self.is_mature():
                        # Failure on a mature card
                        next_interval = MATURE_FAILURE_INTERVAL
                    else:
                        # Failure on a young or new card
                        # Reset the interval
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
                        # Cap the bonus.
                        if grade < GRADE_EASY:
                            bonus_cap_factor = 4.0 #TODO don't hardcode
                        else:
                            # cap less severely for easy grades
                            bonus_cap_factor = 10.0 #TODO don't hardcode
                        interval_bonus = min(interval_bonus, timedelta_to_float(datetime.timedelta(bonus_cap_factor * current_interval)))

                    current_interval += interval_bonus

                    # Penalize hard grades.
                    if grade == GRADE_HARD:
                        ease_factor = 1.2

                    next_interval = current_interval * ease_factor

                    # Give a bonus for easy grades.
                    if grade == GRADE_EASY:
                        next_interval += next_interval * GRADE_EASY_BONUS_FACTOR

                    # Early review.
                    #FIXME account for early review due to sibling? or is it always going to be spaced anyway, thus affecting due_at
                    #TODO for now assume due_at includes delays for spacing by now - but perhaps delays should be separated from due_at?
                    if reviewed_at < self.due_at or is_early_review_due_to_sibling:
                        if reviewed_at < self.due_at:
                            # Lessen the interval increase, proportionate to how early it was reviewed.
                            last_effective_interval = timedelta_to_float(self.due_at - self.last_reviewed_at)

                            percentage_waited = timedelta_to_float(reviewed_at - self.last_reviewed_at) / last_effective_interval
                        else:
                            percentage_waited = 1.0 # to be the 

                        # Consider the time since last review to be even less if a sibling card was reviewed more recently.
                        if is_early_review_due_to_sibling:
                            percentage_waited = min(percentage_waited, percentage_waited_for_sibling)

                        #TODO Give penalty for hard grades in an early review, if the last grade was better.

                        #print 'percentage waited: ' + str(percentage_waited)

                        # If reviewed really early, don't add much to the interval.
                        # If reviewed close to due date, add most of the interval.
                        adjusted_interval_increase = (next_interval - current_interval) * self._adjustment_curve(percentage_waited)

                        #print 'interval increase was going to be: ' + str(next_interval - current_interval)
                        #print 'but was changed to: ' + str(adjusted_interval_increase)
                        next_interval = current_interval + adjusted_interval_increase
                        #print 'current interval is: ' + str(current_interval)
                        #print 'so next interval is: ' + str(next_interval)

        if do_fuzz:
            # Fuzz the result. Conservatively favor shorter intervals.
            #print 'next_interval before fuzz:' + str(next_interval)
            fuzz = next_interval * random.triangular(-INTERVAL_FUZZ_MAX, INTERVAL_FUZZ_MAX, (-INTERVAL_FUZZ_MAX) / 4.5)
            # Fuzz less for early reviews.
            if is_early_review_due_to_sibling or (self.due_at and reviewed_at < self.due_at):
                #TODO refactor / DRY all these early review calculations
                if self.last_reviewed_at:
                    last_effective_interval = timedelta_to_float(self.due_at - self.last_reviewed_at)
                    if is_early_review_due_to_sibling and last_reviewed_sibling.last_reviewed_at > self.last_reviewed_at:
                        last_effectively_reviewed_at = last_reviewed_sibling.last_reviewed_at
                    else:
                        last_effectively_reviewed_at = self.last_reviewed_at
                    percentage_waited = timedelta_to_float(reviewed_at - last_effectively_reviewed_at) / last_effective_interval
                # New card.
                else:
                    percentage_waited = percentage_waited_for_sibling
                #print 'fuzz was to be: ' + str(fuzz)
                fuzz *= self._adjustment_curve(percentage_waited)
                #print 'adjusted fuzz: ' + str(fuzz)
            next_interval += fuzz
            #print 'and after fuzz: ' + str(next_interval)

        return next_interval


    def _next_ease_factor(self, grade, reviewed_at):
        #TODO refactor early review detection into its own method for DRY

        # Was it reviewed too soon after a sibling card? (Early Review)
        is_early_review_due_to_sibling = False
        last_reviewed_sibling = self._last_reviewed_sibling()
        if last_reviewed_sibling:
            time_since_last_sibling_review = datetime.datetime.utcnow() - last_reviewed_sibling.last_reviewed_at
            if time_since_last_sibling_review < datetime.timedelta(minutes=60): #TODO don't hardcode here
                last_sibling_grade = last_reviewed_sibling.last_review_grade
                percentage_waited_for_sibling = timedelta_to_float(time_since_last_sibling_review) / timedelta_to_float(datetime.timedelta(minutes=60))
                is_early_review_due_to_sibling = True

        # New card.
        if self.ease_factor is None:
            # Default to the average for this deck
            next_ease_factor = self.fact.deck.average_ease_factor() + EASE_FACTOR_MODIFIERS[grade]

            # Lessen the ease if this card was reviewed very soon after a sibling card.
            if is_early_review_due_to_sibling:
                #print 'grade: '+str(grade)
                #print 'last_sibling_grade: '+str(last_sibling_grade)
                if grade <= last_sibling_grade:
                    # Rated lower than expected since sibling was reviewed recently,
                    # yet rated higher than this.
                    #print 'next EF was to be: ' + str(next_ease_factor)
                    #print 'percentage_waited_for_sibling: ' + str(percentage_waited_for_sibling)
                    next_ease_factor -= (1 - self._adjustment_curve(percentage_waited_for_sibling)) * 0.1 #TODO don't hardcode here
                    #print 'next EF became: ' + str(next_ease_factor)
                else:
                    # This was probably rated higher than needed, 
                    # so let's just put it the sibling's EF, plus the modifier, brought it down 1 grade for calculating ease.
                    #print 'next EF was to be: ' + str(next_ease_factor)
                    #print 'percentage_waited_for_sibling: ' + str(percentage_waited_for_sibling)
                    new_grade = grade - 1
                    if grade in [GRADE_NONE, GRADE_HARD]:
                        new_grade = GRADE_NONE
                    else:
                        new_grade = grade - 1
                    next_ease_factor = last_reviewed_sibling.ease_factor + EASE_FACTOR_MODIFIERS[new_grade]
                    #self.fact.deck.average_ease_factor()# + EASE_FACTOR_MODIFIERS[grade - 1]
                    #print 'next EF became: ' + str(next_ease_factor)
        # Old card.
        else:
            # Only make the ease factor harder if the last review grade was better than this review (for young cards only)
            if EASE_FACTOR_MODIFIERS[grade] <= 0 and self.is_being_learned() and grade >= self.last_review_grade:
                #TODO make it slightly harder if it was reviewed again too early, compared to self or sibling
                #TODO is_being_learned might not cut it for later when mature failures are taken into account (it would return false?)
                next_ease_factor = self.ease_factor
            else:
                next_ease_factor = self.ease_factor + EASE_FACTOR_MODIFIERS[grade]
                #print 'current EF: ' + str(self.ease_factor)
                #print 'next EF: ' + str(next_ease_factor)

                # Lessen the effect if this card was reviewed successfully soon after failing
                if grade > GRADE_NONE \
                        and self.last_review_grade == GRADE_NONE \
                        and (reviewed_at - self.last_reviewed_at) < datetime.timedelta(minutes=60): #TODO don't hard code this value here
                    #FIXME except if this is an early review due to spacing from siblings, then don't lessen it as much
                    #TODO different adjustment for 'hard' grades vs good/too easy
                    percentage_early_since_failure = timedelta_to_float(reviewed_at - self.last_reviewed_at) \
                            / timedelta_to_float(datetime.timedelta(minutes=60)) #TODO don't hard code this value here

                    if is_early_review_due_to_sibling:
                        percentage_early_since_failure = min(percentage_early_since_failure, percentage_waited_for_sibling)

                    adjustment = (next_ease_factor - self.ease_factor) * self._adjustment_curve(percentage_early_since_failure)
                    next_ease_factor = self.ease_factor + adjustment
                # Early Review, and not right after a failure (failure reviews will often be 'early').
                elif reviewed_at < self.due_at and self.last_review_grade != GRADE_NONE:
                    # Lessen the EF adjustment, proportionate to how early it was reviewed.
                    last_effective_interval = timedelta_to_float(self.due_at - self.last_reviewed_at)
                    percentage_waited = timedelta_to_float(reviewed_at - self.last_reviewed_at) / last_effective_interval
                    #print 'percentage waited: ' + str(percentage_waited)
                    # If reviewed really early, don't add much to the interval.
                    # If reviewed close to due date, add most of the interval.
                    if is_early_review_due_to_sibling:
                        percentage_waited = min(percentage_waited, percentage_waited_for_sibling)
                        #print 'percentage waited changed to: ' + str(percentage_waited)
                    adjustment = (next_ease_factor - self.ease_factor) * self._adjustment_curve(percentage_waited)
                    #print 'adjustment: ' + str(adjustment)
                    next_ease_factor = self.ease_factor + adjustment
                # Early Review, compared to sibling
                elif is_early_review_due_to_sibling:
                    adjustment = (next_ease_factor - self.ease_factor) * self._adjustment_curve(percentage_waited_for_sibling)
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
        return card_history_item


    def _next_due_at(self, grade, reviewed_at, interval):
        return reviewed_at + datetime.timedelta(days=interval)


    @transaction.commit_on_success    
    def review(self, grade):
        #TODO how to handle failures on new cards? should it keep its 'new' status, and should the EF change?

        reviewed_at = datetime.datetime.utcnow()
        was_new = self.interval is None

        # Update this card's statistics
        card_history_item = self._update_statistics(grade, reviewed_at)

        # Update the overall review statistics for this user
        review_stats = self.owner.reviewstatistics #ReviewStatistics.objects.get_or_create(user=self.owner)[0]
        if was_new:
            review_stats.increment_new_reviews()
        if grade == GRADE_NONE:
            review_stats.increment_failed_reviews()

        # Create Undo stack item
        UndoCardReview.objects.add_undo(card_history_item)

        # Adjust ease factor
        last_ease_factor = self.ease_factor
        self.ease_factor = self._next_ease_factor(grade, reviewed_at)
        self.last_ease_factor = last_ease_factor

        # Adjust interval
        last_interval = self.interval
        self.interval = self._next_interval(grade, self.ease_factor, reviewed_at)
        self.last_interval = last_interval
    
        # Determine next due date
        self.last_due_at = self.due_at
        self.due_at = self._next_due_at(grade, reviewed_at, self.interval)


        self.last_review_grade = grade
        self.last_reviewed_at = reviewed_at
        if grade == GRADE_NONE:
            self.last_failed_at = reviewed_at

        
        review_stats.save()
        self.save()







#TODO implement (remember to update UndoReview too)
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





