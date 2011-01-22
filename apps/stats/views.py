from flashcards.views.decorators import flashcard_api as api
from flashcards.views.decorators import ApiException
from datetime import datetime
from flashcards.views.decorators import has_card_query_filters
from django.views.decorators.http import require_GET
from flashcards.models import CardHistory, Card
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext, loader
import settings


# Views for graphs


MATURITY_COLORS = {
    'new':      '#62C691',
    'young':    '#7074C5',#'#49388a',
    'mature':   '#E4C670',
}
    


@api
@require_GET
def repetitions(request):
    '''
    Graph data for repetitions per day.
    '''
    series = []
    user_items = CardHistory.objects.of_user(request.user)

    for maturity in ['new', 'young', 'mature']:
        data = getattr(user_items, maturity)().repetitions()

        # Convert the values into pairs (from hashes)
        data = list((value['reviewed_on'], value['repetitions'])
                      for value in data)

        series.append({
            'name': maturity,
            'data': data,
            'color': MATURITY_COLORS[maturity],
        })

    return {'series': series}

@api
@require_GET
def due_counts(request):
    '''Due per day in future.'''
    series = []
    user_items = Card.objects.of_user(request.user)

    for maturity in ['young', 'mature']:
        items = getattr(user_items, maturity)()

        today_count = items.due_today_count()

        data = [(datetime.today(), today_count,)]

        future_counts = getattr(user_items, maturity)().future_due_counts()

        # Convert the values into pairs (from hashes)
        data.extend(list((value['due_on'], value['due_count'])
                      for value in future_counts))

        series.append({
            'name': maturity,
            'data': data,
            'color': MATURITY_COLORS[maturity],
        })

    return {'series': series}



@login_required
def index(request):
    context = {
    }
    return render_to_response('stats/index.html', context,
        context_instance=RequestContext(request))




########################################
#
# Used for end of review session stats
#
########################################

@api
@require_GET
@has_card_query_filters
def scheduling_summary(request, deck=None, tags=None):
    '''
    Provides the following data:
        # due now
        # due tomorrow
        # new cards
        next card's due date (datetime)
    '''
    user = request.user
    data = {
        'due_now': Card.objects.due_cards(
                user, deck=deck).count(),
        'due_tomorrow': Card.objects.count_of_cards_due_tomorrow(
                user, deck=deck, tags=tags),
        'new': Card.objects.new_cards_count(
                user, [], deck=deck, tags=tags),
        'next_card_due_at': Card.objects.next_card_due_at(
                user, deck=deck, tags=tags),
    }
    return data
