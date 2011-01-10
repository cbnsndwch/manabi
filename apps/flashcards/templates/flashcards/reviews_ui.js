// user interface functions for reviews
//
dojo.provide('reviews_ui');

dojo.require('reviews');



dojo.addOnLoad(function() {
    reviews_ui.reviewOptionsDialog = dijit.byId('reviews_reviewDialog');
    reviews_ui.review_dialog = dijit.byId('reviews_fullscreenContainer');
    reviews_ui.sessionStarted = false;

});

reviews_ui.humanizedInterval = function(interval) {
    // `interval` is in milliseconds, we convert it to days inside
    // the function.
    var ret = null;
    var duration = null;
    interval = parseFloat(interval) / (1000 * 60 * 60 * 24);

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
    reviews_beginReviewButton.st('disabled', true);
    if (!reviews_ui.reviewOptionsDialog.get('open')) {
        //reviews_ui.reviewOptionsDialog.show();
        reviews_ui.openDialog();
    }

    reviews_ui._showNoCardsDue();

    if (!canLearnMore && emptyQuery) {
        reviews_beginEarlyReviewButton.set('disabled', true);
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
        reviews_learnMoreButton.set('disabled', !canLearnMore);
        reviews_beginEarlyReviewButton.set('disabled', false);
    }

};

reviews_ui.showReviewOptions = function() {
    //FIXME temp fix dojo.byId('reviews_beginReview').style.display = '';
    dojo.byId('reviews_beginReview').style.display = 'none';
    dojo.byId('reviews_noCardsDue').style.display = 'none';
    dojo.byId('reviews_emptyQuery').style.display = 'none';
    dojo.byId('reviews_reviewEndScreen').style.display = 'none';
    reviews_beginReviewButton.set('disabled', false);
    reviews_beginEarlyReviewButton.set('disabled', true);
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
    dojo.byId('tabhead').style.display = '';

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
    var now = new Date();
    dojo.byId('reviews_gradeNoneInterval').innerHTML = 'Review soon';
    dojo.byId('reviews_gradeHardInterval').innerHTML = reviews_ui.humanizedInterval(card.nextDueAt(3) - now);
    dojo.byId('reviews_gradeGoodInterval').innerHTML = reviews_ui.humanizedInterval(card.nextDueAt(4) - now);
    dojo.byId('reviews_gradeEasyInterval').innerHTML = reviews_ui.humanizedInterval(card.nextDueAt(5) - now);
};


reviews_ui.displayCard = function(card, show_card_back) {
    reviews_ui.cardBackVisible = false;
    reviews_ui.unsetCardBackKeyboardShortcuts();
    reviews_cardFront.set('content', card.front);
    dojo.byId('reviews_showCardBack').style.display = '';
    reviews_cardBack.set('content', '');
    reviews_cardBack.domNode.style.display = 'none';
    reviews_subfactPane.set('content', '');
    reviews_subfactPane.domNode.style.display = 'none';
    dojo.byId('reviews_gradeButtonsContainer').style.visibility = 'hidden';
    if (show_card_back) {
        reviews_ui.showCardBack(card);
    } else {
        reviews_ui.setCardFrontKeyboardShortcuts();
        reviews_showCardBackButton.set('disabled', false);
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
        dojo.query('.dijitButton', dojo.byId('reviews_gradeButtonsContainer')).forEach(function(node) {
            dijit.getEnclosingWidget(node).set('disabled', true);
        });
        //disable the card back button until the next card is ready
        reviews_showCardBackButton.set('disabled', true);
        
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
    reviews_showCardBackButton.set('disabled', true);
    reviews_ui.cardBackVisible = true;
    reviews_ui.unsetCardFrontKeyboardShortcuts();
    
    //enable the grade buttons
    dojo.query('.dijitButton', dojo.byId('reviews_gradeButtons')).forEach(function(node) {
        dijit.getEnclosingWidget(node).set('disabled', false);
    });

    dojo.byId('reviews_showCardBack').style.display = 'none';
    reviews_cardBack.set('content', card.back);
    reviews_cardBack.domNode.style.display = '';
    reviews_ui.displayNextIntervals(card);
    dojo.byId('reviews_gradeButtonsContainer').style.visibility = '';
    reviews_ui.review_dialog.domNode.focus();
    reviews_ui.setCardBackKeyboardShortcuts();
};


reviews_ui.reviewCard = function(card, grade) {
    var review_def = card.review(grade);
    review_def.addCallback(function(data) {
        // Enable the Undo button (maybe should do this before the def?)
        reviews_undoReviewButton.set('disabled', false);
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
        dijit.getEnclosingWidget(item).set('disabled', disable);
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
        reviews_undoReviewButton.set('disabled', true);
    });
};


reviews_ui.showReviewScreen = function() {
    //show the fullscreen reviews div
    dijit.byId('reviews_fullscreenContainer').domNode.style.display = '';

    //hide the page behind this
    dojo.byId('body_contents').style.display = 'none';
    dojo.byId('tabhead').style.display = 'none';

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
    reviews.currentCard.suspend();
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

    reviews_undoReviewButton.set('disabled', true);

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
    reviews_beginReviewButton.set('disabled', true);
    reviews_learnMoreButton.set('disabled', true);
    reviews_beginEarlyReviewButton.set('disabled', true);

    var decksGridItem = reviews_decksGrid.selection.getSelected()[0];
    var deckId = decksGridItem.id[0]; //TODO allow multiple selections
    var timeLimit = reviews_timeLimitInput.set('value');
    var cardLimit = reviews_cardLimitInput.set('value');
    //var dailyNewCardLimt = reviews_newCardLimitInput.set('value');

    //! var tag_id = reviews_filterByTagInput.set('value');
    //! if (reviews_filterByTagInput.set('displayedValue') == '') {
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



