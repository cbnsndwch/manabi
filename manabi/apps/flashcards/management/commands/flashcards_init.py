from django.core.management.base import BaseCommand


def create_initial_data():
    from django.conf import settings
    from manabi.apps.flashcards.models.facts import FactType
    from manabi.apps.flashcards.models.fields import FieldType
    import manabi.apps.flashcards.partsofspeech as partsofspeech
    import pickle

    #Japanese model
    japanese_fact_type = FactType(name='Japanese')
    japanese_fact_type.save()
    assert japanese_fact_type.id == FactType.objects.japanese.id
    meaning_field = FieldType.objects.create(
        display_name='Meaning',
        name='meaning',
        fact_type=japanese_fact_type,
        unique=True,
        blank=False,
        ordinal=1,
    )
    reading_field = FieldType.objects.create(
        display_name='Reading',
        name='reading',
        fact_type=japanese_fact_type,
        unique=False,
        blank=True,
        ordinal=2,
    )
    expression_field = FieldType.objects.create(
        display_name='Expression',
        name='expression',
        fact_type=japanese_fact_type,
        transliteration_field_type=reading_field,
        unique=True,
        blank=False,
        ordinal=0,
    )
    part_of_speech_choices = pickle.dumps(partsofspeech.ALL_PART_OF_SPEECH_CHOICES)
    pos_field = FieldType.objects.create(
        display_name='Part of Speech',
        name='part_of_speech',
        hidden_in_grid=True,
        disabled_in_form=True,
        hidden_in_form=True,
        fact_type=japanese_fact_type,
        unique=False,
        blank=True,
        choices=part_of_speech_choices,
        grid_column_width='7.4em',
        ordinal=4,
    )
    notes_field = FieldType.objects.create(
        display_name='Notes',
        name='notes',
        fact_type=japanese_fact_type,
        unique=False,
        blank=True,
        hidden_in_form=True,
        hidden_in_grid=True,
        ordinal=5,
    )

    #sub-model for example sentences inside a fact
    sub_japanese_fact_type = FactType.objects.create(
        name='Example Sentence',
        parent_fact_type=japanese_fact_type,
        many_children_per_fact=True,
    )
    sub_meaning_field = FieldType.objects.create(
        display_name='Meaning',
        name='meaning',
        fact_type=sub_japanese_fact_type,
        unique=True,
        blank=False,
        ordinal=1,
    )
    sub_reading_field = FieldType.objects.create(
        display_name='Reading',
        name='reading',
        fact_type=sub_japanese_fact_type,
        unique=False,
        blank=True,
        ordinal=2,
    )
    sub_expression_field = FieldType.objects.create(
        display_name='Expression',
        name='expression',
        fact_type=sub_japanese_fact_type,
        transliteration_field_type=sub_reading_field,
        unique=True,
        blank=False,
        ordinal=0,
    )
    #sub_reading_field = FieldType(name='Source', fact_type=sub_japanese_fact_type, unique=False, blank=True, ordinal=2)
    #sub_reading_field.save()


    ## templates


class Command(BaseCommand):
    def handle(self, *args, **options):
        create_initial_data()

