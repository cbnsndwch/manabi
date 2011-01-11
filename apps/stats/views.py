from flashcards.views.decorators import flashcard_api as api
from flashcards.views.decorators import ApiException
from django.views.decorators.http import require_GET
from flashcards.models import CardHistory
from django.http import HttpResponse
import settings

@api
@require_GET
def repetitions(request):
    '''
    Graph data for repetitions per day.
    '''
    series = []
    user_items = CardHistory.objects.of_user(request.user)

    for maturity in ['new_cards', 'young_cards', 'mature_cards']:
        data = getattr(user_items, maturity)().repetitions()

        # Convert the values into pairs (from hashes)
        data = list((value['date'], value['repetitions'])
                      for value in data)

        series.append({
            'name': maturity.rstrip('_cards'),
            'data': data,
        })

    return {'series': series}


