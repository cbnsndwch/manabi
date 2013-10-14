import datetime
from itertools import chain

from django.db import models
from django.db.models.query import QuerySet
from django.db.models import Avg, Max, Min, Count
from model_utils.managers import PassThroughManager

from manabi.apps.manabi_redis.models import redis
from manabi.apps.flashcards.models.constants import (
    GRADE_NONE, GRADE_HARD, GRADE_GOOD, GRADE_EASY,
    MAX_NEW_CARD_ORDINAL, EASE_FACTOR_MODIFIERS,
    YOUNG_FAILURE_INTERVAL, MATURE_FAILURE_INTERVAL, MATURE_INTERVAL_MIN,
    GRADE_EASY_BONUS_FACTOR, DEFAULT_EASE_FACTOR, INTERVAL_FUZZ_MAX)


class SchedulerMixin(object):
    '''
    Contains the functions for retrieving the next cards that are 
    ready to be reviewed.
    '''
    def _space_cards(self, card_query, count, review_time,
            excluded_ids=[], early_review=False):
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
        # Keep track of new cards we want to skip,
        # since we shouldn't set their due_at (via delay())
        delayed_cards = [] 

        # REDIS WIP
        #while True:
        #    cards = card_query.exclude(
        #        id__in=[card.id for card in delayed_cards])
        #    card_ids = cards[:count].values_list('id', flat=True)

        #    if early_review and len(cards) == 0:
        #        return delayed_cards[:count]

        #    # get cards to delay.
        #    # get fact IDs
        #    # get zrange of score > 
        #    for card in cards:
        #        min_space = card.sibling_spacing()
        #        fact_id = card.fact_id
        #        if redis.zrangebyscore()

        while True:
            cards_delayed = 0
            cards = card_query.exclude(
                id__in=[card.id
                        for card
                        in delayed_cards]).select_related()
            cards = cards[:count]

            if early_review and len(cards) == 0:
                return delayed_cards[:count]

            for card in cards:
                min_space = card.sibling_spacing()
                for sibling in card.siblings:
                    if sibling.is_due(review_time) \
                            or sibling.id in excluded_ids \
                            or (sibling.last_reviewed_at \
                                and abs(card.due_at
                                        - sibling.last_reviewed_at)
                                <= min_space):
                        # Delay the card. It's already sorted by priority,
                        # so we delay this one instead of its sibling.
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

    def _next_failed_due_cards(self, user, initial_query, count,
            review_time, excluded_ids=[],
            early_review=False, deck=None, tags=None, **kwargs):
        if not count:
            return []
        cards = initial_query.filter(
            last_review_grade=GRADE_NONE,
            due_at__isnull=False,
            due_at__lte=review_time).order_by('due_at')
        # Don't space these #self._space_cards(cards, count, review_time)
        return cards[:count] 

    def _next_not_failed_due_cards(self, user, initial_query, count,
            review_time, excluded_ids=[],
            early_review=False, deck=None, tags=None, **kwargs):
        '''
        Returns the first [count] cards from initial_query which are due,
        weren't failed the last review, and  taking spacing of cards from
        the same fact into account.
        
        review_time should be datetime.datetime.utcnow()
        '''
        if not count:
            return []
        due_cards = initial_query.exclude(
            last_review_grade=GRADE_NONE).filter(
            due_at__isnull=False,
            due_at__lte=review_time).order_by('-interval')
        #TODO-OLD Also get cards that aren't quite due yet, but will be soon,
        # and depending on their maturity
        # (i.e. only mature cards due soon).
        # Figure out some kind of way to prioritize these too.
        return self._space_cards(due_cards, count, review_time)

    def _next_failed_not_due_cards(self, user, initial_query, count,
            review_time, excluded_ids=[], 
            early_review=False, deck=None, tags=None, **kwargs):
        if not count:
            return []
        #TODO-OLD prioritize certain failed cards, not just by due date
        # We'll show failed cards even if they've been reviewed recently.
        # This is because failed cards are set to be shown 'soon' and not
        # just in 10 minutes. Special rules.
        #TODO-OLD we shouldn't show mature failed cards so soon though!
        #TODO-OLD randomize the order (once we fix the Undo)
        card_query = initial_query.filter(last_review_grade=GRADE_NONE, \
                due_at__gt=review_time).order_by('due_at') 
        return card_query[:count]

    def _next_new_cards(self, user, initial_query, count, review_time,
            excluded_ids=[], early_review=False, learn_more=False,
            deck=None, tags=None,
            add_upstream_facts_as_needed=True, **kwargs):
        ''' Gets the next new cards for this user or deck. '''
        from manabi.apps.flashcards.models.facts import Fact

        if not count:
            return []

        new_card_query = initial_query.filter(
                due_at__isnull=True).order_by('new_card_ordinal')

        def _next_new_cards2():
            new_cards = []
            for card in new_card_query.iterator():
                min_space = card.sibling_spacing()

                for sibling in card.siblings:
                    # sibling is already included as a new card to be shown or
                    # sibling is currently in the client-side review queue or 
                    # sibling is due or
                    # sibling was reviewed recently or
                    # sibling is failed. Either it's due, or it's not due and it's shown before new cards.
                    if (sibling in new_cards
                        or sibling.id in excluded_ids
                        or sibling.is_due(review_time)
                        or (sibling.last_reviewed_at and 
                            abs(review_time - sibling.last_reviewed_at)
                            <= min_space)
                        or sibling.last_review_grade == GRADE_NONE):
                        break
                else:
                    # Only add the card if none of the 
                    # conditions above matched for its siblings.
                    new_cards.append(card)

                    # Got enough cards?
                    if len(new_cards) == count: #or \
                       #(new_count_left_for_today is not None and not early_review and len(new_cards) == new_count_left_for_today):
                        break

            return new_cards

        new_cards = _next_new_cards2()

        if add_upstream_facts_as_needed and len(new_cards) < count:
            # Still have fewer cards than requested.
            # See if we can get new cards from synchronized decks.
            facts_added = Fact.objects.add_new_facts_from_synchronized_decks(
                    user, count - len(new_cards), deck=deck, tags=tags)
            if len(facts_added):
                # Got new facts from a synchronized deck.
                # Get cards from them by re-getting new cards
                new_cards = _next_new_cards2()

        eligible_ids = [card.id for card in new_cards]

        if (early_review or learn_more) and len(eligible_ids) < count:
            # Queue up spaced cards if needed for early review.
            eligible_ids.extend([card.id for card in new_card_query.exclude(
                                    id__in=eligible_ids).select_related()
                                    [:count - len(eligible_ids)]])

        # Return a query containing the eligible cards.
        ret = self.filter(id__in=eligible_ids).order_by('new_card_ordinal')
        ret = ret[:count]
        return ret

    def _next_due_soon_cards(self, user, initial_query, count,
            review_time, excluded_ids=[], 
            early_review=False, deck=None, tags=None, **kwargs):
        '''
        Used for early review.
        Ordered by due date.
        '''
        if not count:
            return []
        priority_cutoff = review_time - datetime.timedelta(minutes=60)
        cards = initial_query.exclude(
            last_review_grade=GRADE_NONE).filter(
            due_at__gt=review_time).order_by('due_at')
        staler_cards = cards.filter(
            last_reviewed_at__gt=priority_cutoff).order_by('due_at')
        return self._space_cards(
            staler_cards, count, review_time, early_review=True)

    def _next_due_soon_cards2(self, user, initial_query, count,
            review_time, excluded_ids=[], 
            early_review=False, deck=None, tags=None, **kwargs):
        if not count:
            return []
        priority_cutoff = review_time - datetime.timedelta(minutes=60)
        cards = initial_query.exclude(
            last_review_grade=GRADE_NONE).filter(
            due_at__gt=review_time).order_by('due_at')
        fresher_cards = cards.filter(
            last_reviewed_at__isnull=False,
            last_reviewed_at__lte=priority_cutoff).order_by('due_at')
        return self._space_cards(
            fresher_cards, count, review_time, early_review=True)

    def _next_cards(self, early_review=False, learn_more=False):
        card_funcs = [
            self._next_failed_due_cards,        # due, failed
            self._next_not_failed_due_cards,    # due, not failed
            self._next_failed_not_due_cards]    # failed, not due

        if early_review and learn_more:
            raise Exception(
                    'Cannot set both early_review and learn_more together.')

        if early_review:
            card_funcs.extend([
                self._next_due_soon_cards,
                # due soon, not yet, but next in the future
                self._next_due_soon_cards2]) 
        elif learn_more:
            # Only new cards, and ignore spacing.
            card_funcs = [self._next_new_cards]
        else:
            card_funcs.extend([self._next_new_cards]) # new cards at end
        return card_funcs

    def next_cards(self, user, count, excluded_ids=[],
            session_start=False, deck=None, tags=None,
            early_review=False, learn_more=False):
        '''
        Returns `count` cards to be reviewed, in order.
        count should not be any more than a short session of cards
        set `early_review` to True for reviewing cards early 
        (following any due cards)

        If learn_more is True, only new cards will be chosen,
        even if they were spaced due to sibling reviews.

        "Due soon" cards won't be chosen in this case,
        contrary to early_review's normal behavior.

        (#TODO-OLD consider changing this to have a separate option)
        '''
        #TODO-OLD somehow spread some new cards into the early review 
        # cards if early_review==True
        #TODO-OLD use args instead, like *kwargs etc for these funcs
        now = datetime.datetime.utcnow()
        card_funcs = self._next_cards(
            early_review=early_review, learn_more=learn_more)

        user_cards = self.common_filters(user,
            deck=deck, excluded_ids=excluded_ids, tags=tags)

        cards_left = count
        card_queries = []

        for card_func in card_funcs:
            if not cards_left:
                break

            cards = card_func(
                user, user_cards, cards_left, now, excluded_ids,
                early_review=early_review,
                learn_more=learn_more,
                deck=deck,
                tags=tags)

            cards_left -= len(cards)

            if len(cards):
                card_queries.append(cards)

        #TODO-OLD decide what to do with this #if session_start:
        #FIXME add new cards into the mix when there's a defined 
        # new card per day limit
        #for now, we'll add new ones to the end
        return chain(*card_queries)


class CommonFiltersMixin(object):
    '''
    Provides filters for decks, tags, maturity level, etc.

    This is particularly useful with view URLs which take query params for 
    these things.
    '''
    def available(self):
        ''' Cards which are active and unsuspended. '''
        return self.filter(active=True, suspended=False)

    def of_deck(self, deck, with_upstream=False):
        deck_key = 'cards:deck:{0}'.format(deck.id)
        if with_upstream and deck.synchronized_with:
            sync_deck_key = 'cards:deck:{0}'.format(deck.synchronized_with_id)
            card_ids = redis.sunion(deck_key, sync_deck_key)
        else:
            card_ids = redis.smembers(deck_key)
        return self.filter(id__in=card_ids)

    def of_user(self, user):
        return self.filter(deck__owner=user)

    def with_tags(self, tags):
        from manabi.apps.flashcards.models.facts import Fact
        from manabi.apps.usertagging.models import UserTaggedItem

        facts = UserTaggedItem.objects.get_by_model(Fact, tags)
        return self.filter(fact__in=facts)

    def exclude_ids(self, excluded_ids):
        return self.exclude(id__in=excluded_ids)

    def unsuspended(self):
        return self.filter(suspended=False)

    def common_filters(self, user,
            deck=None, tags=None, excluded_ids=None):
        cards = self.of_user(user).unsuspended().filter(active=True)

        if deck:
            cards = cards.of_deck(deck, with_upstream=with_upstream)
        else:
            cards = cards.exclude(fact__deck__owner=user,
                                  fact__deck__suspended=True)

        if excluded_ids:
            cards = cards.exclude_ids(excluded_ids)
        if tags:
            cards = cards.with_tags(tags)
        return cards

    def new(self, user):
        return self.filter(
                last_reviewed_at__isnull=True).without_upstream(user)
    
    def new_count(self, user):
        '''
        Use this rather than `new(user).count()`, since this will
        count upstream cards properly.

        Any uncopied upstream cards are to be considered "new".
        '''
        return self.new(user).count() + self.of_upstream(user).count()

    def approx_new_count(self, user=None, deck=None):
        '''
        Approximates how many new cards are actually available to review.
        Will be between what new_count and unspaced_new_count return,
        but much faster than the latter.
        '''
        cards = self.available()
        if deck:
            cards = cards.of_deck(deck)
        return (cards.new(user).values_list('fact_id').distinct().count() +
                cards.of_upstream(user).values_list('fact_id').distinct().count())

    def unspaced_new_count(self, user):
        '''
        Same as `new_count`, except it subtracts new cards that 
        will be delayed due to sibling spacing (cards which haven't
        been spaced.)

        Works properly with upstream cards.
        '''
        local_query = self.new(user)
        desired_count = 999999 #TODO-OLD use more elegant solution.
        now = datetime.datetime.utcnow()
        local = self._next_new_cards(user, local_query, desired_count, now,
                add_upstream_facts_as_needed=False).count()

        # Count the number of upstream cards -- they are all "new".
        # But only count one card per distinct fact, to simulate
        # the effect of sibling spacing.
        upstream = self.of_upstream(user).values('fact_id').distinct().count()

        return local + upstream

    def young(self, user):
        return self.filter(
                last_reviewed_at__isnull=False,
                interval__isnull=False,
                interval__lt=MATURE_INTERVAL_MIN
                ).without_upstream(user)

    def mature(self, user):
        return self.filter(
                interval__gte=MATURE_INTERVAL_MIN
                ).without_upstream(user)

    def due(self, user, _space_cards=True):
        '''
        `_space_cards` is whether to space out due cards before returning
        them (which can result in fewer being returned).

        Excludes upstream cards that the user doesn't own.
        '''
        now = datetime.datetime.utcnow()
        due_cards = self.filter(
            due_at__isnull=False,
            due_at__lte=now).without_upstream(user)

        if _space_cards:
            self._space_cards(due_cards, due_cards.count(), now)

            # Re-get them since some may have been spaced
            due_cards = due_cards.filter(
                due_at__lte=now)

        return due_cards.order_by('-interval')

    def count_of_cards_due_tomorrow(self, user):
        '''
        Returns the number of cards due by tomorrow at the same time 
        as now. Doesn't take future spacing into account though, so it's
        a somewhat rough estimate.

        No longer includes new cards in its count.
        '''
        #from manabi.apps.flashcards.models.facts import Fact
        #cards = self.of_user(user)
        #if deck:
        #    cards = cards.filter(fact__deck=deck)
        #if tags:
        #    facts = usertagging.models.UserTaggedItem.objects.get_by_model(
        #            Fact, tags)
        #    cards = cards.filter(fact__in=facts)

        this_time_tomorrow = (datetime.datetime.utcnow()
                              + datetime.timedelta(days=1))
        cards = self.filter(
            due_at__isnull=False,
            due_at__lt=this_time_tomorrow).without_upstream(user)
        due_count = cards.count()

        #new_count = self.new().count()
        #new_count = self.common_filters(
                #user, deck=deck, tags=tags, with_upstream=True).new().count()
        #new_count = min(
            #NEW_CARDS_PER_DAY,
            #self.new_cards_count(user, [], deck=deck, tags=tags))
        #return due_count + new_count
        return due_count

    def next_card_due_at(self):
        '''
        Returns the due date of the next due card.
        If one is already due, this will be in the past.
        '''
        return self.aggregate(Min('due_at'))['due_at__min']

    #def spaced_cards_new_count(self, user, deck=None):
        #threshold_at = datetime.datetime.utcnow() - datetime.timedelta(minutes=30)
        #recently_reviewed = self.filter(fact__deck__owner=user, fact__deck=deck, last_reviewed_at__lte=threshold_at)
        #facts = Fact.objects.filter(id__in=recently_reviewed.values_list('fact', flat=True))
        #new_cards_count = self.new_cards(user, deck).exclude(fact__in=facts).count()
        #return new_cards_count

class CardStatsMixin(object):
    '''Stats data methods, primarily used for graphs and things.'''

    def with_due_dates(self):
        '''
        Adds a `due_on` DateField-like value. Same as `due_at` minus its 
        time information -- so just the day.
        '''
        return self.extra(select={'due_on': 'date(due_at)'})

    def due_counts(self):
        '''Number of cards due per day in the future.'''
        return self.with_due_dates().values('due_on').annotate(
            due_count=Count('id'))

    def due_today_count(self):
        '''The # of cards already due right now or later today.'''
        return self.filter(
            due_at__isnull=False,
            due_at__lte=datetime.datetime.today()).count()

    def future_due_counts(self):
        '''Same as `due_counts` but only for future, after today.'''
        return self.filter(
            due_at__gt=datetime.datetime.today()).with_due_dates().values(
            'due_on').annotate(due_count=Count('id'))


class CardQuerySet(CommonFiltersMixin, SchedulerMixin, CardStatsMixin, QuerySet):
    pass

