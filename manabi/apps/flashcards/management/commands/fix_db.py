# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import re

from django.core.management.base import BaseCommand
from django.db import connections

from manabi.apps.flashcards.models import Fact


def new_reading(reading):
    reading = re.sub(ur'^(\w+)\[(\w*)\]', ur'｜\1《\2》',
                     reading, flags=re.UNICODE)
    reading = re.sub(ur' (\w+)\[(\w*)\]', ur'｜\1《\2》',
                     reading, flags=re.UNICODE)
    print reading
    return reading


def do_it():
    with connections['old'].cursor() as old_cursor:
        for fact in Fact.objects.all().iterator():
            try:
                old_cursor.execute(
                    'select content from flashcards_fieldcontent where '
                    'fact_id = %s and field_type_id = 3', [fact.id])
                old_expression = old_cursor.fetchone()[0]
                old_cursor.execute(
                    'select content from flashcards_fieldcontent where '
                    'fact_id = %s and field_type_id = 2', [fact.id])
                old_reading = old_cursor.fetchone()[0]
                old_cursor.execute(
                    'select content from flashcards_fieldcontent where '
                    'fact_id = %s and field_type_id = 1', [fact.id])
                old_meaning = old_cursor.fetchone()[0]
            except TypeError:
                continue

            old_reading = new_reading(old_reading)

            print u'changing {} {} {} ...'.format(fact.expression, fact.reading, fact.meaning)
            print u'... to {} {} {}'.format(old_expression, old_reading, old_meaning)
            print

            fact.expression = old_expression
            fact.reading = old_reading
            fact.meaning = old_meaning
            fact.save(update_fields=['expression', 'reading', 'meaning'])


class Command(BaseCommand):
    def handle(self, *args, **options):
        do_it()
