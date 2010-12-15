// flashcard reviewing




//dojo.declare('reviews', null, {blah:function(){console.log('f');}});//reviews = {};
/*TODO convert to dojo declare syntax
  if(!dojo._hasResource['reviews']){
dojo._hasResource['reviews'] = true;
dojo.provide('reviews');
}*/
reviews = {};

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
                    reviews.cards = reviews.cards.concat(data.cards);
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
                reviews.currentCard = data.card;
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
        url: '{% url api-cards %}/' + card.id,
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

















// user interface functions for reviews

reviews_ui = {};


dojo.addOnLoad(function() {
    reviews_ui.reviewOptionsDialog = dijit.byId('reviews_reviewDialog');
    reviews_ui.review_dialog = dijit.byId('reviews_fullscreenContainer');
    reviews_ui.sessionStarted = false;

});

reviews_ui.humanizedInterval = function(interval) {
    var ret = null;
    var duration = null;
    interval = parseFloat(interval);

    if ((interval * 24 * 60) < 1) {
        //less than a minute
        ret = 'Soon';
    } else if ((interval * 24) < 1) {
        //less than an hour: show minutes
        duration = Math.round(interval * 24 * 60);
        ret = duration + ' minute';
    } else if (interval < 1) {
        //less than a day: show hours
        duration = Math.round(interval * 24);
        if (duration == 24) {
            duration = 1;
            ret = '1 day';
        } else {
            ret = duration + ' hour';
        }
    } else {
        //days
        duration = Math.round(interval);
        ret = duration + ' day'; //TODO how to round?
    }

    if (duration >= 2) {
        //pluralize
        ret += 's';
    }
    
    return ret;
};

reviews_ui._showNoCardsDue = function() {
    dojo.byId('reviews_beginReview').style.display = 'none';
    dojo.byId('reviews_reviewScreen').style.display = 'none';
    dojo.byId('reviews_reviewEndScreen').style.display = 'none';
};


reviews_ui._humanizeDuration = function(hours) {
    // Returns a humanized duration.
    // If hours < 1/60, returns "under a minute"
    // If hours < 1, returns "n minutes"
    // Otherwise, "n hours"
    var minutes = hours / 60;
    if (minutes < 1) {
        return 'under a minute';
    } else if (hours < 1) {
        return minutes + ' minutes';
    } else {
        return hours + ' hours';
    }
};

reviews_ui._humanizedTimeUntil = function(timeUntil) {
    var minutesUntil = parseInt(timeUntil.minutesUntilNextCardDue) || -1;
    var hoursUntil = parseInt(timeUntil.hoursUntilNextCardDue, 10) || -1;
    if (hoursUntil > 0) {
    //if (parseInt(timeUntil['hoursUntilNextCardDue']) > 0) {
        return hoursUntil + ' hours'; //timeUntil['hoursUntilNextCardDue'] + ' hours';
    } else if (minutesUntil > 0) { //parseInt(timeUntil['minutesUntilNextCardDue']) > 0) {
        return minutesUntil + ' minutes'; //timeUntil['minutesUntilNextCardDue'] + ' minutes';
    } else {
        return 'under a minute';
    }
};


reviews_ui.showNoCardsDue = function(canLearnMore, emptyQuery) {
    reviews_beginReviewButton.attr('disabled', true);
    if (!reviews_ui.reviewOptionsDialog.attr('open')) {
        //reviews_ui.reviewOptionsDialog.show();
        reviews_ui.openDialog();
    }

    reviews_ui._showNoCardsDue();

    if (!canLearnMore && emptyQuery) {
        reviews_beginEarlyReviewButton.attr('disabled', true);
        dojo.byId('reviews_emptyQuery').style.display = '';
    } else {
        reviews.timeUntilNextCardDue(reviews_ui.lastSessionArgs.deckId, reviews_ui.lastSessionArgs.tag_id).addCallback(function(hoursUntil) {
            if (hoursUntil > 24) {
                reviews.nextCardDueAt().addCallback(function(next_due_at) {
                    dojo.byId('reviews_noCardsDueNextDueAt').innerHTML = 'The next card is due at: ' + next_due_at;
                    dojo.byId('reviews_noCardsDue').style.display = '';
                });
            } else {
                dojo.byId('reviews_noCardsDueNextDueAt').innerHTML = 'The next card is due in ' + reviews_ui._humanizeDuration(hoursUntil);
                dojo.byId('reviews_noCardsDue').style.display = '';
            }
        });
        dojo.byId('reviews_learnMoreContainer').style.display = canLearnMore ? '' : 'none';
        reviews_learnMoreButton.attr('disabled', !canLearnMore);
        reviews_beginEarlyReviewButton.attr('disabled', false);
    }

};

reviews_ui.showReviewOptions = function() {
    //FIXME temp fix dojo.byId('reviews_beginReview').style.display = '';
    dojo.byId('reviews_beginReview').style.display = 'none';
    dojo.byId('reviews_noCardsDue').style.display = 'none';
    dojo.byId('reviews_emptyQuery').style.display = 'none';
    dojo.byId('reviews_reviewEndScreen').style.display = 'none';
    reviews_beginReviewButton.attr('disabled', false);
    reviews_beginEarlyReviewButton.attr('disabled', true);
};


reviews_ui.openDialog = function() {
    //TODO first check if there are any cards due (using default review options? or special request to server)

    //show the options screen
    reviews_ui.showReviewOptions();
    reviews_ui.reviewOptionsDialog.tabStart = reviews_beginReviewButton;

    reviews_ui.reviewOptionsDialog.show();

    reviews_decksGrid.store.close();
    reviews_decksGrid.store.fetch({
        onComplete: function() {
            reviews_decksGrid.sort();
            reviews_decksGrid.resize();
            
            //reset the deck selection
            reviews_decksGrid.selection.setSelected(reviews_decksGrid.selection.selectedIndex, false);
            reviews_decksGrid.selection.setSelected(0, true);
        }
    });
};


reviews_ui.openSessionOverDialog = function(reviewCount) {
    // get the # due tomorrow to display
    reviews.countOfCardsDueTomorrow(reviews_ui.lastSessionArgs.deckId).addCallback(function(count) {
        if (count === 0) {
            // None due by this time tomorrow, so we'll get the time when one
            // is next due.
            reviews.timeUntilNextCardDue(reviews_ui.lastSessionArgs.deckId, reviews_ui.lastSessionArgs.tag_id).addCallback(function(hoursUntil) {
                dojo.byId('reviews_sessionOverDialogNextDue').innerHTML = 'The next card is due in ' + reviews_ui._humanizeDuration(hoursUntil);
                dojo.byId('reviews_sessionOverDialogReviewCount').innerHTML = reviewCount;
                reviews_sessionOverDialog.show();
            });
        } else {
            dojo.byId('reviews_sessionOverDialogNextDue').innerHTML = 'At this time tomorrow, there will be ' + count + ' cards due for review.';
            dojo.byId('reviews_sessionOverDialogReviewCount').innerHTML = reviewCount;
            reviews_sessionOverDialog.show();
        }
    });

};


reviews_ui.endSession = function() {
    reviews_ui.unsetKeyboardShortcuts();

    reviews_ui._unsubscribeFromSessionEvents();

    //show the page behind this
    dojo.byId('body_contents').style.display = '';

    dojo.byId('reviews_fullscreenContainer').style.display = 'none';
    //TODO fade out, less harsh
    //TODO show review session results
    var reviewCount = reviews.sessionCardsReviewedCount;
    reviews.endSession();

    if (reviewCount) {
        reviews_ui.openSessionOverDialog(reviewCount);

        // refresh the active page, in case it has due card counts etc
        manabi_ui.xhrReload();
    }

    reviews_ui.sessionStarted = false;
};


reviews_ui.displayNextIntervals = function(card) {
    //show a special message for card failures
    //FIXME but only for young card failures - mature cards should have an interval shown
    dojo.byId('reviews_gradeNoneInterval').innerHTML = 'Review soon';
    dojo.byId('reviews_gradeHardInterval').innerHTML = reviews_ui.humanizedInterval(card.nextDueAtPerGrade['3']);
    dojo.byId('reviews_gradeGoodInterval').innerHTML = reviews_ui.humanizedInterval(card.nextDueAtPerGrade['4']);
    dojo.byId('reviews_gradeEasyInterval').innerHTML = reviews_ui.humanizedInterval(card.nextDueAtPerGrade['5']);
};


reviews_ui.displayCard = function(card, show_card_back) {
    reviews_ui.cardBackVisible = false;
    reviews_ui.unsetCardBackKeyboardShortcuts();
    reviews_cardFront.attr('content', card.front);
    dojo.byId('reviews_showCardBack').style.display = '';
    reviews_cardBack.attr('content', card.back);
    reviews_cardBack.domNode.style.display = 'none';
    reviews_subfactPane.attr('content', '');
    reviews_subfactPane.domNode.style.display = 'none';
    dojo.byId('reviews_gradeButtonsContainer').style.visibility = 'hidden';
    if (show_card_back) {
        reviews_ui.showCardBack(card);
    } else {
        reviews_ui.setCardFrontKeyboardShortcuts();
        reviews_showCardBackButton.attr('disabled', false);
        reviews_showCardBackButton.focus();
    }
};

reviews_ui.goToNextCard = function() {
    //see if the session has already ended before moving on to the next card
    if (reviews_ui.sessionOverAfterCurrentCard
            || (reviews.sessionCardsReviewedCount >= reviews.sessionCardLimit && reviews.sessionCardLimit)) {
        reviews_ui.endSession();
    } else {
        //disable the review buttons until the back is shown again
        dojo.query('button', dojo.byId('reviews_gradeButtonsContainer')).forEach(function(node) {
            dijit.getEnclosingWidget(node).attr('disabled', true);
        });
        //disable the card back button until the next card is ready
        reviews_showCardBackButton.attr('disabled', true);
        
        var nextCardDef = reviews.nextCard();
        nextCardDef.addCallback(function(nextCard) {
            if (nextCard) {
                //next card is ready
                reviews_ui.displayCard(nextCard);
            } else  {
                //out of cards on the server
                reviews_ui.endSession();
            }
        });
    }
};


reviews_ui.showCardBack = function(card) {
    reviews_showCardBackButton.attr('disabled', true);
    reviews_ui.cardBackVisible = true;
    reviews_ui.unsetCardFrontKeyboardShortcuts();
    
    //enable the grade buttons
    dojo.query('button', dojo.byId('reviews_gradeButtons')).forEach(function(node) {
        dijit.getEnclosingWidget(node).attr('disabled', false);
    });

    dojo.byId('reviews_showCardBack').style.display = 'none';
    reviews_cardBack.domNode.style.display = '';
    reviews_ui.displayNextIntervals(card);
    dojo.byId('reviews_gradeButtonsContainer').style.visibility = '';
    reviews_ui.review_dialog.domNode.focus();
    reviews_ui.setCardBackKeyboardShortcuts();
};


reviews_ui.reviewCard = function(card, grade) {
    var review_def = reviews.reviewCard(card, grade);
    review_def.addCallback(function(data) {
        // Enable the Undo button (maybe should do this before the def?)
        reviews_undoReviewButton.attr('disabled', false);
        //FIXME anything go here?
    });
    reviews_ui.goToNextCard();
    if (grade == reviews.grades.GRADE_NONE) {
        //failed cards will be reshown
        reviews.failsSincePrefetchRequest += 1;
    }
};


reviews_ui.displayNextCard = function() {
};


reviews_ui._disableReviewScreenUI = function(disable) {
    if (typeof disable == 'undefined') {
        disable = true;
    }
    dojo.query('.dijitButton', dojo.byId('reviews_fullscreenContainer')).forEach(function(item) {
        dijit.getEnclosingWidget(item).attr('disabled', disable);
    });
};


reviews_ui.undo = function() {
    // disable review UI until the undo operation is finished
    reviews_ui._disableReviewScreenUI();

    var undo_def = reviews.undo();

    undo_def.addCallback(function() {
        // Show the next card, now that the cache is cleared.
        // Also show its back.
        reviews_ui.goToNextCard();
        reviews_ui.showCardBack(reviews.currentCard);

        // re-enable review UI
        reviews_ui._disableReviewScreenUI(false);

        // disable the undo button until next review submission
        reviews_undoReviewButton.attr('disabled', true);
    });
};


reviews_ui.showReviewScreen = function() {
    //show the fullscreen reviews div
    dijit.byId('reviews_fullscreenContainer').domNode.style.display = '';

    //hide the page behind this
    dojo.byId('body_contents').style.display = 'none';

    //show the review screen and hide the end of review screen
    dojo.byId('reviews_reviewScreen').style.display = '';
    dojo.byId('reviews_reviewEndScreen').style.display = 'none';

    dijit.byId('reviews_fullscreenContainer').domNode.focus();
};


reviews_ui.isCardBackDisplayed = function() {
    //Returns true if the card's back side is shown
    return reviews_cardBack.domNode.style.display === '';
};


reviews_ui.unsetKeyboardShortcuts = function() {
    //unsets the keyboard shortcuts, `
    //no matter whether the card's front or back is currently displayed
    reviews_ui.unsetCardFrontKeyboardShortcuts();
    reviews_ui.unsetCardBackKeyboardShortcuts();
};

reviews_ui.setKeyboardShortcuts = function() {
    reviews_ui.unsetKeyboardShortcuts();
    if (reviews_ui.isCardBackDisplayed()) {
        reviews_ui.setCardBackKeyboardShortcuts();
    } else {
        reviews_ui.setCardFrontKeyboardShortcuts();
    }
};

reviews_ui.suspendCurrentCard = function() {
    reviews.suspendCard(reviews.currentCard);
    reviews_ui.goToNextCard();
};

reviews_ui.cardFrontKeyboardShortcutConn = null;
reviews_ui.cardBackKeyboardShortcutConn = null;

reviews_ui.setCardBackKeyboardShortcuts = function() {
    reviews_ui.unsetCardBackKeyboardShortcuts(); //don't set twice
    //reviews_ui.cardBackKeyboardShortcutConn = dojo.connect(reviews_ui.review_dialog, 'onKeyPress', function(e) {
    reviews_ui.cardBackKeyboardShortcutConn = dojo.connect(window, 'onkeypress', function(e) {
        switch(e.charOrCode) {
            case '0':
            case '1':
                reviews_ui.reviewCard(reviews.currentCard, reviews.grades.GRADE_NONE);
                break;
            case '2':
                reviews_ui.reviewCard(reviews.currentCard, reviews.grades.GRADE_HARD);
                break;
            case '3':
                reviews_ui.reviewCard(reviews.currentCard, reviews.grades.GRADE_GOOD);
                break;
            case '4':
                reviews_ui.reviewCard(reviews.currentCard, reviews.grades.GRADE_EASY);
                break;
        }
    });
};

reviews_ui.setCardFrontKeyboardShortcuts = function() {
  reviews_ui.unsetCardFrontKeyboardShortcuts(); //don't set twice
  reviews_ui.cardFrontKeyboardShortcutConn = dojo.connect(window, 'onkeypress', function(e) {
    var k = dojo.keys;
    switch(e.charOrCode) {
        case k.ENTER:
        case ' ':
            reviews_ui.showCardBack(reviews.currentCard);
            dojo.stopEvent(e);
            break;
        //default:
    }
  });
};

reviews_ui.unsetCardFrontKeyboardShortcuts = function() {
    if (reviews_ui.cardFrontKeyboardShortcutConn) {
        dojo.disconnect(reviews_ui.cardFrontKeyboardShortcutConn);
    }
};

reviews_ui.unsetCardBackKeyboardShortcuts = function() {
    if (reviews_ui.cardBackKeyboardShortcutConn) {
        dojo.disconnect(reviews_ui.cardBackKeyboardShortcutConn);
    }
};

reviews_ui._subscribeToSessionEvents = function() {
    reviews_ui._eventSubscriptions = [];
    //session timer completion event (when the session timer has exceeded the session time limit)
    reviews_ui._eventSubscriptions.push(dojo.subscribe(reviews.subscriptionNames.sessionTimerOver, function(evt) {
        reviews_ui.sessionOverAfterCurrentCard = true;
    }));
}

reviews_ui._unsubscribeFromSessionEvents = function() {
    //dojo.unsubscribe(reviews.subscriptionNames.sessionTimerOver);
    reviews_ui._eventSubscriptions.forEach(function(handle) {
        dojo.unsubscribe(handle);
    });
};

reviews_ui.startSession = function(args) { //deckId, sessionTimeLimit, sessionCardLimit, tag_id, earlyReview, learnMore) { //, dailyNewCardLimt) {
    //args//if (.earlyReview == undefined) { var earlyReview = false; }
    //if (learnMore == undefined) { var learnMore = false; }
    //if (sessionTimeLimit == undefined) { var sessionTimeLimit = 10; }
    //if (sessionCardLimit == undefined) { var sessionCardLimit = 0; }
    //if (tag_id == undefined) { var tag_id = '-1'; }

    // raise error (FIXME we just ignore it for now) if the session is already
    // in progress
    if (reviews_ui.sessionStarted) {
        return;
    }

    reviews_ui.sessionStarted = true;

    reviews_ui.sessionOverAfterCurrentCard = false;

    reviews_undoReviewButton.attr('disabled', true);

    reviews_ui.lastSessionArgs = dojo.clone(args);

    //start a review session with the server
    var session_def = reviews.startSession(
            args.deckId||'-1', 
            20, 
            args.sessionCardLimit||0, 
            args.sessionTimeLimit||10,
            args.tag_id||'-1',
            args.earlyReview||false, 
            args.learnMore||false); //FIXME use the user-defined session limits

    reviews_ui._subscribeToSessionEvents();

    //wait for the first cards to be returned from the server
    session_def.addCallback(function(initialCardPrefetch) {
        //show the first card
        var nextCardDef = reviews.nextCard();
        nextCardDef.addCallback(dojo.hitch(null, function(initialCardPrefetch, nextCard) {

            if (nextCard) {
                //hide this dialog and show the review screen
                reviews_reviewDialog.refocus = false;
                reviews_reviewDialog.hide();
                reviews_ui.showReviewScreen();

                //show the card
                reviews_ui.displayCard(nextCard);
            } else {
                //no cards are due
                //are there new cards left to learn today? (decide whether to
                //show learn more button).
                //canLearnMore = initialCardPrefetch.new_cards_left_for_today == '0' && initialCardPrefetch.new_cards_left != '0'; //TODO better api for this
                // ! canLearnMore = initialCardPrefetch.new_cards_left > 0; //TODO better api for this
                // ! emptyQuery = initialCardPrefetch.total_card_count_for_query <= 0;
                // ! reviews_ui.showNoCardsDue(canLearnMore, emptyQuery);
                reviews_ui.showNoCardsDue(false, false); //FIXME do we need this dialog anymore, or just show some error
            }
        }, initialCardPrefetch));
    });

};

reviews_ui.submitReviewOptionsDialog = function(earlyReview, learnMore) {
    if (typeof earlyReview == 'undefined') {
        earlyReview = false;
    }
    if (typeof learnMore == 'undefined') {
        learnMore = false;
    }

    //hide this options screen
    //dojo.byId('reviews_reviewOptions').style.display = 'none';//({display: 'none'});

    //TODO add a loading screen

    //disable the submit button while it processes
    reviews_beginReviewButton.attr('disabled', true);
    reviews_learnMoreButton.attr('disabled', true);
    reviews_beginEarlyReviewButton.attr('disabled', true);

    var decksGridItem = reviews_decksGrid.selection.getSelected()[0];
    var deckId = decksGridItem.id[0]; //TODO allow multiple selections
    var timeLimit = reviews_timeLimitInput.attr('value');
    var cardLimit = reviews_cardLimitInput.attr('value');
    //var dailyNewCardLimt = reviews_newCardLimitInput.attr('value');

    //! var tag_id = reviews_filterByTagInput.attr('value');
    //! if (reviews_filterByTagInput.attr('displayedValue') == '') {
        //tag_id = '-1';
    //! }

    var args = {
        deckId: deckId,
        timeLimit: timeLimit,
        cardLimit: cardLimit,
        earlyReview: earlyReview,
        learnMore: learnMore
    };

    reviews_ui.startSession(args); //deckId, timeLimit, cardLimit, tag_id, earlyReview, learnMore); //, dailyNewCardLimt);
};


