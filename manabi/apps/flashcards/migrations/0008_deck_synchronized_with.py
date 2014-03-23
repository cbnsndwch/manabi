# encoding: utf8
from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('flashcards', '0007_cardtemplate_requisite_field_types'),
    ]

    operations = [
        migrations.AddField(
            model_name='deck',
            name='synchronized_with',
            field=models.ForeignKey(to_field=u'id', blank=True, to='flashcards.Deck', null=True),
            preserve_default=True,
        ),
    ]
