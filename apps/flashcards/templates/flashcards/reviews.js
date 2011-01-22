// flashcard reviewing

dojo.provide('reviews');
dojo.provide('reviews.Card');
dojo.provide('reviews.Session');

//dojo.require('manabi');


reviews.grades = { GRADE_NONE: 0, GRADE_HARD: 3, GRADE_GOOD: 4, GRADE_EASY: 5 };

reviews.subscriptionNames = {
    sessionTimerTick: 'manabi.reviews.session_timer_tick',
    sessionTimerOver: 'manabi.reviews.session_timer_over',
    sessionCardLimitReached: 'manabi.reviews.session_card_limit_reached',
    sessionOver: 'manabi.reviews.session_over',
    cardReviewed: 'manabi.reviews.card_reviewed'
};

dojo.declare('reviews.Card', null, {
    constructor: function(jsonCard, session) {
        /* `json_card` is the JSON object representing a card from Django.*/
        dojo.safeMixin(this, jsonCard);
        this.session = session;
    },

    nextDueAt: function(grade) {
        // Returns a date for the next due date for the given grade
        return dojo.date.stamp.fromISOString(this.nextDueAtPerGrade[grade]);
    },

    suspend: function() {
        // Suspends this and sibling cards.
        xhrArgs = {
            url: '/flashcards/api/facts/' + this.factId + '/suspend/',
            handleAs: 'json',
            load: dojo.hitch(this, function(data) {
                if (data.success) {
                } else {
                    //FIXME try again on failure, or something
                }
            })
        };
        return dojo.xhrPost(xhrArgs);
    },

    review: function(grade) {
        xhrArgs = {
            url: '{% url api-cards %}' + this.id + '/',
            content: { grade: grade },
            handleAs: 'json',
            load: dojo.hitch(this, function(data) {
                if (data.success) {
                    this.session.cardsReviewedPending.splice(this.session.cardsReviewedPending.lastIndexOf(this.id), 1);
                } else {
                    //FIXME try again on failure, or something
                }
            })
        };

        //start sending the review in ASAP
        var def = dojo.xhrPost(xhrArgs);

        dojo.publish(reviews.subscriptionNames.cardReviewed, [{
            card: this,
            grade: grade,
            reviewDef: def
        }]);

        return def;
    }

});


dojo.declare('reviews.Session', null, {
    cards: [],

    //this is for cards that are reviewed, and have been submitted to the server
    //without a response yet.
    //It's a list of card IDs.
    cardBufferSize: 5,

    // Defaults (can be overriden via the constructor args)
    earlyReview: false,
    learnMore: false,

    // private values (TODO: prepend _)
    //TODO sensible args consolidated w/ view and reviews_ui.startSession
    reviewCount: 0,
    emptyPrefetchProducer: false,
    failsSincePrefetchRequest: 0,
    _prefetchInProgress: false,
    //this.session_over_def = new dojo.Deferred();
    emptyPrefetchProducer: false,

    constructor: function(args) {
        //Use deckId = -1 for all decks
        //Use tagId = -1 for no tag filter
        //timeLimit is in minutes
        //
        // Requires these arguments:
        //   deckId, dailyNewCardLimit, cardLimit, timeLimit, tagId, earlyReview, learnMore) {
        console.log('rev count:'+this.reviewCount);
        dojo.safeMixin(this, args);
        console.log('rev count:'+this.reviewCount);

        // Initialize non-primitive props
        this.currentCard = null;
        this.timer = null;
        this.cardsReviewedPending = [];
        this.cardsReviewedPendingDef = []; //contains the Deferred objects for each pending review

        this.reviewCountPerGrade = {};
        this.reviewCountPerGrade[reviews.grades.GRADE_NONE] = this.reviewCountPerGrade[reviews.grades.GRADE_HARD] = this.reviewCountPerGrade[reviews.grades.GRADE_GOOD] = this.reviewCountPerGrade[reviews.grades.GRADE_EASY] = 0,

        // Subscribe to card review events
        dojo.subscribe(reviews.subscriptionNames.cardReviewed, dojo.hitch(this, function(data) {
            this._cardReviewCallback(data.card, data.grade, data.reviewDef)
        }));
    },

    startSession: function() {
        // Always call this before doing anything else.
        // Returns a deferred.

        // Reset the review undo stack on the server.
        var def = new dojo.Deferred();
        reviews._simpleXHRPost('{% url api-reset_review_undo_stack %}').addCallback(dojo.hitch(this, function(def) {
            var prefetchDef = this.prefetchCards(this.cardBufferSize * 2, true);
            prefetchDef.addCallback(dojo.hitch(this, function(def, prefetch_item) {
                //start session timer - a published event
                this._startSessionTimer();

                def.callback(prefetch_item);
            }, def));
        }, def));

        //TODO cleanup beforehand? precautionary..
        return def;
    },

    endSession: function() {
        this._stopSessionTimer();

        //session over event
        dojo.publish(reviews.subscriptionNames.sessionOver, [{
            reviewCount: this.reviewCount,
            timeElapsed: this.endTime - this.startTime}]);

        //FIXME cleanup, especially once the dialog is closed prematurely, automatically
        this.cards = [];
        this.cardsReviewedPending = [];
        this.emptyPrefetchProducer = false;
    },

    successfulReviewCount: function() {
        return this.reviewCount - this.failedReviewCount();
    },

    failedReviewCount: function() {
        return this.reviewCountPerGrade[reviews.grades.GRADE_NONE];
    },

    _cardReviewCallback: function(card, grade, reviewDef) {
        // Handles the review event

        this.reviewCount++;
        this.reviewCountPerGrade[grade]++;

        //if this card failed, then the server may have more cards for us to prefetch
        //even if it was empty before
        if (grade == reviews.grades.GRADE_NONE) {
            //in case a prefetch request was made and has not been returned yet from the server
            this.failsSincePrefetchRequest++;
            //TODO don't keep showing this card if it's failed and it's the last card for the session
            this.emptyPrefetchProducer = false;
        }

        //check if the session should be over now (time or card limit is up)
        //now = new Date(); //FIXME consolidate with more recent timer stuff

        //add to review def queue
        this.cardsReviewedPendingDef.push(reviewDef);
        reviewDef.addCallback(dojo.hitch(this, function(reviewDef) {
            // remove the def from the queue once it's called
            this.cardsReviewedPendingDef.splice(this.cardsReviewedPendingDef.lastIndexOf(reviewDef), 1);
        }, reviewDef));

        //has the user reached the card review count limit?
        if (this.reviewCount >= this.cardLimit
                && this.cardLimit) {
            dojo.publish(reviews.subscriptionNames.sessionCardLimitReached, [{
                reviewCount: this.reviewCount,
                timeElapsed: this.endTime - this.startTime}]);
        }
    },

    prefetchCards: function(count, sessionStart) {
        //get next cards from server, discounting those currently enqueued/pending
        //Returns a deferred.
        this._prefetchInProgress = true;

        //serialize the excluded id list
        var excludedIds = [];
        dojo.forEach(this.cards,
            function(card, index) {
                if (excludedIds.lastIndexOf(card.id) == -1) {
                    excludedIds.push(card.id);
                }
        });
        dojo.forEach(this.cardsReviewedPending,
            function(cardId, index) {
                if (excludedIds.lastIndexOf(cardId) == -1) {
                    excludedIds.push(cardId);
                }
        });

        var url = '{% url api-next_cards_for_review %}';
        url += '?count=' + count;
        //FIXME camelcase these, and refactor
        if (sessionStart) { url += '&session_start=true'; }
        if (excludedIds.length > 0) { url += '&excluded_cards=' + excludedIds.join('+'); }
        if (this.deckId != '-1' && this.deckId !== null) { url += '&deck=' + this.deckId; }
        if (this.tagId != '-1' && this.tagId !== null) { url += '&tag=' + this.tagId; }
        if (this.earlyReview) { url += '&early_review=true'; }
        if (this.learnMore) { url += '&learn_more=true'; }

        var xhrArgs = {
            url: url,
            handleAs: 'json',
            load: dojo.hitch(this, function(data) {
                if (data.success) {
                    //start the session timer if it hasn't already been started
                    if (this.timer !== null) {
                    console.log(this.timer);
                    console.log(this);
                        if (!this.timer.isRunning) {
                            this.timer.start();
                        }
                    }
                    if (data.data.length > 0) {
                        dojo.forEach(data.data, dojo.hitch(this, function(card) {
                            //card = new reviews.Card(card);
                            card = new reviews.Card(card, this);
                            this.cards.push(card);
                        }));
                    }
                    if (data.data.length < count) {
                        //server has run out of cards for us
                        if (this.failsSincePrefetchRequest === 0) {
                            this.emptyPrefetchProducer = true;
                        }
                    }
                } else {
                    //error //FIXME it should redo the request
                }
                this._prefetchInProgress = false;
            })
        };

        this.failsSincePrefetchRequest = 0;

        return dojo.xhrGet(xhrArgs);
    },

    _startSessionTimer: function() {
        if (this.timer) {
            this.timer.stop();
            delete this.timer;
        }
        this.startTime = new Date();
        this.timer = new dojox.timing.Timer();
        this.timer.setInterval(1000); //in ms
        this.timer.onTick = dojo.hitch(this, function() {
            var time_now = new Date();
            var elapsed = time_now - this.startTime; //in ms
            //see if we're over the session time limit
            if (this.timeLimit
                    && this.timeLimit * 60000 <= elapsed) {
                this._stopSessionTimer();
            } else {
                dojo.publish(reviews.subscriptionNames.sessionTimerTick, [{
                    is_running: true,
                    timeElapsed: elapsed }]);
            }
        });
    },

    _stopSessionTimer: function() {
        if (this.timer) {
            if (this.timer.isRunning) {
                this.endTime = new Date();
                this.timer.stop();
                this.timer = null;
                var event_obj = {
                    is_running: false,
                    timeElapsed: this.endTime - this.startTime
                };
                dojo.publish(reviews.subscriptionNames.sessionTimerTick, [event_obj]);
                dojo.publish(reviews.subscriptionNames.sessionTimerOver, [event_obj]);
            }
        }
    },

    _nextCard: function() {
        //assumes we already have a non-empty card queue, and returns the next card.
        card = this.cards.shift();
                            console.log('pushin2');
                            console.log(this);
        this.cardsReviewedPending.push(card.id);
        this.currentCard = card;
        return card;
    },

    nextCard: function() {
        //Returns a deferred.

        //TODO -?-(done?)dont prefetch more cards if a prefetch is already in progress
        var nextCardDef = new dojo.Deferred();

        if (this.cards.length > 0) {
            nextCardDef.callback(this._nextCard());

            //prefetch more cards if the buffer runs low
            if (this.cards.length <= this.cardBufferSize) {
                if (!this.emptyPrefetchProducer && !this._prefetchInProgress) {
                    var prefetch_cards_def = this.prefetchCards(this.cardBufferSize, false);
                }
            }

        } else {
            if (!this.emptyPrefetchProducer && !this._prefetchInProgress) {
                //out of cards, need to fetch more
                var prefetchDef = this.prefetchCards(this.cardBufferSize * 2, false);
                prefetchDef.addCallback(dojo.hitch(this, function(nextCardDef) {
                    if (this.cards.length) {
                        nextCardDef.callback(this._nextCard());
                    } else {
                        nextCardDef.callback(null);
                    }
                }, nextCardDef));
            } else {
                nextCardDef.callback(null);
            }
        }

        return nextCardDef;
    },

    reloadCurrentCard: function() {
        //TODO refresh the card inside this.cards, instead of just setting current_cards
        var xhrArgs = {
            url: '{% url api-cards %}/' + this.currentCard.id + '/',
            handleAs: 'json',
            load: dojo.hitch(this, function(data) {
                if (data.success) {
                    this.currentCard = new reviews.Card(data.card, this);
                }
            })
        };
        return dojo.xhrGet(xhrArgs);
    },

    _resetCardBuffer: function() {
        // Resets the card cache, as well as the "currentCard"

        // Clear cache
        this.cardsReviewedPending.splice(this.cardsReviewedPending.lastIndexOf(this.currentCard.id), 1);
        this.cards = [];
        this.currentCard = null;

        // Refill it
        return this.prefetchCards(this.cardBufferSize * 2, true);
    },

    undo: function() {
        // Note that this will nullify currentCard. You'll have to call nextCard
        // after this is done (after its deferred is called).

        // Wait until the card review submission queue is clear before issuing the
        // undo, so that we don't accidentally undo earlier than intended.
        var review_defs = new dojo.DeferredList(this.cardsReviewedPendingDef);
        var undo_def = new dojo.Deferred();
        review_defs.addCallback(dojo.hitch(this, function(undo_def) {
            // Send undo request
            var actual_undo_def = reviews._simpleXHRPost('{% url api-undo_review %}');
            
            // Clear and refill card cache
            actual_undo_def.addCallback(dojo.hitch(this, function(undo_def) {
                this.reviewCount -= 1;
                this._resetCardBuffer().addCallback(dojo.hitch(this, function(undo_def) {
                    undo_def.callback();
                }, undo_def));
            }, undo_def));
        }, undo_def));
        return undo_def;
    },
});











reviews._simpleXHRPost = function(url) {
    var def = new dojo.Deferred();

    var xhrArgs = {
        url: url,
        handleAs: 'json',
        load: dojo.hitch(this, function(def, data) {
            if (data.success) {
                def.callback();
                //TODO return the data to the deferred
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
        load: dojo.hitch(this, function(def, data) {
            if (data.success) {
                if (typeof valueName == 'undefined') {
                    def.callback(data.data);
                } else {
                    def.callback(data.data[valueName]);
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

















