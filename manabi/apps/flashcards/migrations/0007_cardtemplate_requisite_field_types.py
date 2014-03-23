# encoding: utf8
from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('flashcards', '0006_cardtemplate_fact_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='cardtemplate',
            name='requisite_field_types',
            field=models.ManyToManyField(to='flashcards.FieldType', blank=True),
            preserve_default=True,
        ),
    ]
