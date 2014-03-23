# encoding: utf8
from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('flashcards', '0004_card_fact'),
    ]

    operations = [
        migrations.AddField(
            model_name='card',
            name='deck',
            field=models.ForeignKey(to='flashcards.Deck', to_field=u'id'),
            preserve_default=True,
        ),
    ]
