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
        if (reviews.session_deck_id != '-1') {
            url += '&deck='+reviews.session_deck_id;
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

    reviews.startSession = function(deck_id, session_new_card_limit, session_card_limit, session_time_limit) {
        //Use deck_id = -1 for all decks
        //Always call this before doing anything else.
        //Returns a deferred.
        reviews.session_deck_id = deck_id;
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

    reviews.reload_current_card = function() {
        //TODO refresh the card inside reviews.cards, instead of just setting current_cards
        var xhr_args = {
            url: 'flashcards/rest/cards/'+reviews.current_card.id,
            handleAs: 'json',
            load: function(data) {
                if (data.success) {
                    reviews.current_card = data.card;
                }
            }
        };
        return dojo.xhrGet(xhr_args);
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





// user interface

reviews_ui = {}

dojo.addOnLoad(function() {
    reviews_ui.review_options_dialog = dijit.byId('reviews_reviewDialog');
    reviews_ui.review_dialog = dijit.byId('reviews_fullscreenContainer');
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
};

reviews_ui.showNoCardsDue = function() {
    dojo.byId('reviews_noCardsDue').style.display = '';
    dojo.byId('reviews_beginReview').style.display = 'none';
    dojo.byId('reviews_reviewOptions').style.display = '';
    dojo.byId('reviews_reviewScreen').style.display = 'none';
    dojo.byId('reviews_reviewEndScreen').style.display = 'none';
};

reviews_ui.showReviewOptions = function() {
    dojo.byId('reviews_beginReview').style.display = '';
    dojo.byId('reviews_reviewOptions').style.display = '';
    dojo.byId('reviews_noCardsDue').style.display = 'none';
    dojo.byId('reviews_reviewEndScreen').style.display = 'none';

    //refresh the decks grid
//    reviews_decksStore.close();
//reviews_decksStore.fetch();

    //show the due count
    reviews.dueCardsCount().addCallback(function(count) {
        dojo.byId('reviews_cardsDueCount').innerHTML = count;
    });
    //show the new count
    reviews.newCardsCount().addCallback(function(count) {
        dojo.byId('reviews_cardsNewCount').innerHTML = count;
    });

};

reviews_ui.openDialog = function() {
    //TODO first check if there are any cards due (using default review options? or special request to server)

    reviews_ui.showReviewOptions();

    reviews_ui.review_options_dialog.tabStart = reviews_beginReviewButton;

    //show the options screen
    dojo.byId('reviews_reviewOptions').style.display = '';
    //hide the review screen
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

reviews_ui.endSession = function() {
    reviews_ui.unsetCardBackKeyboardShortcuts();
    reviews_ui.unsetCardFrontKeyboardShortcuts();

    //show the page behind this
    dojo.byId('body_contents').style.display = '';

    dojo.byId('reviews_fullscreenContainer').style.display = 'none';
    //TODO fade out, less harsh
    //TODO show review session results
    reviews.endSession();
};

reviews_ui.displayNextIntervals = function(card) {
    //dojo.byId('reviews_gradeNoneInterval').innerHTML = reviews_ui.humanizedInterval(card.next_due_at_per_grade['0']);
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
    dojo.byId('reviews_gradeButtons').style.visibility = 'hidden';
    //reviews_ui.review_dialog._position(); //recenter dialog
    //reviews_showCardBackButton.focus();
    if (show_card_back) {
        reviews_ui.showCardBack(card);
    } else {
        reviews_ui.setCardFrontKeyboardShortcuts();
        reviews_showCardBackButton.attr('disabled', false);
        reviews_showCardBackButton.focus();
    }
};

reviews_ui.goToNextCard = function() {
    //disable the review buttons until the back is shown again
    dojo.query('button', dojo.byId('reviews_gradeButtons')).forEach(function(node) {
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
    dojo.byId('reviews_gradeButtons').style.visibility = '';
    reviews_ui.review_dialog.domNode.focus();
    reviews_ui.setCardBackKeyboardShortcuts();
};

reviews_ui.reviewCard = function(card, grade) {
    var review_def = reviews.reviewCard(card, grade);
    review_def.addCallback(function(data) {
        //FIXME anything go here?
    });
    reviews_ui.goToNextCard();
};


reviews_ui.displayNextCard = function() {
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
    //unsets the keyboard shortcuts, 
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


reviews_ui.card_front_keyboard_shortcut_connection = null;
reviews_ui.card_back_keyboard_shortcut_connection = null;

reviews_ui.setCardBackKeyboardShortcuts = function() {
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
  //reviews_ui.card_front_keyboard_shortcut_connection = dojo.connect(reviews_ui.review_dialog, 'onKeyPress', function(e) {
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



reviews_ui.submitReviewOptionsDialog = function() {
    //hide this options screen
    //dojo.byId('reviews_reviewOptions').style.display = 'none';//({display: 'none'});

    //TODO add a loading screen



    var decks_grid_item = reviews_decksGrid.selection.getSelected()[0];
    var deck_id = decks_grid_item['id'][0]; //TODO allow multiple selections
    
    //start a review session with the server
    var session_def = reviews.startSession(deck_id, 20); //FIXME use the user-defined session limits

    //wait for the first cards to be returned from the server
    session_def.addCallback(function() {
        //show the first card
        var next_card_def = reviews.nextCard();
        next_card_def.addCallback(function(next_card) {

            if (next_card) {
                //hide this dialog and show the review screen
                reviews_reviewDialog.refocus = false;
                reviews_reviewDialog.hide();
                reviews_ui.showReviewScreen();

                //show the card
                reviews_ui.displayCard(next_card);
            } else {
                //no cards are due
                reviews_ui.showNoCardsDue();
            }
        });
    });
};


var reviews_decksGridLayout = [{
			type: "dojox.grid._RadioSelector"
		},{ cells: [[
			{name: 'Name', field: 'name', width: 'auto'},
			//{name: 'Cards', field: 'card_count', width: 'auto'},
			{name: 'Cards due', field: 'due_card_count', width: '58px'},
			{name: 'New cards', field: 'new_card_count', width: '60px'},
		]]}];
