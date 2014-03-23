# encoding: utf8
from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('flashcards', '0005_card_deck'),
    ]

    operations = [
        migrations.AddField(
            model_name='cardtemplate',
            name='fact_type',
            field=models.ForeignKey(to='flashcards.FactType', to_field=u'id'),
            preserve_default=True,
        ),
    ]
