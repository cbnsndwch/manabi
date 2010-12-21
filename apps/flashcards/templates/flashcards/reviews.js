// flashcard reviewing

dojo.provide('reviews');
dojo.provide('reviews.Card');

dojo.declare('reviews.Card', null, {
    constructor: function(json_card) {
        /* `json_card` is the JSON object representing a card from Django.*/
        dojo.safeMixin(this, json_card);
    },

    nextDueAt: function(grade) {
        // Returns a date for the next due date for the given grade
        return dojo.date.stamp.fromISOString(this.nextDueAtPerGrade[grade]);
    }
});
	//dojo.date.stamp.fromISOString

//dojo.declare('reviews', null, {blah:function(){console.log('f');}});//reviews = {};
/*TODO convert to dojo declare syntax
  if(!dojo._hasResource['reviews']){
dojo._hasResource['reviews'] = true;
dojo.provide('reviews');
}*/
//reviews = {};

dojo.addOnLoad(function() {
    reviews.cards = [];
    
    //this is for cards that are reviewed, and have been submitted to the server
    //without a response yet.
    //It's a list of card IDs.
    reviews.cardBufferSize = 5;

    reviews.grades = { GRADE_NONE: 0, GRADE_HARD: 3, GRADE_GOOD: 4, GRADE_EASY: 5 };
    //reviews.session_over_def = null; //subscribe to this to know when the session is over,
                                     //particularly because the time/card limit ran out
});

reviews.subscriptionNames = {
    sessionTimerTick: '/manabi/reviews/session-timer-tick',
    sessionTimerOver: '/manabi/reviews/session-timer-over',
    sessionCardLimitReached: '/manabi/reviews/session-card-limit-reached',
    sessionOver: '/manabi/reviews/session-over'
};


reviews.prefetchCards = function(count, session_start) {
    //get next cards from server, discounting those currently enqueued/pending
    //Returns a deferred.
    reviews._prefetchInProgress = true;

    //serialize the excluded id list
    excludedIds = [];
    dojo.forEach(reviews.cards,
        function(card, index) {
            if (excludedIds.lastIndexOf(card.id) == -1) {
                excludedIds.push(card.id);
            }
    });
    dojo.forEach(reviews.cardsReviewedPending,
        function(cardId, index) {
            if (excludedIds.lastIndexOf(cardId) == -1) {
                excludedIds.push(cardId);
            }
    });

    var url = '{% url api-next_cards_for_review %}';
    url += '?count='+count;
    if (session_start) {
        url += '&session_start=true';
    }
    if (excludedIds.length > 0) {
        url += '&excluded_cards=' + excludedIds.join('+');
    }
    if (reviews.sessionDeckId != '-1') {
        url += '&deck=' + reviews.sessionDeckId;
    }
    if (reviews.sessionTagId != '-1') {
        url += '&tag=' + reviews.sessionTagId;
    }
    if (reviews.sessionEarlyReview) {
        url += '&early_review=true';
    }
    if (reviews.sessionLearnMore) {
        url += '&learn_more=true';
    }

    xhrArgs = {
        url: url,
        handleAs: 'json',
        load: function(data) {
            if (data.success) {
                //start the session timer if it hasn't already been started
                if (reviews.sessionTimer !== null) {
                    if (!reviews.sessionTimer.isRunning) {
                        reviews.sessionTimer.start();
                    }
                }
                if (data.cards.length > 0) {
                    dojo.forEach(data.cards, function(card) {
                        //card = new reviews.Card(card);
                        card = new reviews.Card(card);
                        console.log(card);
                        reviews.cards.push(card);
                    });
                }
                if (data.cards.length < count) {
                    //server has run out of cards for us
                    if (reviews.failsSincePrefetchRequest === 0) {
                        reviews.emptyPrefetchProducer = true;
                    }
                }
            } else {
                //error //FIXME it should redo the request
            }
            reviews._prefetchInProgress = false;
        }
    };

    reviews.failsSincePrefetchRequest = 0;

    return dojo.xhrGet(xhrArgs);
};

reviews._startSessionTimer = function() {
    if (reviews.sessionTimer) {
        reviews.sessionTimer.stop();
        delete reviews.sessionTimer;
    }
    reviews.sessionStartTime = new Date();
    reviews.sessionTimer = new dojox.timing.Timer();
    reviews.sessionTimer.setInterval(1000); //in ms
    reviews.sessionTimer.onTick = function() {
        var time_now = new Date();
        var elapsed = time_now - reviews.sessionStartTime; //in ms
        //see if we're over the session time limit
        if (reviews.sessionTimeLimit
                && reviews.sessionTimeLimit * 60000 <= elapsed) {
            reviews._stopSessionTimer();
        } else {
            dojo.publish(reviews.subscriptionNames.sessionTimerTick, [{
                is_running: true,
                timeElapsed: elapsed }]);
        }
    };
};

reviews._stopSessionTimer = function() {
    if (reviews.sessionTimer) {
        if (reviews.sessionTimer.isRunning) {
            reviews.sessionEndTime = new Date();
            reviews.sessionTimer.stop();
            reviews.sessionTimer = null;
            var event_obj = { is_running: false,
                              timeElapsed: reviews.sessionEndTime - reviews.sessionStartTime };
            dojo.publish(reviews.subscriptionNames.sessionTimerTick, [event_obj]);
            dojo.publish(reviews.subscriptionNames.sessionTimerOver, [event_obj]);
        }
    }
};

reviews.startSession = function(deckId, dailyNewCardLimt, sessionCardLimit, sessionTimeLimit, tag_id, earlyReview, learnMore) {
    if (typeof earlyReview == 'undefined') {
        earlyReview = false;
    }
    if (typeof learnMore == 'undefined') {
        learnMore = false;
    }
    //Use deckId = -1 for all decks
    //Use tag_id = -1 for no tag filter
    //sessionTimeLimit is in minutes
    //Always call this before doing anything else.
    //Returns a deferred.
    reviews.sessionDeckId = deckId;
    reviews.sessionTagId = tag_id;
    reviews.dailyNewCardLimt = dailyNewCardLimt;
    reviews.sessionCardLimit = sessionCardLimit;
    reviews.sessionTimeLimit = sessionTimeLimit;
    reviews.sessionCardsReviewedCount = 0;
    reviews.sessionEarlyReview = earlyReview;
    reviews.sessionLearnMore = learnMore;
    reviews.emptyPrefetchProducer = false;
    reviews.cardsReviewedPending = []; 
    reviews.cardsReviewedPendingDef = []; //contains the Deferred objects for each pending review
    reviews.currentCard = null;
    reviews.failsSincePrefetchRequest = 0;
    reviews.sessionTimer = null;
    reviews._prefetchInProgress = false;
    //reviews.session_over_def = new dojo.Deferred();
    reviews.emptyPrefetchProducer = false;

    // reset the review undo stack on the server
    var def = new dojo.Deferred();
    reviews._simpleXHRPost('{% url api-reset_review_undo_stack %}').addCallback(dojo.hitch(def, function(def) {
        var prefetchDef = reviews.prefetchCards(reviews.cardBufferSize * 2, true);
        prefetchDef.addCallback(dojo.hitch(def, function(def, prefetch_item) {
            //start session timer - a published event
            reviews._startSessionTimer();

            def.callback(prefetch_item);
        }, def));
    }, def));

    //TODO cleanup beforehand? precautionary..
    return def;
};


reviews.endSession = function() {
    reviews._stopSessionTimer();

    //session over event
    dojo.publish(reviews.subscriptionNames.sessionOver, [{
        cardsReviewedCount: reviews.sessionCardsReviewedCount,
        timeElapsed: reviews.sessionEndTime - reviews.sessionStartTime}]);

    //FIXME cleanup, especially once the dialog is closed prematurely, automatically
    reviews.cards = [];
    reviews.cardsReviewedPending = [];
    reviews.emptyPrefetchProducer = false;
};

reviews.reloadCurrentCard = function() {
    //TODO refresh the card inside reviews.cards, instead of just setting current_cards
    var xhrArgs = {
        url: '{% url api-cards %}/' + reviews.currentCard.id + '/',
        handleAs: 'json',
        load: function(data) {
            if (data.success) {
                reviews.currentCard = new reviews.Card(data.card);
            }
        }
    };
    return dojo.xhrGet(xhrArgs);
};

reviews._nextCard = function() {
    //assumes we already have a non-empty card queue, and returns the next card.
    card = reviews.cards.shift();
    reviews.cardsReviewedPending.push(card.id);
    reviews.currentCard = card;
    return card;
};

reviews.nextCard = function() {
    //Returns a deferred.

    //TODO -?-(done?)dont prefetch more cards if a prefetch is already in progress
    var nextCardDef = new dojo.Deferred();

    if (reviews.cards.length > 0) {
        nextCardDef.callback(reviews._nextCard());

        //prefetch more cards if the buffer runs low
        if (reviews.cards.length <= reviews.cardBufferSize) {
            if (!reviews.emptyPrefetchProducer && !reviews._prefetchInProgress) {
                var prefetch_cards_def = reviews.prefetchCards(reviews.cardBufferSize, false);
                /*prefetch_cards_def.addCallback(dojo.hitch(function(nextCardDef) {
                    //nextCardDef.callback(reviews._nextCard());
                }, null, nextCardDef));            */
            }
        }

    } else {
        if (!reviews.emptyPrefetchProducer && !reviews._prefetchInProgress) {
            //out of cards, need to fetch more
            var prefetchDef = reviews.prefetchCards(reviews.cardBufferSize * 2, false);
            prefetchDef.addCallback(dojo.hitch(null, function(nextCardDef) {
                if (reviews.cards.length) {
                    nextCardDef.callback(reviews._nextCard());
                } else {
                    nextCardDef.callback(null);
                }
            }, nextCardDef));
        } else {
            nextCardDef.callback(null);
        }
    }

    return nextCardDef;
};


reviews._resetCardCache = function() {
    // Resets the card cache, as well as the "currentCard"

    // Clear cache
    reviews.cardsReviewedPending.splice(reviews.cardsReviewedPending.lastIndexOf(reviews.currentCard.id), 1);
    reviews.cards = [];
    reviews.currentCard = null;

    // Refill it
    return reviews.prefetchCards(reviews.cardBufferSize * 2, true);
};


reviews.undo = function() {
    // Note that this will nullify currentCard. You'll have to call nextCard
    // after this is done (after its deferred is called).

    // Wait until the card review submission queue is clear before issuing the
    // undo, so that we don't accidentally undo earlier than intended.
    var review_defs = new dojo.DeferredList(reviews.cardsReviewedPendingDef);
    var undo_def = new dojo.Deferred();
    review_defs.addCallback(dojo.hitch(null, function(undo_def) {
        // Send undo request
        var actual_undo_def = reviews._simpleXHRPost('{% url api-undo_review %}');
        
        // Clear and refill card cache
        actual_undo_def.addCallback(dojo.hitch(null, function(undo_def) {
            reviews.sessionCardsReviewedCount -= 1;
            reviews._resetCardCache().addCallback(dojo.hitch(null, function(undo_def) {
                undo_def.callback();
            }, undo_def));
        }, undo_def));
    }, undo_def));
    return undo_def;
};

reviews.suspendCard = function(card) {
    // Suspends this and sibling cards.
    xhrArgs = {
        url: '/flashcards/api/facts/' + card.factId + '/suspend/',
        handleAs: 'json',
        load: function(data) {
            if (data.success) {
            } else {
                //FIXME try again on failure, or something
            }
        }
    };
    return dojo.xhrPost(xhrArgs);
};

reviews.reviewCard = function(card, grade) {
    xhrArgs = {
        url: '{% url api-cards %}' + card.id + '/',
        content: { grade: grade },
        handleAs: 'json',
        load: function(data) {
            if (data.success) {
                reviews.cardsReviewedPending.splice(reviews.cardsReviewedPending.lastIndexOf(card.id), 1);
            } else {
                //FIXME try again on failure, or something
            }
        }
    };

    reviews.sessionCardsReviewedCount++;

    //if this card failed, then the server may have more cards for us to prefetch
    //even if it was empty before
    if (grade == reviews.grades.GRADE_NONE) {
        //in case a prefetch request was made and has not been returned yet from the server
        reviews.failsSincePrefetchRequest++;
        //TODO don't keep showing this card if it's failed and it's the last card for the session
        reviews.emptyPrefetchProducer = false;
    }


    //check if the session should be over now (time or card limit is up)
    //now = new Date(); //FIXME consolidate with more recent timer stuff

    //start sending the review in ASAP
    var def = dojo.xhrPost(xhrArgs);

    //add to review def queue
    reviews.cardsReviewedPendingDef.push(def);
    def.addCallback(dojo.hitch(null, function(def) {
        // remove the def from the queue once it's called
        reviews.cardsReviewedPendingDef.splice(reviews.cardsReviewedPendingDef.lastIndexOf(def), 1);
    }, def));

    //has the user reached the card review count limit?
    if (reviews.sessionCardsReviewedCount >= reviews.sessionCardLimit
            && reviews.sessionCardLimit) {
        dojo.publish(reviews.subscriptionNames.sessionCardLimitReached, [{
            cardsReviewedCount: reviews.sessionCardsReviewedCount,
            timeElapsed: reviews.sessionEndTime - reviews.sessionStartTime}]);
    }

    return def;
};

reviews._simpleXHRPost = function(url) {
    var def = new dojo.Deferred();

    var xhrArgs = {
        url: url,
        handleAs: 'json',
        load: dojo.hitch(null, function(def, data) {
            if (data.success) {
                def.callback();
            } else {
                //TODO error handling (do a failure callback)
            }
        }, def)
    };
    dojo.xhrPost(xhrArgs);

    return def;
};


reviews._simpleXHRValueFetch = function(url, valueName) {
    // valueName is optional
    var def = new dojo.Deferred();

    var xhrArgs = {
        url: url,
        handleAs: 'json',
        load: dojo.hitch(null, function(def, data) {
            if (data.success) {
                if (typeof valueName == 'undefined') {
                    def.callback(data);
                } else {
                    def.callback(data[valueName]);
                }
            } else {
                //TODO error handling (do a failure callback)
            }
        }, def)
    };
    dojo.xhrGet(xhrArgs);

    return def;
};

reviews.dueCardCount = function() {
    return reviews._simpleXHRValueFetch('{% url api-due_card_count %}');
};

reviews.newCardCount = function() {
    return reviews._simpleXHRValueFetch('{% url api-new_card_count %}');
};

reviews.nextCardDueAt = function() {
    return reviews._simpleXHRValueFetch('{% url api-next_card_due_at %}');
};

reviews.timeUntilNextCardDue = function(deck, tags) {
    // Returns a float of the hours until the next card is due.
    var args = {};
    args.deck = deck || null;
    args.tags = tags || null;
    var query = dojo.objectToQuery(args);
    var url = '{% url api-hours_until_next_card_due %}';
    if (query) {
        url += '?' + query;
    }
    return parseInt(reviews._simpleXHRValueFetch(url), 10);
//    console.log(data);
//   return {hours: data['hoursUntilNextCardDue'], minutes: data['minutesUntilNextCardDue']};
};

reviews.countOfCardsDueTomorrow = function(deck) {
    var url = '{% url api-due_tomorrow_count %}';
    //TODO use dojo's url params api
    if (typeof deck != 'undefined' && deck) {
        url += '?deck='+deck;
    }
    return reviews._simpleXHRValueFetch(url);
};

















