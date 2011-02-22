from django import template
from flashcards.models import Card, Deck
from django.core.urlresolvers import reverse

register = template.Library()

@register.simple_tag
def show_lazy_user_warning(user):
    '''
    Only shows the warning if the user has added some cards.
    '''
    cards_exist = Card.objects.of_user(user).exists()
    if cards_exist:
        return '''
                <div class="lazy_user_warning">
                    You have unsaved data. To save your progress,
                    please remember to <a href="{0}">sign up</a>
                    for a free account.
                </div>
               '''.format(reverse('lazysignup_convert'))
