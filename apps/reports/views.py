import datetime
from flashcards.models import CardHistory, Card
from django.contrib.auth.models import User
from django.shortcuts import render_to_response
from django.template import RequestContext

from django.contrib.auth.decorators import user_passes_test
def staff_required(login_url=None):
    return user_passes_test(lambda u: u.is_staff, login_url=login_url)


@staff_required(login_url="../admin")
def spring_break_usage(request):
    context = {}

    date_range = (datetime.datetime(2010, 3, 12), datetime.datetime(2010, 3, 23, 5),)
    context['date_range'] = date_range

    users = context['users'] = {}

    for user in User.objects.filter(is_active=True).order_by('username').iterator():
        users[user] = {}
        user_reviews = CardHistory.objects.of_user(user)
        user_reviews_in_range = user_reviews.filter(reviewed_at__gte=date_range[0], reviewed_at__lte=date_range[1])
        users[user]['reviews'] = user_reviews_in_range
        users[user]['reviews_before'] = user_reviews.filter(reviewed_at__lt=date_range[0])
        users[user]['reviews_since'] = user_reviews.filter(reviewed_at__gt=date_range[1])
        
        users[user]['unique_cards'] = Card.objects.filter(id__in=user_reviews_in_range.values_list('card_id', flat=True)).distinct()

    return render_to_response('reports/usage.html', context, context_instance=RequestContext(request))
