// flashcard reviewing

reviews = {};

dojo.addOnLoad(function() {

    reviews.cards = new Array();
    
    //this is for cards that are reviewed, and have been submitted to the server
    //without a response yet.
    //It's a list of card IDs.
    reviews.cards_reviewed_pending = new Array(); 

    reviews.current_card = null;

    reviews.card_buffer_count = 5;

    reviews.grades = {GRADE_NONE: 0, GRADE_HARD: 3, GRADE_GOOD: 4, GRADE_EASY: 5}
    
    reviews.empty_prefetch_producer = false;
    reviews.fails_since_prefetch_request = 0;

    reviews.session_over_def = null; //subscribe to this to know when the session is over,
                                     //particularly because the time/card limit ran out

    reviews.prefetchCards = function(count, session_start) {
        //get next cards from server, discounting those currently enqueued/pending
        //Returns a deferred.

        //serialize the excluded id list
        excluded_ids = new Array();
        dojo.forEach(reviews.cards, //.concat(reviews.cards_reviewed_pending),
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

        var url = '/flashcards/rest/cards_for_review';
        url += '?count='+count;
        if (session_start) {
            url += '&session_start=True';
        }
        if (excluded_ids.length > 0) {
            url += '&excluded_cards='+excluded_ids.join('+');
        }

        xhr_args = {
            url: url,//'/flashcards/rest/cards_for_review', //TODO don't hardcode these URLs
            handleAs: 'json',
            load: function(data) {
                if (data.success) {
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
            }
        }

        reviews.fails_since_prefetch_request = 0;

        return dojo.xhrGet(xhr_args);
    }

    reviews.startSession = function(session_new_card_limit, session_card_limit, session_time_limit) {
        //Always call this before doing anything else.
        //Returns a deferred.
        reviews.session_new_card_limit = session_new_card_limit;
        reviews.session_card_limit = session_card_limit;
        reviews.session_time_limit = session_time_limit;
        reviews.session_cards_reviewed_count = 0;
        reviews.session_over_def = new dojo.Deferred();
        reviews.session_start_time = new Date();
        reviews.empty_prefetch_producer = false;

        //TODO cleanup beforehand? precautionary..
        return reviews.prefetchCards(reviews.card_buffer_count * 2, true);
    }

    reviews.endSession = function() {
        reviews.session_end_time = new Date();
        //FIXME cleanup, especially once the dialog is closed prematurely, automatically
        reviews.cards = new Array();
        reviews.cards_reviewed_pending = new Array();
        reviews.empty_prefetch_producer = false;
    }

    reviews._nextCard = function() {
        //assumes we already have a non-empty card queue, and returns the next card.
        card = reviews.cards.shift();
        reviews.cards_reviewed_pending.push(card.id);
        reviews.current_card = card;
        return card;
    }

    reviews.nextCard = function() {
        //Returns a deferred.

        //TODO dont prefetch more cards if a prefetch is already in progress
        var next_card_def = new dojo.Deferred();

        if (reviews.cards.length > 0) {
            next_card_def.callback(reviews._nextCard());

            //prefetch more cards if the buffer runs low
            if (reviews.cards.length <= reviews.card_buffer_count) {
                if (!reviews.empty_prefetch_producer) {
                    var prefetch_cards_def = reviews.prefetchCards(reviews.card_buffer_count, false);
                    prefetch_cards_def.addCallback(dojo.hitch(function(next_card_def) {
                        next_card_def.callback(reviews._nextCard());
                    }, null, next_card_def));            
                }
            }

        } else {
            if (!reviews.empty_prefetch_producer) {
                //out of cards, need to fetch more
                var prefetch_def = reviews.prefetchCards(reviews.card_buffer_count * 2, false);
                prefetch_def.addCallback(dojo.hitch(null, function(next_card_def) {
                if (!reviews.empty_prefetch_producer) {
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
    }


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
        }

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
        now = new Date();
        if ((reviews.session_start_time.getMinutes() +
            reviews.session_time_limit) < now ||
            reviews.session_card_limit <= reviews.session_cards_reviewed_count) {
            reviews.session_over_def.callback();
        }

        return dojo.xhrPost(xhr_args);
    }

    reviews.dueCardsCount = function() {
        var due_count_def = new dojo.Deferred();

        xhr_args = {
            url: '/flashcards/rest/cards_for_review/due_count',
            handleAs: 'json',
            load: dojo.hitch(null, function(due_count_def, data) {
                if (data.success) {
                    due_count_def.callback(data.cards_due_count);
                } else {
                    //TODO error handling (do a failure callback)
                }
            }, due_count_def),

        }

        dojo.xhrGet(xhr_args);

        return due_count_def;
    }

    reviews.newCardsCount = function() {
        var new_count_def = new dojo.Deferred();

        xhr_args = {
            url: '/flashcards/rest/cards_for_review/new_count',
            handleAs: 'json',
            load: dojo.hitch(null, function(new_count_def, data) {
                if (data.success) {
                    new_count_def.callback(data.cards_new_count);
                } else {
                    //TODO error handling (do a failure callback)
                }
            }, new_count_def),

        }

        dojo.xhrGet(xhr_args);

        return new_count_def;
    }
});



reviews_ui = {}

dojo.addOnLoad(function() {
    reviews_ui.review_dialog = dijit.byId('reviews_reviewDialog');
});

reviews_ui.humanizedInterval = function(interval) {
    var ret = null;
    var duration = null;

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
}

reviews_ui.showNoCardsDue = function() {
    dojo.byId('reviews_noCardsDue').style.display = '';
    dojo.byId('reviews_beginReview').style.display = 'none';
    dojo.byId('reviews_reviewOptions').style.display = '';
    dojo.byId('reviews_reviewScreen').style.display = 'none';
    dojo.byId('reviews_reviewEndScreen').style.display = 'none';
}

reviews_ui.showReviewOptions = function() {
    /*dojo.byId('reviews_beginReview').style.display = '';
    dojo.byId('reviews_reviewOptions').style.display = '';
    dojo.byId('reviews_noCardsDue').style.display = 'none';
    dojo.byId('reviews_reviewEndScreen').style.display = 'none';*/

    //show the due count
    reviews.dueCardsCount().addCallback(function(count) {
        dojo.byId('reviews_cardsDueCount').innerHTML = count;
    });
    //show the new count
    reviews.newCardsCount().addCallback(function(count) {
        dojo.byId('reviews_cardsNewCount').innerHTML = count;
    });

}

reviews_ui.openDialog = function() {
    //TODO first check if there are any cards due (using default review options? or special request to server)

    
    reviews_ui.showReviewOptions();

    //show the options screen
    dojo.byId('reviews_reviewOptions').style.display = '';
    //hide the review screen
    /*dojo.byId('reviews_reviewScreen').style.display = 'none';
    dojo.byId('reviews_reviewEndScreen').style.display = 'none';*/
    reviews_ui.review_dialog.show();
}

reviews_ui.endSession = function() {
    reviews_ui.unsetCardBackKeyboardShortcuts();
    reviews_ui.unsetCardFrontKeyboardShortcuts();
    /*dojo.byId('reviews_reviewScreen').style.display = 'none';
    dojo.byId('reviews_reviewEndScreen').style.display = '';*/
    dojo.byId('reviews_fullscreenContainer').style.display = 'none';
    //TODO fade out, less harsh
    //TODO show review session results
    reviews.endSession();
}

reviews_ui.displayNextIntervals = function(card) {
    dojo.byId('reviews_gradeNoneInterval').innerHTML = reviews_ui.humanizedInterval(card.next_due_at_per_grade['0']);
    dojo.byId('reviews_gradeHardInterval').innerHTML = reviews_ui.humanizedInterval(card.next_due_at_per_grade['3']);
    dojo.byId('reviews_gradeGoodInterval').innerHTML = reviews_ui.humanizedInterval(card.next_due_at_per_grade['4']);
    dojo.byId('reviews_gradeEasyInterval').innerHTML = reviews_ui.humanizedInterval(card.next_due_at_per_grade['5']);
}

reviews_ui.displayCard = function(card) {
    reviews_ui.unsetCardBackKeyboardShortcuts();
    reviews_cardFront.attr('content', card.front);
    dojo.byId('reviews_showCardBack').style.display = '';
    reviews_cardBack.attr('content', card.back);
    reviews_cardBack.domNode.style.display = 'none';
    dojo.byId('reviews_gradeButtons').style.visibility = 'hidden';
    reviews_ui.review_dialog._position(); //recenter dialog
    reviews_showCardBackButton.focus();
    reviews_ui.setCardFrontKeyboardShortcuts();
}

reviews_ui.goToNextCard = function() {
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

reviews_ui.showCardBack = function(card) {
    reviews_ui.unsetCardFrontKeyboardShortcuts();
    dojo.byId('reviews_showCardBack').style.display = 'none';
    reviews_cardBack.domNode.style.display = '';
    reviews_ui.displayNextIntervals(card);
    dojo.byId('reviews_gradeButtons').style.visibility = '';
    reviews_ui.review_dialog.domNode.focus();
    reviews_ui.setCardBackKeyboardShortcuts();
}

reviews_ui.reviewCard = function(card, grade) {
    var review_def = reviews.reviewCard(card, grade);
    review_def.addCallback(function(data) {
        //FIXME anything go here?
    });
    reviews_ui.goToNextCard();
}


reviews_ui.displayNextCard = function() {
}


reviews_ui.showReviewScreen = function() {
    //show the fullscreen reviews div
    dojo.byId('reviews_fullscreenContainer').style.display = '';

    //show the review screen and hide the end of review screen
    dojo.byId('reviews_reviewScreen').style.display = '';
    dojo.byId('reviews_reviewEndScreen').style.display = 'none';


}


reviews_ui.card_front_keyboard_shortcut_connection = null;
reviews_ui.card_back_keyboard_shortcut_connection = null;

reviews_ui.setCardBackKeyboardShortcuts = function() {
  reviews_ui.card_back_keyboard_shortcut_connection = dojo.connect(reviews_ui.review_dialog, 'onKeyPress', function(e) {
    switch(e.charOrCode) {
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
  reviews_ui.card_front_keyboard_shortcut_connection = dojo.connect(reviews_ui.review_dialog, 'onKeyPress', function(e) {
    var k = dojo.keys;
    switch(e.charOrCode) {
        case k.ENTER:
        case ' ':
            reviews_ui.showCardBack(reviews.current_card);
            dojo.stopEvent(e);
            break;
        default:
    }
  });
};

reviews_ui.unsetCardFrontKeyboardShortcuts = function() {
    dojo.disconnect(reviews_ui.card_front_keyboard_shortcut_connection);
};

reviews_ui.unsetCardBackKeyboardShortcuts = function() {
    dojo.disconnect(reviews_ui.card_back_keyboard_shortcut_connection);
};
