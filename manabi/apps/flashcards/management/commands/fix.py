from django.core.management.base import BaseCommand
from django.db import connections

from manabi.apps.flashcards.models import Card



class Command(BaseCommand):
    def handle(self, *args, **options):
        old_cursor = connections['old'].cursor()

        for old_card_id in Card.objects.using('old').all().values_list('id', flat=True).order_by('id').iterator():
            try:
                new_card = Card.objects.get(id=old_card_id)
            except Card.DoesNotExist:
                continue

            old_cursor.execute('select legacy_template_id, id from flashcards_card where id = %s', [old_card_id])
            leg_row = old_cursor.fetchone()
            legacy_id = leg_row[0]

            if legacy_id == 1:
                new_template = 0
            elif legacy_id == 2:
                new_template = 1
            elif legacy_id == 3:
                new_template = 2
            elif legacy_id == 4:
                new_template = 3
            else:
                print leg_row
                raise ValueError("what")

            print old_card_id,
            print new_card.template,
            new_card.template = new_template
            new_card.save(update_fields=['template'])
            print '->', new_template
            # print old_card_id, legacy_id
