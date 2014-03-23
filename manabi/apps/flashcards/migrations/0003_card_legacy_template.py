# encoding: utf8
from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('flashcards', '0002_cardtemplate_deck_fact_facttype_fieldcontent_fieldtype_undocardreview'),
    ]

    operations = [
        migrations.AddField(
            model_name='card',
            name='legacy_template',
            field=models.ForeignKey(to_field=u'id', to='flashcards.CardTemplate', blank=True, null=True, db_index=False),
            preserve_default=True,
        ),
    ]
