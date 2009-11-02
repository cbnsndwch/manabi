from cards import * #Card, CardHistory, CardStatistics
from facts import * #Fact, FactType
from fields import *
from decks import *
from cardtemplates import *

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
      japanese_fact_type = FactType(name='Japanese', owner=user)
      japanese_fact_type.save()
      expression_field = FieldType(name='Expression', fact_type=japanese_fact_type, unique=True, blank=False, ordinal=0)
      expression_field.save()
      meaning_field = FieldType(name='Meaning', fact_type=japanese_fact_type, unique=True, blank=False, ordinal=1)
      meaning_field.save()
      reading_field = FieldType(name='Reading', fact_type=japanese_fact_type, unique=False, blank=True, ordinal=2)
      reading_field.save()
      
      my_deck = Deck(name='My First Deck', owner=user)
      my_deck.save()

      my_deck_scheduling = SchedulingOptions(deck=my_deck)
      my_deck_scheduling.save()
      
      # templates
      # production:
      production_card_template = CardTemplate(name='Production', fact_type=japanese_fact_type, front_template_name='', back_template_name='', generate_by_default=True, ordinal=0)
      production_card_template.save()
      front_template_content = '{{{{ fields.{0} }}}}'.format(meaning_field.id)
      front_template_name = u'flashcards/users/{0}/{1}/{2}_front.html'.format(user.id, japanese_fact_type.id, production_card_template.id)
      back_template_content = '{{{{ fields.{0} }}}}<br>{{{{ fields.{1} }}}}'.format(expression_field.id, reading_field.id)
      back_template_name = u'flashcards/users/{0}/{1}/{2}_back.html'.format(user.id, japanese_fact_type.id, production_card_template.id)
      tmplt = Template(name=front_template_name, content=front_template_content) #FIXME make sure this works
      tmplt.save()
      tmplt.sites.add(settings.SITE_ID)
      tmplt.save()
      tmplt = Template(name=back_template_name, content=back_template_content)
      tmplt.save()
      tmplt.sites.add(settings.SITE_ID)
      tmplt.save()
      production_card_template.front_template_name = front_template_name
      production_card_template.back_template_name = back_template_name
      production_card_template.save()
      
      #recognition:
      recognition_card_template = CardTemplate(name='Recognition', fact_type=japanese_fact_type, front_template_name='', back_template_name='', generate_by_default=True, ordinal=1)
      recognition_card_template.save()
      front_template_content = '{{{{ fields.{0} }}}}'.format(expression_field.id)
      front_template_name = u'flashcards/users/{0}/{1}/{2}_front.html'.format(user.id, japanese_fact_type.id, recognition_card_template.id)
      back_template_content = '{{{{ fields.{0} }}}}<br>{{{{ fields.{1} }}}}'.format(reading_field.id, meaning_field.id)
      back_template_name = u'flashcards/users/{0}/{1}/{2}_back.html'.format(user.id, japanese_fact_type.id, recognition_card_template.id)
      tmplt = Template(name=front_template_name, content=front_template_content)
      tmplt.save()
      tmplt.sites.add(settings.SITE_ID)
      tmplt.save()
      tmplt = Template(name=back_template_name, content=back_template_content)
      tmplt.save()
      tmplt.sites.add(settings.SITE_ID)
      tmplt.save()
      recognition_card_template.front_template_name = front_template_name
      recognition_card_template.back_template_name = back_template_name
      recognition_card_template.save()
    
post_save.connect(create_default_user_data, sender=User) 



