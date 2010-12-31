from django.core.management.base import BaseCommand



class Command(BaseCommand):
    #help = ""
    #args = '[various KEY=val options, use `runfcgi help` for help]'
    
    def _wrap_furiganaize_template_tag(self, template_content):
        return u''.join([u'{% load japanese %}{% furiganaize  %}', template_content, u'{% endfuriganaize %}'])

    def _add_front_prompt(self, template_content, card_template):
        template_content += u'<p class="reviews_front_prompt"><em>'+card_template.front_prompt+'</em></p>'
        return template_content

    def handle(self, *args, **options):
        from django.conf import settings
        from flashcards.models.facts import FactType
        from flashcards.models.fields import FieldType
        #from flashcards.models.fields import FieldType
        from flashcards.models.cardtemplates import CardTemplate
        from dbtemplates.models import Template
        
        #Japanese model
        japanese_fact_type = FactType(name='Japanese')
        japanese_fact_type.save()
        meaning_field = FieldType(name='Meaning', fact_type=japanese_fact_type, unique=True, blank=False, ordinal=1)
        meaning_field.save()
        reading_field = FieldType(name='Reading', fact_type=japanese_fact_type, unique=False, blank=True, ordinal=2)
        reading_field.save()
        expression_field = FieldType(name='Expression', fact_type=japanese_fact_type, transliteration_field_type=reading_field, unique=True, blank=False, ordinal=0)
        expression_field.save()
        import flashcards.partsofspeech as partsofspeech
        import pickle
        part_of_speech_choices = pickle.dumps(partsofspeech.ALL_PART_OF_SPEECH_CHOICES)
        pos_field = FieldType(name='Part of Speech', hidden_in_grid=True, disabled_in_form=True, hidden_in_form=True, fact_type=japanese_fact_type, unique=False, blank=True, choices=part_of_speech_choices, grid_column_width='7.4em', ordinal=4)
        pos_field.save()
        notes_field = FieldType(name='Notes', fact_type=japanese_fact_type, unique=False, blank=True, hidden_in_form=True, hidden_in_grid=True, ordinal=5)
        notes_field.save()

        #sub-model for example sentences inside a fact
        sub_japanese_fact_type = FactType(name='Example Sentence', parent_fact_type=japanese_fact_type, many_children_per_fact=True)
        sub_japanese_fact_type.save()
        sub_meaning_field = FieldType(name='Meaning', fact_type=sub_japanese_fact_type, unique=True, blank=False, ordinal=1)
        sub_meaning_field.save()
        sub_reading_field = FieldType(name='Reading', fact_type=sub_japanese_fact_type, unique=False, blank=True, ordinal=2)
        sub_reading_field.save()
        sub_expression_field = FieldType(name='Expression', fact_type=sub_japanese_fact_type, transliteration_field_type=sub_reading_field, unique=True, blank=False, ordinal=0)
        sub_expression_field.save()
        #sub_reading_field = FieldType(name='Source', fact_type=sub_japanese_fact_type, unique=False, blank=True, ordinal=2)
        #sub_reading_field.save()
        


        # templates
        # production:
        production_card_template = CardTemplate(name='Production', fact_type=japanese_fact_type, front_template_name='', back_template_name='', generate_by_default=True, ordinal=0)
        production_card_template.front_prompt = u'What is this in Japanese?'
        production_card_template.save()
        front_template_content = '{{{{ fields.{0}.content|linebreaksbr }}}}'.format(meaning_field.id)
        front_template_name = u'flashcards/shared/{0}/{1}_front.html'.format(japanese_fact_type.id, production_card_template.id)
        back_template_content = '{{% if not fields.{0}.has_identical_transliteration_field %}}{{{{ fields.{0}.content|linebreaksbr }}}}<br>{{% endif %}}{{{{ fields.{1}.content|linebreaksbr }}}}'.format(expression_field.id, reading_field.id)
        back_template_name = u'flashcards/shared/{0}/{1}_back.html'.format(japanese_fact_type.id, production_card_template.id)
        tmplt = Template(name=front_template_name, content=self._add_front_prompt(self._wrap_furiganaize_template_tag(front_template_content), production_card_template))
        tmplt.save()
        tmplt.sites.add(settings.SITE_ID)
        tmplt.save()
        tmplt = Template(name=back_template_name, content=self._wrap_furiganaize_template_tag(back_template_content))
        tmplt.save()
        tmplt.sites.add(settings.SITE_ID)
        tmplt.save()
        production_card_template.front_template_name = front_template_name
        production_card_template.back_template_name = back_template_name
        production_card_template.requisite_field_types.add(meaning_field, reading_field, expression_field)
        production_card_template.save()

        #recognition:
        recognition_card_template = CardTemplate(name='Recognition', fact_type=japanese_fact_type, front_template_name='', back_template_name='', generate_by_default=True, ordinal=1)
        recognition_card_template.front_prompt = u'What does this expression mean?'
        recognition_card_template.save()
        #front_template_content = '{{{{ fields.{0}.content|linebreaksbr }}}}'.format(expression_field.id)
        front_template_content = '{{% if not fields.{0}.has_identical_transliteration_field %}}{{{{ fields.{0}.content|linebreaksbr }}}}<br>{{% endif %}}{{{{ fields.{1}.content|linebreaksbr }}}}'.format(expression_field.id, reading_field.id)
        front_template_name = u'flashcards/shared/{0}/{1}_front.html'.format(japanese_fact_type.id, recognition_card_template.id)
        back_template_content = '{{{{ fields.{0}.content|linebreaksbr }}}}'.format(meaning_field.id)
        back_template_name = u'flashcards/shared/{0}/{1}_back.html'.format(japanese_fact_type.id, recognition_card_template.id)
        tmplt = Template(name=front_template_name, content=self._add_front_prompt(self._wrap_furiganaize_template_tag(front_template_content), recognition_card_template))
        tmplt.save()
        tmplt.sites.add(settings.SITE_ID)
        tmplt.save()
        tmplt = Template(name=back_template_name, content=self._wrap_furiganaize_template_tag(back_template_content))
        tmplt.save()
        tmplt.sites.add(settings.SITE_ID)
        tmplt.save()
        recognition_card_template.front_template_name = front_template_name
        recognition_card_template.back_template_name = back_template_name
        recognition_card_template.requisite_field_types.add(meaning_field, reading_field, expression_field)
        recognition_card_template.save()

        ################################################
        ##Kanji model
        #fact_type = FactType(name='Kanji')
        #fact_type.save()
        #expression_field = FieldType(name='Kanji Expression', fact_type=fact_type, unique=False, blank=False, ordinal=0) #TODO uniqueness
        #expression_field.save()
        #meaning_field = FieldType(name='Meaning', fact_type=fact_type, unique=False, blank=False, ordinal=2)
        #meaning_field.save()
        #reading_field = FieldType(name='Reading', fact_type=fact_type, unique=False, blank=True, ordinal=1)
        #reading_field.save()

        ## templates
        ## production:
        #production_card_template = CardTemplate(name='Writing', fact_type=fact_type, front_template_name='', back_template_name='', generate_by_default=True, ordinal=0)
        #production_card_template.save()
        #front_template_content = '{{{{ fields.{0} }}}}<br>{{{{ fields.{1} }}}}'.format(reading_field.id, meaning_field.id)
        #front_template_name = u'flashcards/shared/{0}/{1}_front.html'.format(fact_type.id, production_card_template.id)
        #back_template_content = '{{{{ fields.{0} }}}}'.format(expression_field.id)
        #back_template_name = u'flashcards/shared/{0}/{1}_back.html'.format(fact_type.id, production_card_template.id)
        #tmplt = Template(name=front_template_name, content=front_template_content)
        #tmplt.save()
        #tmplt.sites.add(settings.SITE_ID)
        #tmplt.save()
        #tmplt = Template(name=back_template_name, content=back_template_content)
        #tmplt.save()
        #tmplt.sites.add(settings.SITE_ID)
        #tmplt.save()
        #production_card_template.front_template_name = front_template_name
        #production_card_template.back_template_name = back_template_name
        #production_card_template.save()

        kanji_reading_card_template = CardTemplate(name='Kanji Reading', fact_type=japanese_fact_type, front_template_name='', back_template_name='', generate_by_default=False, ordinal=3)
        kanji_reading_card_template.front_prompt = u'How do you read this kanji?'
        kanji_reading_card_template.save()
        front_template_content = '{{{{ fields.{0}.content|linebreaksbr }}}}<br>{{{{ fields.{1}.content|linebreaksbr }}}}'.format(expression_field.id, meaning_field.id)
        front_template_name = u'flashcards/shared/{0}/{1}_front.html'.format(japanese_fact_type.id, kanji_reading_card_template.id)
        back_template_content = '{{{{ fields.{0}.content|linebreaksbr }}}}'.format(reading_field.id)
        back_template_name = u'flashcards/shared/{0}/{1}_back.html'.format(japanese_fact_type.id, kanji_reading_card_template.id)
        tmplt = Template(name=front_template_name, content=self._add_front_prompt(self._wrap_furiganaize_template_tag(front_template_content), kanji_reading_card_template))
        tmplt.save()
        tmplt.sites.add(settings.SITE_ID)
        tmplt.save()
        tmplt = Template(name=back_template_name, content=self._wrap_furiganaize_template_tag(back_template_content))
        tmplt.save()
        tmplt.sites.add(settings.SITE_ID)
        tmplt.save()
        kanji_reading_card_template.front_template_name = front_template_name
        kanji_reading_card_template.back_template_name = back_template_name
        kanji_reading_card_template.requisite_field_types.add(meaning_field, reading_field, expression_field)
        kanji_reading_card_template.save()


        kanji_writing_card_template = CardTemplate(name='Kanji Writing', fact_type=japanese_fact_type, front_template_name='', back_template_name='', generate_by_default=False, ordinal=4)
        kanji_writing_card_template.front_prompt = u'How do you write this in kanji?'
        kanji_writing_card_template.save()
        front_template_content = '{{{{ fields.{0}.strip_ruby_bottom }}}}<br>{{{{ fields.{1}.content|linebreaksbr }}}}'.format(reading_field.id, meaning_field.id)
        front_template_name = u'flashcards/shared/{0}/{1}_front.html'.format(japanese_fact_type.id, kanji_writing_card_template.id)
        back_template_content = '{{{{ fields.{0}.content|linebreaksbr }}}}'.format(expression_field.id)
        back_template_name = u'flashcards/shared/{0}/{1}_back.html'.format(japanese_fact_type.id, kanji_writing_card_template.id)
        tmplt = Template(name=front_template_name, content=self._add_front_prompt(self._wrap_furiganaize_template_tag(front_template_content), kanji_writing_card_template))
        tmplt.save()
        tmplt.sites.add(settings.SITE_ID)
        tmplt.save()
        tmplt = Template(name=back_template_name, content=self._wrap_furiganaize_template_tag(back_template_content))
        tmplt.save()
        tmplt.sites.add(settings.SITE_ID)
        tmplt.save()
        kanji_writing_card_template.front_template_name = front_template_name
        kanji_writing_card_template.back_template_name = back_template_name
        kanji_writing_card_template.requisite_field_types.add(meaning_field, reading_field, expression_field)
        kanji_writing_card_template.save()

        ##meaning:
        #meaning_card_template = CardTemplate(name='Meaning', fact_type=fact_type, front_template_name='', back_template_name='', generate_by_default=True, ordinal=2)
        #meaning_card_template.save()
        #front_template_content = '{{{{ fields.{0} }}}}<br>{{{{ fields.{1} }}}}'.format(expression_field.id, reading_field.id)
        #front_template_name = u'flashcards/shared/{0}/{1}_front.html'.format(fact_type.id, meaning_card_template.id)
        #back_template_content = '{{{{ fields.{0} }}}}'.format(meaning_field.id)
        #back_template_name = u'flashcards/shared/{0}/{1}_back.html'.format(fact_type.id, meaning_card_template.id)
        #tmplt = Template(name=front_template_name, content=front_template_content)
        #tmplt.save()
        #tmplt.sites.add(settings.SITE_ID)
        #tmplt.save()
        #tmplt = Template(name=back_template_name, content=back_template_content)
        #tmplt.save()
        #tmplt.sites.add(settings.SITE_ID)
        #tmplt.save()
        #meaning_card_template.front_template_name = front_template_name
        #meaning_card_template.back_template_name = back_template_name
        #meaning_card_template.save()

