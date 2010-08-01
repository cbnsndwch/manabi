// flashcard reviewing




//dojo.declare('reviews', null, {blah:function(){console.log('f');}});//reviews = {};
/*TODO convert to dojo declare syntax
  if(!dojo._hasResource['reviews']){
dojo._hasResource['reviews'] = true;
dojo.provide('reviews');
}*/
reviews = {};

dojo.addOnLoad(function() {
    reviews.cards = new Array();
    
    //this is for cards that are reviewed, and have been submitted to the server
    //without a response yet.
    //It's a list of card IDs.
    reviews.card_buffer_count = 5;
    reviews.grades = {GRADE_NONE: 0, GRADE_HARD: 3, GRADE_GOOD: 4, GRADE_EASY: 5};
    //reviews.session_over_def = null; //subscribe to this to know when the session is over,
                                     //particularly because the time/card limit ran out
});

reviews.subscription_names = {
    session_timer_tick: '/manabi/reviews/session_timer_tick',
    session_timer_over: '/manabi/reviews/session_timer_over',
    session_card_limit_reached: '/manabi/reviews/session_card_limit_reached',
    session_over: '/manabi/reviews/session_over'
};


reviews.prefetchCards = function(count, session_start) {
    //get next cards from server, discounting those currently enqueued/pending
    //Returns a deferred.
    reviews._prefetch_in_progress = true;

    //serialize the excluded id list
    excluded_ids = new Array();
    dojo.forEach(reviews.cards,
        function(card, index) {
            if (excluded_ids.lastIndexOf(card.id) == -1) {
                excluded_ids.push(card.id);
            }
    });
    dojo.forEach(reviews.cards_reviewed_pending,
        function(card_id, index) {
            if (excluded_ids.lastIndexOf(card_id) == -1) {
                excluded_ids.push(card_id);
            }
    });

    var url = '/flashcards/rest/cards_for_review'; //TODO don't hardcode these URLs
    url += '?count='+count;
    if (session_start) {
        url += '&session_start=True';
    }
    if (excluded_ids.length > 0) {
        url += '&excluded_cards=' + excluded_ids.join('+');
    }
    if (reviews.session_deck_id != '-1') {
        url += '&deck=' + reviews.session_deck_id;
    }
    if (reviews.session_tag_id != '-1') {
        url += '&tag=' + reviews.session_tag_id;
    }
    if (reviews.session_early_review) {
        url += '&early_review=True';
    }
    if (reviews.session_learn_more) {
        url += '&learn_more=True';
    }

    xhr_args = {
        url: url,
        handleAs: 'json',
        load: function(data) {
            if (data.success) {
                //start the session timer if it hasn't already been started
                if (reviews.session_timer != null) {
                    if (!reviews.session_timer.isRunning) {
                        reviews.session_timer.start()
                    }
                }
                if (data.cards.length > 0) {
                    reviews.cards = reviews.cards.concat(data.cards);
                }
                if (data.cards.length < count) {
                    //server has run out of cards for us
                    if (reviews.fails_since_prefetch_request == 0) {
                        reviews.empty_prefetch_producer = true;
                    }
                }
            } else {
                //error //FIXME it should redo the request
            }
            reviews._prefetch_in_progress = false;
        }
    };

    reviews.fails_since_prefetch_request = 0;

    return dojo.xhrGet(xhr_args);
}

reviews._start_session_timer = function() {
    if (reviews.session_timer) {
        reviews.session_timer.stop();
        delete reviews.session_timer;
    }
    reviews.session_start_time = new Date();
    reviews.session_timer = new dojox.timing.Timer();
    reviews.session_timer.setInterval(1000); //in ms
    reviews.session_timer.onTick = function() {
        var time_now = new Date();
        var elapsed = time_now - reviews.session_start_time; //in ms
        //see if we're over the session time limit
        if (reviews.session_time_limit
                && reviews.session_time_limit * 60000 <= elapsed) {
            reviews._stop_session_timer();
        } else {
            dojo.publish(reviews.subscription_names.session_timer_tick, [{
                is_running: true,
                time_elapsed: elapsed }]);
        }
    };
};

reviews._stop_session_timer = function() {
    if (reviews.session_timer) {
        if (reviews.session_timer.isRunning) {
            reviews.session_end_time = new Date();
            reviews.session_timer.stop();
            reviews.session_timer = null;
            var event_obj = { is_running: false,
                              time_elapsed: reviews.session_end_time - reviews.session_start_time };
            dojo.publish(reviews.subscription_names.session_timer_tick, [event_obj]);
            dojo.publish(reviews.subscription_names.session_timer_over, [event_obj]);
        }
    }
};

reviews.startSession = function(deck_id, daily_new_card_limit, session_card_limit, session_time_limit, tag_id, early_review, learn_more) {
    if (typeof early_review == 'undefined') {
        var early_review = false;
    }
    if (typeof learn_more == 'undefined') {
        var learn_more = false;
    }
    //Use deck_id = -1 for all decks
    //Use tag_id = -1 for no tag filter
    //session_time_limit is in minutes
    //Always call this before doing anything else.
    //Returns a deferred.
    reviews.session_deck_id = deck_id;
    reviews.session_tag_id = tag_id;
    reviews.daily_new_card_limit = daily_new_card_limit;
    reviews.session_card_limit = session_card_limit;
    reviews.session_time_limit = session_time_limit;
    reviews.session_cards_reviewed_count = 0;
    reviews.session_early_review = early_review;
    reviews.session_learn_more = learn_more;
    reviews.empty_prefetch_producer = false;
    reviews.cards_reviewed_pending = new Array(); 
    reviews.cards_reviewed_pending_defs = new Array(); //contains the Deferred objects for each pending review
    reviews.current_card = null;
    reviews.fails_since_prefetch_request = 0;
    reviews.session_timer = null;
    reviews._prefetch_in_progress = false;
    //reviews.session_over_def = new dojo.Deferred();
    reviews.empty_prefetch_producer = false;

    // reset the review undo stack on the server
    var def = new dojo.Deferred();
    reviews._simpleXHRPost('/flashcards/rest/cards_for_review/undo/reset').addCallback(dojo.hitch(def, function(def) {
        var prefetch_def = reviews.prefetchCards(reviews.card_buffer_count * 2, true);
        prefetch_def.addCallback(dojo.hitch(def, function(def, prefetch_item) {
            //start session timer - a published event
            reviews._start_session_timer();

            def.callback(prefetch_item);
        }, def));
    }, def));

    //TODO cleanup beforehand? precautionary..
    return def;
};

reviews.endSession = function() {
    reviews._stop_session_timer();

    //session over event
    dojo.publish(reviews.subscription_names.session_over, [{
        cards_reviewed_count: reviews.session_cards_reviewed_count,
        time_elapsed: reviews.session_end_time - reviews.session_start_time}]);

    //FIXME cleanup, especially once the dialog is closed prematurely, automatically
    reviews.cards = new Array();
    reviews.cards_reviewed_pending = new Array();
    reviews.empty_prefetch_producer = false;
};

reviews.reload_current_card = function() {
    //TODO refresh the card inside reviews.cards, instead of just setting current_cards
    var xhr_args = {
        url: 'flashcards/rest/cards/' + reviews.current_card.id,
        handleAs: 'json',
        load: function(data) {
            if (data.success) {
                reviews.current_card = data.card;
            }
        }
    };
    return dojo.xhrGet(xhr_args);
};

reviews._nextCard = function() {
    //assumes we already have a non-empty card queue, and returns the next card.
    card = reviews.cards.shift();
    reviews.cards_reviewed_pending.push(card.id);
    reviews.current_card = card;
    return card;
};

reviews.nextCard = function() {
    //Returns a deferred.

    //TODO -?-(done?)dont prefetch more cards if a prefetch is already in progress
    var next_card_def = new dojo.Deferred();

    if (reviews.cards.length > 0) {
        next_card_def.callback(reviews._nextCard());

        //prefetch more cards if the buffer runs low
        if (reviews.cards.length <= reviews.card_buffer_count) {
            if (!reviews.empty_prefetch_producer && !reviews._prefetch_in_progress) {
                var prefetch_cards_def = reviews.prefetchCards(reviews.card_buffer_count, false);
                /*prefetch_cards_def.addCallback(dojo.hitch(function(next_card_def) {
                    //next_card_def.callback(reviews._nextCard());
                }, null, next_card_def));            */
            }
        }

    } else {
        if (!reviews.empty_prefetch_producer && !reviews._prefetch_in_progress) {
            //out of cards, need to fetch more
            var prefetch_def = reviews.prefetchCards(reviews.card_buffer_count * 2, false);
            prefetch_def.addCallback(dojo.hitch(null, function(next_card_def) {
                if (reviews.cards.length) {
                    next_card_def.callback(reviews._nextCard());
                } else {
                    next_card_def.callback(null);
                }
            }, next_card_def));
        } else {
            next_card_def.callback(null);
        }
    }

    return next_card_def;
};


reviews._resetCardCache = function() {
    // Resets the card cache, as well as the "current_card"

    // Clear cache
    reviews.cards_reviewed_pending.splice(reviews.cards_reviewed_pending.lastIndexOf(reviews.current_card.id), 1)
    reviews.cards = new Array();
    reviews.current_card = null;

    // Refill it
    return reviews.prefetchCards(reviews.card_buffer_count * 2, true);
}


reviews.undo = function() {
    // Note that this will nullify current_card. You'll have to call next_card
    // after this is done (after its deferred is called).

    // Wait until the card review submission queue is clear before issuing the
    // undo, so that we don't accidentally undo earlier than intended.
    var review_defs = new dojo.DeferredList(reviews.cards_reviewed_pending_defs);
    var undo_def = new dojo.Deferred();
    review_defs.addCallback(dojo.hitch(null, function(undo_def) {
        // Send undo request
        var actual_undo_def = reviews._simpleXHRPost('/flashcards/rest/cards_for_review/undo');
        
        // Clear and refill card cache
        actual_undo_def.addCallback(dojo.hitch(null, function(undo_def) {
            reviews.session_cards_reviewed_count -= 1;
            reviews._resetCardCache().addCallback(dojo.hitch(null, function(undo_def) {
                undo_def.callback();
            }, undo_def));
        }, undo_def));
    }, undo_def));
    return undo_def;
}

reviews.suspendCard = function(card) {
    // Suspends this and sibling cards.
    xhr_args = {
        url: '/flashcards/rest/facts/' + card.fact_id + '/suspend',
        handleAs: 'json',
        load: function(data) {
            if (data.success) {
            } else {
                //FIXME try again on failure, or something
            }
        }
    };
    return dojo.xhrPost(xhr_args);
};

reviews.reviewCard = function(card, grade) {
    xhr_args = {
        url: '/flashcards/rest/cards/'+card.id,
        content: { grade: grade },
        handleAs: 'json',
        load: function(data) {
            if (data.success) {
                reviews.cards_reviewed_pending.splice(reviews.cards_reviewed_pending.lastIndexOf(card.id), 1)
            } else {
                //FIXME try again on failure, or something
            }
        }
    };

    reviews.session_cards_reviewed_count++;

    //if this card failed, then the server may have more cards for us to prefetch
    //even if it was empty before
    if (grade == reviews.grades.GRADE_NONE) {
        //in case a prefetch request was made and has not been returned yet from the server
        reviews.fails_since_prefetch_request++;
        //TODO don't keep showing this card if it's failed and it's the last card for the session
        reviews.empty_prefetch_producer = false;
    }


    //check if the session should be over now (time or card limit is up)
    //now = new Date(); //FIXME consolidate with more recent timer stuff

    //start sending the review in ASAP
    var def = dojo.xhrPost(xhr_args);

    //add to review def queue
    reviews.cards_reviewed_pending_defs.push(def);
    def.addCallback(dojo.hitch(null, function(def) {
        // remove the def from the queue once it's called
        reviews.cards_reviewed_pending_defs.splice(reviews.cards_reviewed_pending_defs.lastIndexOf(def), 1);
    }, def));

    //has the user reached the card review count limit?
    if (reviews.session_cards_reviewed_count >= reviews.session_card_limit
            && reviews.session_card_limit) {
        dojo.publish(reviews.subscription_names.session_card_limit_reached, [{
            cards_reviewed_count: reviews.session_cards_reviewed_count,
            time_elapsed: reviews.session_end_time - reviews.session_start_time}]);
    }

    return def;
};

reviews._simpleXHRPost = function(url) {
    var def = new dojo.Deferred();

    var xhr_args = {
        url: url,
        handleAs: 'json',
        load: dojo.hitch(null, function(def, data) {
            if (data.success) {
                def.callback();
            } else {
                //TODO error handling (do a failure callback)
            }
        }, def),
    }
    dojo.xhrPost(xhr_args);

    return def;
};


reviews._simpleXHRValueFetch = function(url, value_name) {
    // value_name is optional
    var def = new dojo.Deferred();

    var xhr_args = {
        url: url,
        handleAs: 'json',
        load: dojo.hitch(null, function(def, data) {
            if (data.success) {
                if (typeof value_name == 'undefined') {
                    def.callback(data);
                } else {
                    def.callback(data[value_name]);
                }
            } else {
                //TODO error handling (do a failure callback)
            }
        }, def),
    }
    dojo.xhrGet(xhr_args);

    return def;
};

reviews.dueCardsCount = function() {
    return reviews._simpleXHRValueFetch('/flashcards/rest/cards_for_review/due_count', 'cards_due_count');
};

reviews.newCardsCount = function() {
    return reviews._simpleXHRValueFetch('/flashcards/rest/cards_for_review/new_count', 'cards_new_count');
};

reviews.nextCardDueAt = function() {
    return reviews._simpleXHRValueFetch('/flashcards/rest/cards_for_review/next_due_at', 'next_card_due_at');
};

reviews.timeUntilNextCardDue = function(deck, tags) {
    var args = {};
    args.deck = deck || null;
    args.tags = tags || null;
    var query = dojo.objectToQuery(args);
    var url = '/flashcards/rest/cards_for_review/hours_until_next_due';
    if (query) {
        url += '?' + query;
    }
    return reviews._simpleXHRValueFetch(url);
//    console.log(data);
//   return {hours: data['hours_until_next_card_due'], minutes: data['minutes_until_next_card_due']};
};

reviews.countOfCardsDueTomorrow = function(deck) {
    var url = '/flashcards/rest/cards_for_review/due_tomorrow_count';
    if (typeof deck != 'undefined' && deck) {
        url += '?deck='+deck;
    }
    return reviews._simpleXHRValueFetch(url, 'cards_due_tomorrow_count');
};

















// user interface functions for reviews

reviews_ui = {};


dojo.addOnLoad(function() {
    reviews_ui.review_options_dialog = dijit.byId('reviews_reviewDialog');
    reviews_ui.review_dialog = dijit.byId('reviews_fullscreenContainer');
    reviews_ui.session_started = false;

});

reviews_ui.humanizedInterval = function(interval) {
    var ret = null;
    var duration = null;
    interval = parseFloat(interval);

    if ((interval * 24 * 60) < 1) {
        //less than a minute
        ret = 'Soon'
    } else if ((interval * 24) < 1) {
        //less than an hour: show minutes
        duration = Math.round(interval * 24 * 60);
        ret = duration + ' minute'
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
    dojo.byId('reviews_reviewOptions').style.display = 'none';
    dojo.byId('reviews_reviewScreen').style.display = 'none';
    dojo.byId('reviews_reviewEndScreen').style.display = 'none';
};


reviews_ui._humanizedTimeUntil = function(time_until) {
    var minutes_until = parseInt(time_until['minutes_until_next_card_due']) || -1;
    var hours_until = parseInt(time_until['hours_until_next_card_due']) || -1;
    if (hours_until > 0) {
    //if (parseInt(time_until['hours_until_next_card_due']) > 0) {
        return hours_until + ' hours'; //time_until['hours_until_next_card_due'] + ' hours';
    } else if (minutes_until > 0) { //parseInt(time_until['minutes_until_next_card_due']) > 0) {
        return minutes_until + ' minutes'; //time_until['minutes_until_next_card_due'] + ' minutes';
    } else {
        return 'under a minute';
    }
};


reviews_ui.showNoCardsDue = function(can_learn_more, empty_query) {
    reviews_beginReviewButton.attr('disabled', true);
    if (!reviews_ui.review_options_dialog.attr('open')) {
        //reviews_ui.review_options_dialog.show();
        reviews_ui.openDialog();
    }
    if (!can_learn_more && empty_query) {
        reviews_beginEarlyReviewButton.attr('disabled', true);
        dojo.byId('reviews_emptyQuery').style.display = '';
        reviews_ui._showNoCardsDue();
    } else {
        reviews.timeUntilNextCardDue(reviews_ui.last_session_args.deck_id, reviews_ui.last_session_args.tag_id).addCallback(function(time_until) {
            if (parseInt(time_until['hours_until_next_card_due']) > 24) {
                reviews.nextCardDueAt().addCallback(function(next_due_at) {
                    dojo.byId('reviews_noCardsDueNextDueAt').innerHTML = 'The next card is due at: ' + next_due_at;
                    dojo.byId('reviews_noCardsDue').style.display = '';
                    reviews_ui._showNoCardsDue();
                });
            } else {
                dojo.byId('reviews_noCardsDueNextDueAt').innerHTML = 'The next card is due in ' + reviews_ui._humanizedTimeUntil(time_until);
                dojo.byId('reviews_noCardsDue').style.display = '';
                reviews_ui._showNoCardsDue();
            }
        });
        dojo.byId('reviews_learnMoreContainer').style.display = can_learn_more ? '' : 'none';
        reviews_learnMoreButton.attr('disabled', !can_learn_more);
        reviews_beginEarlyReviewButton.attr('disabled', false);
        reviews_ui._showNoCardsDue();
    }

};

reviews_ui.showReviewOptions = function() {
    //FIXME temp fix dojo.byId('reviews_beginReview').style.display = '';
    dojo.byId('reviews_beginReview').style.display = 'none';
    dojo.byId('reviews_reviewOptions').style.display = '';
    dojo.byId('reviews_noCardsDue').style.display = 'none';
    dojo.byId('reviews_emptyQuery').style.display = 'none';
    dojo.byId('reviews_reviewEndScreen').style.display = 'none';

    //show the due count
    /*reviews.dueCardsCount().addCallback(function(count) {
        dojo.byId('reviews_cardsDueCount').innerHTML = count;
    });
    //show the new count
    reviews.newCardsCount().addCallback(function(count) {
        dojo.byId('reviews_cardsNewCount').innerHTML = count;
    });*/

    reviews_beginReviewButton.attr('disabled', false);
    reviews_beginEarlyReviewButton.attr('disabled', true);
};


reviews_ui.openDialog = function() {
    //TODO first check if there are any cards due (using default review options? or special request to server)

    //show the options screen
    reviews_ui.showReviewOptions();
    reviews_ui.review_options_dialog.tabStart = reviews_beginReviewButton;

    reviews_ui.review_options_dialog.show();

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


reviews_ui.openSessionOverDialog = function(review_count) {
    // get the # due tomorrow to display
    reviews.countOfCardsDueTomorrow(reviews_ui.last_session_args.deck_id).addCallback(function(count) {
        if (count == 0) {
            // None due by this time tomorrow, so we'll get the time when one
            // is next due.
            reviews.timeUntilNextCardDue(reviews_ui.last_session_args.deck_id, reviews_ui.last_session_args.tag_id).addCallback(function(time_until) {
                dojo.byId('reviews_sessionOverDialogNextDue').innerHTML = 'The next card is due in ' + reviews_ui._humanizedTimeUntil(time_until);
                dojo.byId('reviews_sessionOverDialogReviewCount').innerHTML = review_count;
                reviews_sessionOverDialog.show();
            });
        } else {
            dojo.byId('reviews_sessionOverDialogNextDue').innerHTML = 'At this time tomorrow, there will be ' + count + ' cards due for review.';
            dojo.byId('reviews_sessionOverDialogReviewCount').innerHTML = review_count;
            reviews_sessionOverDialog.show();
        }
    });

}


reviews_ui.endSession = function() {
    reviews_ui.unsetKeyboardShortcuts();

    reviews_ui._unsubscribe_from_session_events();

    //show the page behind this
    dojo.byId('body_contents').style.display = '';

    dojo.byId('reviews_fullscreenContainer').style.display = 'none';
    //TODO fade out, less harsh
    //TODO show review session results
    var review_count = reviews.session_cards_reviewed_count;
    reviews.endSession();

    if (review_count) {
        reviews_ui.openSessionOverDialog(review_count);

        // refresh the active page, in case it has due card counts etc
        manabi_ui.xhrReload();
    }

    reviews_ui.session_started = false;
};


reviews_ui.displayNextIntervals = function(card) {
    //show a special message for card failures
    //FIXME but only for young card failures - mature cards should have an interval shown
    dojo.byId('reviews_gradeNoneInterval').innerHTML = 'Review soon';
    dojo.byId('reviews_gradeHardInterval').innerHTML = reviews_ui.humanizedInterval(card.next_due_at_per_grade['3']);
    dojo.byId('reviews_gradeGoodInterval').innerHTML = reviews_ui.humanizedInterval(card.next_due_at_per_grade['4']);
    dojo.byId('reviews_gradeEasyInterval').innerHTML = reviews_ui.humanizedInterval(card.next_due_at_per_grade['5']);
};


reviews_ui.displayCard = function(card, show_card_back) {
    reviews_ui.card_back_visible = false;
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
    if (reviews_ui.session_over_after_current_card
            || (reviews.session_cards_reviewed_count >= reviews.session_card_limit && reviews.session_card_limit)) {
        reviews_ui.endSession();
    } else {
        //disable the review buttons until the back is shown again
        dojo.query('button', dojo.byId('reviews_gradeButtonsContainer')).forEach(function(node) {
            dijit.getEnclosingWidget(node).attr('disabled', true);
        });
        //disable the card back button until the next card is ready
        reviews_showCardBackButton.attr('disabled', true);
        
        var next_card_def = reviews.nextCard();
        next_card_def.addCallback(function(next_card) {
            if (next_card) {
                //next card is ready
                reviews_ui.displayCard(next_card);
            } else  {
                //out of cards on the server
                reviews_ui.endSession();
            }
        });
    }
};


reviews_ui.showCardBack = function(card) {
    reviews_showCardBackButton.attr('disabled', true);
    reviews_ui.card_back_visible = true;
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
        reviews.fails_since_prefetch_request += 1;
    }
};


reviews_ui.displayNextCard = function() {
};


reviews_ui._disableReviewScreenUI = function(disable) {
    if (typeof disable == 'undefined') {
        var disable = true;
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
        reviews_ui.showCardBack(reviews.current_card);

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
    return reviews_cardBack.domNode.style.display == '';
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
    reviews.suspendCard(reviews.current_card);
    reviews_ui.goToNextCard();
}

reviews_ui.card_front_keyboard_shortcut_connection = null;
reviews_ui.card_back_keyboard_shortcut_connection = null;

reviews_ui.setCardBackKeyboardShortcuts = function() {
  reviews_ui.unsetCardBackKeyboardShortcuts(); //don't set twice
  //reviews_ui.card_back_keyboard_shortcut_connection = dojo.connect(reviews_ui.review_dialog, 'onKeyPress', function(e) {
  reviews_ui.card_back_keyboard_shortcut_connection = dojo.connect(window, 'onkeypress', function(e) {
    switch(e.charOrCode) {
        case '0':
        case '1':
            reviews_ui.reviewCard(reviews.current_card, reviews.grades.GRADE_NONE);
            break;
        case '2':
            reviews_ui.reviewCard(reviews.current_card, reviews.grades.GRADE_HARD);
            break;
        case '3':
            reviews_ui.reviewCard(reviews.current_card, reviews.grades.GRADE_GOOD);
            break;
        case '4':
            reviews_ui.reviewCard(reviews.current_card, reviews.grades.GRADE_EASY);
            break;
    }
  });
};

reviews_ui.setCardFrontKeyboardShortcuts = function() {
  reviews_ui.unsetCardFrontKeyboardShortcuts(); //don't set twice
  reviews_ui.card_front_keyboard_shortcut_connection = dojo.connect(window, 'onkeypress', function(e) {
    var k = dojo.keys;
    switch(e.charOrCode) {
        case k.ENTER:
        case ' ':
            reviews_ui.showCardBack(reviews.current_card);
            dojo.stopEvent(e);
            break;
        //default:
    }
  });
};

reviews_ui.unsetCardFrontKeyboardShortcuts = function() {
    if (reviews_ui.card_front_keyboard_shortcut_connection) {
        dojo.disconnect(reviews_ui.card_front_keyboard_shortcut_connection);
    }
};

reviews_ui.unsetCardBackKeyboardShortcuts = function() {
    if (reviews_ui.card_back_keyboard_shortcut_connection) {
        dojo.disconnect(reviews_ui.card_back_keyboard_shortcut_connection);
    }
};

reviews_ui._subscribe_to_session_events = function() {
    reviews_ui._event_subscriptions = new Array();
    //session timer completion event (when the session timer has exceeded the session time limit)
    reviews_ui._event_subscriptions.push(dojo.subscribe(reviews.subscription_names.session_timer_over, function(evt) {
        reviews_ui.session_over_after_current_card = true;
    }));
}

reviews_ui._unsubscribe_from_session_events = function() {
    //dojo.unsubscribe(reviews.subscription_names.session_timer_over);
    reviews_ui._event_subscriptions.forEach(function(handle) {
        dojo.unsubscribe(handle);
    });
}

reviews_ui.startSession = function(args) { //deck_id, session_time_limit, session_card_limit, tag_id, early_review, learn_more) { //, daily_new_card_limit) {
    //args//if (.early_review == undefined) { var early_review = false; }
    //if (learn_more == undefined) { var learn_more = false; }
    //if (session_time_limit == undefined) { var session_time_limit = 10; }
    //if (session_card_limit == undefined) { var session_card_limit = 0; }
    //if (tag_id == undefined) { var tag_id = '-1'; }

    // raise error (FIXME we just ignore it for now) if the session is already
    // in progress
    if (reviews_ui.session_started) {
        return;
    }

    reviews_ui.session_started = true;

    reviews_ui.session_over_after_current_card = false;

    reviews_undoReviewButton.attr('disabled', true);

    reviews_ui.last_session_args = dojo.clone(args);

    //start a review session with the server
    var session_def = reviews.startSession(
            args.deck_id||'-1', 
            20, 
            args.session_card_limit||0, 
            args.session_time_limit||10,
            args.tag_id||'-1',
            args.early_review||false, 
            args.learn_more||false); //FIXME use the user-defined session limits

    reviews_ui._subscribe_to_session_events();

    //wait for the first cards to be returned from the server
    session_def.addCallback(function(initial_card_prefetch) {
        //show the first card
        var next_card_def = reviews.nextCard();
        next_card_def.addCallback(dojo.hitch(null, function(initial_card_prefetch, next_card) {

            if (next_card) {
                //hide this dialog and show the review screen
                reviews_reviewDialog.refocus = false;
                reviews_reviewDialog.hide();
                reviews_ui.showReviewScreen();

                //show the card
                reviews_ui.displayCard(next_card);
            } else {
                //no cards are due
                //are there new cards left to learn today? (decide whether to
                //show learn more button).
                //can_learn_more = initial_card_prefetch.new_cards_left_for_today == '0' && initial_card_prefetch.new_cards_left != '0'; //TODO better api for this
                // ! can_learn_more = initial_card_prefetch.new_cards_left > 0; //TODO better api for this
                // ! empty_query = initial_card_prefetch.total_card_count_for_query <= 0;
                // ! reviews_ui.showNoCardsDue(can_learn_more, empty_query);
                reviews_ui.showNoCardsDue(false, false); //FIXME do we need this dialog anymore, or just show some error
            }
        }, initial_card_prefetch));
    });

}

reviews_ui.submitReviewOptionsDialog = function(early_review, learn_more) {
    if (typeof early_review == 'undefined') {
        var early_review = false;
    }
    if (typeof learn_more == 'undefined') {
        var learn_more = false;
    }

    //hide this options screen
    //dojo.byId('reviews_reviewOptions').style.display = 'none';//({display: 'none'});

    //TODO add a loading screen

    //disable the submit button while it processes
    reviews_beginReviewButton.attr('disabled', true);
    reviews_learnMoreButton.attr('disabled', true);
    reviews_beginEarlyReviewButton.attr('disabled', true);

    var decks_grid_item = reviews_decksGrid.selection.getSelected()[0];
    var deck_id = decks_grid_item['id'][0]; //TODO allow multiple selections
    var time_limit = reviews_timeLimitInput.attr('value');
    var card_limit = reviews_cardLimitInput.attr('value');
    //var daily_new_card_limit = reviews_newCardLimitInput.attr('value');

    //! var tag_id = reviews_filterByTagInput.attr('value');
    //! if (reviews_filterByTagInput.attr('displayedValue') == '') {
        //tag_id = '-1';
    //! }

    var args = {
        deck_id: deck_id,
        time_limit: time_limit,
        card_limit: card_limit,
        early_review: early_review,
        learn_more: learn_more};

    reviews_ui.startSession(args); //deck_id, time_limit, card_limit, tag_id, early_review, learn_more); //, daily_new_card_limit);
};


//dojo.declare('reviews_decksGridLayout', null, [{
reviews_decksGridLayout = [{
			type: "dojox.grid._RadioSelector"
		},{ cells: [[
			{name: 'Name', field: 'name', width: 'auto'},
			//{name: 'Cards', field: 'card_count', width: 'auto'},
			{name: 'Cards due', field: 'due_card_count', width: '70px'},
			{name: 'New cards', field: 'new_card_count', width: '70px'},
		]]}];//);

