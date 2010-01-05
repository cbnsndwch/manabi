// flashcard reviewing




var reviews = {};

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
    reviews.session_timer_subscription_name = '/manabi/reviews/session_timer_tick';

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
            }
        }

        reviews.fails_since_prefetch_request = 0;

        return dojo.xhrGet(xhr_args);
    }

    reviews._start_session_timer = function() {
        reviews.session_start_time = new Date();
        reviews.session_timer = new dojox.timing.Timer();
        reviews.session_timer.setInterval(1000); //in ms
        reviews.session_timer.onTick = function() {
            var time_now = new Date();
            var elapsed = time_now - reviews.start_time; //in ms
            var is_running = true;
            //see if we're over the session time limit
            if (reviews.session_time_limit * 60000 <= elapsed) {
                is_running = false;
                reviews.session_timer.stop();
            }
            dojo.publish(reviews.session_timer_subscription_name, [{
                is_running: is_running,
                time_elapsed: elapsed
            }]);
        };
    }

    reviews._stop_session_timer = function() {
        reviews.session_end_time = new Date();
        reviews.session_timer.stop();
        reviews.session_timer = null;
        dojo.publish(reviews.session_timer_subscription_name, [{
            is_running: false,
            time_elapsed: reviews.session_end_time - reviews.session_start_time
        }]);
    }

    reviews.startSession = function(deck_id, session_new_card_limit, session_card_limit, session_time_limit) {
        //Use deck_id = -1 for all decks
        //session_time_limit is in minutes
        //Always call this before doing anything else.
        //Returns a deferred.
        reviews.session_deck_id = deck_id;
        reviews.session_new_card_limit = session_new_card_limit;
        reviews.session_card_limit = session_card_limit;
        reviews.session_time_limit = session_time_limit;
        reviews.session_cards_reviewed_count = 0;
        reviews.session_over_def = new dojo.Deferred();

        //start session timer - a published event
        reviews._start_session_timer();
        
        reviews.empty_prefetch_producer = false;

        //TODO cleanup beforehand? precautionary..
        return reviews.prefetchCards(reviews.card_buffer_count * 2, true);
    }

    reviews.endSession = function() {
        reviews._stop_session_timer();

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

        //TODO -?-(done?)dont prefetch more cards if a prefetch is already in progress
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





