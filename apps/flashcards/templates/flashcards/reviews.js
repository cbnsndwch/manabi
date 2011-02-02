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
    cardReviewed: 'manabi.reviews.card_reviewed',
    cardDisplayed: 'manabi.reviews.card_displayed'
};

dojo.declare('reviews.Card', null, {
    constructor: function(jsonCard, session) {
        /* `json_card` is the JSON object representing a card from Django.*/
        dojo.safeMixin(this, jsonCard);
        this.session = session;
        this.lastReviewGrade = null;
    },

    nextDueAt: function(grade) {
        // Returns a date for the next due date for the given grade
        return dojo.date.stamp.fromISOString(this.nextDueAtPerGrade[grade]);
    },

    stats: function() {
        // Retrieves general stats about this card, and returns them 
        // as a hash object.
        xhrArgs = {
            url: '/flashcards/api/'
        };
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

    review: function(grade, duration, questionDuration) {
        // `duration` is the time it took the user to show the answer.
        // It is optional.
        var duration = typeof duration === 'undefined' ? null : duration;
        var questionDuration = typeof questionDuration === 'undefined' ? null : questionDuration;

        xhrArgs = {
            url: '{% url api-cards %}' + this.id + '/',
            content: { grade: grade, duration: duration, questionDuration: questionDuration },
            handleAs: 'json',
            load: dojo.hitch(this, function(data) {
                if (data.success) {
                    // The XHR req was successful for reviewing this card...
                    // so remove the card from the pending-XHR queue.
                    this.session.cardsReviewedPending.splice(this.session.cardsReviewedPending.lastIndexOf(this.id), 1);
                } else {
                    //FIXME try again on failure, or something
                }
            })
        };

        //start sending the review in ASAP
        var def = dojo.xhrPost(xhrArgs);

        this.lastReviewGrade = grade;

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

    timeLimit: null,

    // private values (TODO: prepend _)
    //TODO sensible args consolidated w/ view and reviews_ui.startSession
    reviewCount: 0,
    emptyPrefetchProducer: false,
    failsSincePrefetchRequest: 0,
    _prefetchInProgress: false,
    //this.session_over_def = new dojo.Deferred();
    emptyPrefetchProducer: false,
    _sessionTimerInterval: 3000, // ms

    constructor: function(args) {
        //Use deckId = -1 for all decks
        //Use tagId = -1 for no tag filter
        //timeLimit is in minutes
        //
        // Requires these arguments:
        //   deckId, dailyNewCardLimit, cardLimit, timeLimit, tagId, earlyReview, learnMore) {
        dojo.safeMixin(this, args);

        // Initialize non-primitive props
        this.currentCard = null;
        this._prevCard = null;
        this.timer = null;
        this._endTime = null;
        this._resetQuestionTimer();
        this._resetCardTimer();

        this.cardsReviewedPending = [];
        this.cardsReviewedPendingDef = []; //contains the Deferred objects for each pending review

        // We can use this to get the count of unique cards reviewed. This will be >= this.reviewCount
        this.reviewedCardIds = [];

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
            timeElapsed: this.duration()
        }]);

        //FIXME cleanup, especially once the dialog is closed prematurely, automatically
        this.cards = [];
        this.cardsReviewedPending = [];
        this.emptyPrefetchProducer = false;
    },

    cardsReviewedCount: function() {
        // Returns the number of unique cards reviewed -- discount repeat reviews of the same card.
        return this.reviewedCardIds.length;
    },

    successfulReviewCount: function() {
        return this.reviewCount - this.failedReviewCount();
    },

    failedReviewCount: function() {
        return this.reviewCountPerGrade[reviews.grades.GRADE_NONE];
    },

    duration: function() {
        // Returns the time elapsed, either so far or until the end of the session,
        // whichever is earlier.
        var endTime = this._endTime ? this._endTime : new Date();
        return endTime - this._startTime;
    },

    startCardTimer: function() {
        // Same as startQuestionTimer, but for the entire duration that 
        // the current card is viewed, including its front and back.
        console.log('startCardTimer()');
        this.currentCardDuration = null;
        this._cardStartTime = new Date();
    },

    stopCardTimer: function() {
        // Also stores the return value in `this.currentCardDuration``
        if (this._cardStartTime) {
            var now = new Date();
            this.currentCardDuration = (now - this._cardStartTime) / 1000; // convert from ms to seconds.
            this._cardStartTime = null;
            return this.currentCardDuration;
        }
    },

    _resetCardTimer: function() {
        // Preps the timer for use.
        this.currentCardDuration = null;
        this._cardStartTime = null;
    },

    startQuestionTimer: function() {
        // Starts a timer for the current card
        // This is used for measuring how long the user takes to think of 
        // the answer to a card, before viewing the card's back.
        console.log('startQuestionTimer()');
        this.currentCardQuestionDuration = null;
        this._questionStartTime = new Date();
    },

    stopQuestionTimer: function() {
        // Ends the question timer, returning the elapsed time.
        // The elapsed duration is calculated in milliseconds, but converted
        // to seconds (floating-point).
        // Also stores the return value in `this.currentCardQuestionDuration`
        if (this._questionStartTime) {
            var now = new Date();
            this.currentCardQuestionDuration = (now - this._questionStartTime) / 1000; // convert from ms to seconds.
            this._questionStartTime = null;
            return this.currentCardQuestionDuration;
        }
    },

    _resetQuestionTimer: function() {
        // Preps the timer for use.
        this.currentCardQuestionDuration = null;
        this._questionStartTime = null;
    },

    _cardReviewCallback: function(card, grade, reviewDef) {
        // Handles the review event

        this.reviewCount++;
        this.reviewCountPerGrade[grade]++;

        if (dojo.indexOf(this.reviewedCardIds, card.id) == -1) {
            this.reviewedCardIds.push(card.id);
        }

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
                timeElapsed: this.duration()
            }]);
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
        this._startTime = new Date();
        this.timer = new dojox.timing.Timer();
        this.timer.setInterval(this._sessionTimerInterval); //in ms

        this.timer.onTick = dojo.hitch(this, function() {

            //see if we're over the session time limit
            //`timeLimit` is in minutes. `duration()` is ms.
            if (this.timeLimit && this.timeLimit * 60000 <= this.duration()) {
                //this._stopSessionTimer();
                //TODO: need something which tells the session to end after the current card
                //without actually stopping the timer until the session is actually fully over.
                //We don't actually use this yet.
            } else {
                dojo.publish(reviews.subscriptionNames.sessionTimerTick, [{
                    is_running: true,
                    timeElapsed: this.duration()
                }]);
            }
        });
    },

    _stopSessionTimer: function() {
        if (this.timer) {
            if (this.timer.isRunning) {
                this._endTime = new Date();
                this.timer.stop();
                this.timer = null;
                var event_obj = {
                    is_running: false,
                    timeElapsed: this.duration()
                };
                dojo.publish(reviews.subscriptionNames.sessionTimerTick, [event_obj]);
                dojo.publish(reviews.subscriptionNames.sessionTimerOver, [event_obj]);
            }
        }
    },

    _nextCard: function() {
        //assumes we already have a non-empty card queue, and returns the next card.
        card = this.cards.shift();
        this.cardsReviewedPending.push(card.id);
        this._prevCard = this.currentCard;
        this.currentCard = card;

        this._resetQuestionTimer();
        this._resetCardTimer();

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
                    this._prevCard = this.currentCard;
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
        this._prevCard = null;
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
                // undo our record-keeping
                console.log('prevcard:');
                console.log(this._prevCard);
                this.reviewCount -= 1;
                this.reviewCountPerGrade[this._prevCard.lastReviewGrade]--;
                this.reviewedCardIds.splice(this.reviewedCardIds.indexOf(this._prevCard.id), 1);

                this._resetCardBuffer().then(dojo.hitch(this, function(undo_def) {
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

















