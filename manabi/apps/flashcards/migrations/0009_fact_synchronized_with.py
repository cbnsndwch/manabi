# encoding: utf8
from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('flashcards', '0008_deck_synchronized_with'),
    ]

    operations = [
        migrations.AddField(
            model_name='fact',
            name='synchronized_with',
            field=models.ForeignKey(to_field=u'id', blank=True, to='flashcards.Fact', null=True),
            preserve_default=True,
        ),
    ]
