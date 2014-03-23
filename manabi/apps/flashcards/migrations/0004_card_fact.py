# encoding: utf8
from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('flashcards', '0003_card_legacy_template'),
    ]

    operations = [
        migrations.AddField(
            model_name='card',
            name='fact',
            field=models.ForeignKey(to='flashcards.Fact', to_field=u'id'),
            preserve_default=True,
        ),
    ]
