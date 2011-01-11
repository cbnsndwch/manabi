from cards import * #Card, CardHistory, CardStatistics
from decks import *
from facts import * #Fact, FactType, SharedFact
from fields import *
from reviews import *
from cardtemplates import *
from undo import *
from django.contrib.auth.models import User

from django.db.models.signals import post_save  

from django.conf import settings

#preloading data
#TODO move into fixtures ?
def create_default_user_data(sender, instance, created, **kwargs):
    """
    Creates the default fact types, fields, deck and card templates.
    Meant to be used when a new user signs up.
    """
    if created:
      user = instance
#      my_deck = Deck(name='Sample Deck', owner=user, active=True)
#      my_deck.save()
#      my_deck_scheduling = SchedulingOptions(deck=my_deck)
#      my_deck_scheduling.save()
      review_stats, created = ReviewStatistics.objects.get_or_create(user=user)
      if created:
        review_stats.save()
      
post_save.connect(create_default_user_data, sender=User) 




