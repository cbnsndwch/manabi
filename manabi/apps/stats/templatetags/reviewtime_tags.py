from django import template
from manabi.apps.flashcards.models import CardHistory

register = template.Library()

@register.simple_tag
def review_seconds_today(user):
    '''
    Returns the number of seconds spent reviewing today.
    '''
    return CardHistory.objects.daily_duration(user)


@register.inclusion_tag('stats/_review_time_report.html')
def show_review_time_report(user):
    '''
    '''
    duration = CardHistory.objects.daily_duration(user)
    return {'duration': duration}
    
