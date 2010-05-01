import datetime
from flashcards.models.cards import CardHistory
from django.contrib.auth.models import User
from django.shortcuts import render_to_response
from django.template import RequestContext

from django.contrib.auth.decorators import user_passes_test
def staff_required(login_url=None):
    return user_passes_test(lambda u: u.is_staff, login_url=login_url)


@staff_required(login_url="../admin")
def spring_break_usage(request):
    context = {}

    date_range = (datetime.date(2010, 3, 12), datetime.date(2010, 3, 22),)

    all_reviews = context['user_reviews'] = {}
    users = User.objects.filter(is_active=True)
    for user in users:
        user_reviews = CardHistory.objects.of_user(user)
        user_reviews = user_reviews.filter(reviewed_at__gte=date_range[0], reviewed_at__lte=date_range[1])
        all_reviews[user] = user_reviews
    return render_to_response('reports/usage.html', context, context_instance=RequestContext(request))
