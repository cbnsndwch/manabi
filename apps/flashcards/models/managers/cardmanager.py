from django.db import models
from django.db.models import Avg, Max, Min, Count
from itertools import chain
from model_utils.managers import manager_from
import datetime
from flashcards.models.constants import \
    GRADE_NONE, GRADE_HARD, GRADE_GOOD, GRADE_EASY, \
    MAX_NEW_CARD_ORDINAL, EASE_FACTOR_MODIFIERS, \
    YOUNG_FAILURE_INTERVAL, MATURE_FAILURE_INTERVAL, MATURE_INTERVAL_MIN, \
    GRADE_EASY_BONUS_FACTOR, DEFAULT_EASE_FACTOR, INTERVAL_FUZZ_MAX, \
    NEW_CARDS_PER_DAY


class SchedulerMixin(object):
    '''
    '''
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
            cards = card_query.exclude(
                id__in=[card.id for card in delayed_cards]).select_related()
            cards = cards[:count]

            if early_review and len(cards) == 0:
                return delayed_cards[:count]

            for card in cards:
                min_space = card.sibling_spacing()
                for sibling in card.siblings:
                    if sibling.is_due(review_time) \
                            or sibling.id in excluded_ids \
                            or (sibling.last_reviewed_at \
                                and abs(card.due_at - sibling.last_reviewed_at) <= min_space):
                        #
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


    def _next_failed_due_cards(self, user, initial_query, count,
            review_time, excluded_ids=[], daily_new_card_limit=None,
            early_review=False, deck=None, tags=None):
        if not count:
            return []
        cards = initial_query.filter(
            last_review_grade=GRADE_NONE,
            due_at__lte=review_time).order_by('due_at')
        # Don't space these #self._space_cards(cards, count, review_time)
        return cards[:count] 

    def _next_not_failed_due_cards(self, user, initial_query, count,
            review_time, excluded_ids=[], daily_new_card_limit=None,
            early_review=False, deck=None, tags=None):
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
            due_at__lte=review_time).order_by('-interval')
        #TODO Also get cards that aren't quite due yet, but will be soon,
        # and depending on their maturity
        # (i.e. only mature cards due soon).
        # Figure out some kind of way to prioritize these too.
        return self._space_cards(due_cards, count, review_time)

    def _next_failed_not_due_cards(self, user, initial_query, count,
            review_time, excluded_ids=[], daily_new_card_limit=None,
            early_review=False, deck=None, tags=None):
        if not count:
            return []
        #TODO prioritize certain failed cards, not just by due date
        # We'll show failed cards even if they've been reviewed recently.
        # This is because failed cards are set to be shown 'soon' and not
        # just in 10 minutes. Special rules.
        #TODO we shouldn't show mature failed cards so soon though!
        #TODO randomize the order (once we fix the Undo)
        card_query = initial_query.filter(last_review_grade=GRADE_NONE, \
                due_at__gt=review_time).order_by('due_at') 
        return card_query[:count]

    def _next_new_cards(self, user, initial_query, count, review_time,
            excluded_ids=[], daily_new_card_limit=None, early_review=False,
            deck=None, tags=None):
        '''Gets the next new cards for this user or deck.
        '''
        from flashcards.models.facts import Fact
        if not count:
            return []

        new_card_query = initial_query.filter(
            due_at__isnull=True).order_by('new_card_ordinal')

        if daily_new_card_limit:
            new_reviews_today = user.reviewstatistics\
                                .get_new_reviews_today()
            if new_reviews_today >= daily_new_card_limit:
                return []
            # Count the number of new cards in the `excluded_ids`,
            # which the user already has queued up
            new_excluded_cards_count = self.filter(
                id__in=excluded_ids, due_at__isnull=True).count()
            new_count_left_for_today = (daily_new_card_limit
                                        - new_reviews_today
                                        - new_excluded_cards_count)
        else:
            new_count_left_for_today = None

        def _next_new_cards2():
            new_cards = []
            for card in new_card_query.select_related().iterator():
                min_space = card.sibling_spacing()

                for sibling in card.siblings:
                    # sibling is already included as a new card to be shown or
                    # sibling is currently in the client-side review queue or 
                    # sibling is due or
                    # sibling was reviewed recently or
                    # sibling is failed. Either it's due, or it's not due and it's shown before new cards.
                    if sibling in new_cards or \
                       sibling.id in excluded_ids or \
                       sibling.is_due(review_time) or \
                       (sibling.last_reviewed_at and \
                        abs(review_time - sibling.last_reviewed_at) <= min_space) or \
                       sibling.last_review_grade == GRADE_NONE:
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
            eligible_ids.extend([card.id for card in new_card_query.exclude(id__in=eligible_ids).select_related()[:count - len(eligible_ids)]])

        # Return a query containing the eligible cards.
        ret = self.filter(id__in=eligible_ids).order_by('new_card_ordinal')
        ret = ret[:min(count, new_count_left_for_today)] if daily_new_card_limit else ret[:count]
        return ret
            


    def _next_due_soon_cards(self, user, initial_query, count,
            review_time, excluded_ids=[], daily_new_card_limit=None,
            early_review=False, deck=None, tags=None):
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
            review_time, excluded_ids=[], daily_new_card_limit=None,
            early_review=False, deck=None, tags=None):
        if not count:
            return []
        priority_cutoff = review_time - datetime.timedelta(minutes=60)
        cards = initial_query.exclude(
            last_review_grade=GRADE_NONE).filter(
            due_at__gt=review_time).order_by('due_at')
        fresher_cards = cards.filter(
            last_reviewed_at__lte=priority_cutoff).order_by('due_at')
        return self._space_cards(
            fresher_cards, count, review_time, early_review=True)

    def _next_cards(self, early_review=False, daily_new_card_limit=None):
        card_funcs = [
            self._next_failed_due_cards,        # due, failed
            self._next_not_failed_due_cards,    # due, not failed
            self._next_failed_not_due_cards]    # failed, not due

        if early_review and daily_new_card_limit:
            card_funcs.extend([
                self._next_due_soon_cards,
                # due soon, not yet, but next in the future
                self._next_due_soon_cards2]) 
        else:
            card_funcs.extend([self._next_new_cards]) # new cards at end
        return card_funcs

    #TODO not sure what this is necessary for, actually - it's used in one 
    # place and can probably be merged with something else.
    def next_cards_count(self, user, excluded_ids=[], session_start=False,
            deck=None, tags=None, early_review=False,
            daily_new_card_limit=None, new_cards_only=False):
        now = datetime.datetime.utcnow()
        if new_cards_only:
            card_funcs = [self._next_new_cards]
        else:
            card_funcs = self._next_cards(
                early_review=early_review,
                daily_new_card_limit=daily_new_card_limit)
        user_cards = self._user_cards(
            user, deck=deck, excluded_ids=excluded_ids, tags=tags)
        count = 0
        cards_left = 99999 #TODO find a more elegant approach
        for card_func in card_funcs:
            cards = card_func(
                user, user_cards, cards_left, now, excluded_ids,
                daily_new_card_limit,
                early_review=early_review,
                deck=deck,
                tags=tags)
            count += cards.count()
        return count


    def next_cards(self, user, count, excluded_ids=[],
            session_start=False, deck=None, tags=None, early_review=False,
            daily_new_card_limit=None):
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
        card_funcs = self._next_cards(
            early_review=early_review,
            daily_new_card_limit=daily_new_card_limit)
        user_cards = self._user_cards(
            user, deck=deck, excluded_ids=excluded_ids, tags=tags)
        cards_left = count
        card_queries = []
        for card_func in card_funcs:
            if not cards_left:
                break

            cards = card_func(
                user, user_cards, cards_left, now, excluded_ids,
                daily_new_card_limit,
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



class CommonFiltersMixin(object):
    '''
    Provides filters for decks, tags.

    This is particularly useful with view URLs which take query params for 
    these things.
    '''
    #def of_user(self, user):
        #'''
        #Includes remote subscribed cards.
        #'''
        #facts = 
        #self.filter(

    def of_deck(self, deck):
        return self.filter(fact__deck=deck)

    def of_user(self, user):
        from flashcards.models.facts import Fact
        #TODO this is probably really slow
        user_cards = self.filter(suspended=False, active=True)
        facts = Fact.objects.with_synchronized(user)
        user_cards = self.filter(fact__in=facts)
        return user_cards

    #TODO just use of_user and of_deck etc. as mixins instead of this
    def _user_cards(self, user, deck=None, tags=None, excluded_ids=None):
        #TODO change excluded_ids=None to =[]
        from flashcards.models.facts import Fact
        user_cards = self.of_user(user)

        if deck:
            user_cards = user_cards.filter(fact__deck=deck)

        if tags:
            facts = usertagging.models.UserTaggedItem.objects.get_by_model(Fact, tags)
            user_cards = user_cards.filter(fact__in=facts)

        if excluded_ids:
            user_cards = user_cards.exclude(id__in=excluded_ids)
        return user_cards

    def new_cards(self, user, deck=None):
        return self.of_user(user).filter(last_reviewed_at__isnull=True,
                                         fact__deck=deck)

    def due_cards(self, user, deck=None):
        return self.of_user(user)\
            .filter(due_at__lte=datetime.datetime.utcnow(),
                    fact__deck=deck)\
            .order_by('-interval')

    #FIXME distinguish from cards_new_count or merge or make some new kind of review optioned class
    #TODO consolidate with next_cards (see below)
    #FIXME make it work for synced decks
    def new_cards_count(self, user, excluded_ids, deck=None, tags=None):
        '''
        Returns the number of new cards for the given review parameters.
        '''
        from flashcards.models.facts import Fact
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

    def count_of_cards_due_tomorrow(self, user, deck=None, tags=None):
        '''
        Returns the number of cards due by tomorrow at the same time 
        as now. Doesn't take future spacing into account though, so it's
        a somewhat rough estimate.
        '''
        from flashcards.models.facts import Fact
        cards = self.of_user(user)
        if deck:
            cards = cards.filter(fact__deck=deck)
        if tags:
            facts = usertagging.models.UserTaggedItem.objects.get_by_model(Fact, tags)
            cards = cards.filter(fact__in=facts)
        this_time_tomorrow = (datetime.datetime.utcnow()
                              + datetime.timedelta(days=1))
        cards = cards.filter(due_at__lt=this_time_tomorrow)
        due_count = cards.count()
        new_count = min(
            NEW_CARDS_PER_DAY,
            self.new_cards_count(user, [], deck=deck, tags=tags))
        return due_count + new_count

    def next_card_due_at(self, user, deck=None, tags=None):
        '''
        Returns the due date of the next due card.
        '''
        from flashcards.models.facts import Fact
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

    #def count(self, user, deck=None, tags=None):
        #cards = self.of_user(user)
        #if deck:
            #cards = cards.filter(fact__deck=deck)
        #if tags:
            #facts = usertagging.models.UserTaggedItem.objects.get_by_model(Fact, tags)
            #cards = cards.filter(fact__in=facts)
        #return cards.count()

    #def spaced_cards_new_count(self, user, deck=None):
        #threshold_at = datetime.datetime.utcnow() - datetime.timedelta(minutes=30)
        #recently_reviewed = self.filter(fact__deck__owner=user, fact__deck=deck, last_reviewed_at__lte=threshold_at)
        #facts = Fact.objects.filter(id__in=recently_reviewed.values_list('fact', flat=True))
        #new_cards_count = self.new_cards(user, deck).exclude(fact__in=facts).count()
        #return new_cards_count



CardManager = lambda: manager_from(CommonFiltersMixin, SchedulerMixin)
    

#class CardManager(models.Manager):
    
    ##set the base query set to only include cards of this user
    #def get_query_set(self):
    #    return super(UserCardManager, self).get_query_set().filter(




        
    #def _next_cards_initial_query(self, user, count, excluded_ids, session_start, deck=None, tags=None, early_review=False, daily_new_card_limit=None):





