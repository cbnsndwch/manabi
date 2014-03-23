# encoding: utf8
from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('flashcards', '0009_fact_synchronized_with'),
    ]

    operations = [
        migrations.AddField(
            model_name='facttype',
            name='parent_fact_type',
            field=models.ForeignKey(to_field=u'id', blank=True, to='flashcards.FactType', null=True),
            preserve_default=True,
        ),
    ]
