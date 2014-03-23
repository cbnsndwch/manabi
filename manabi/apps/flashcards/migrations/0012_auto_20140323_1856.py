# encoding: utf8
from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('flashcards', '0011_fieldcontent_field_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='fieldtype',
            name='transliteration_field_type',
            field=models.OneToOneField(null=True, to_field=u'id', blank=True, to='flashcards.FieldType'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='cardtemplate',
            unique_together=set([('ordinal', 'fact_type'), ('name', 'fact_type')]),
        ),
        migrations.AlterUniqueTogether(
            name='fact',
            unique_together=set([('deck', 'synchronized_with')]),
        ),
        migrations.AlterUniqueTogether(
            name='fieldtype',
            unique_together=set([('ordinal', 'fact_type'), ('name', 'fact_type'), ('display_name', 'fact_type')]),
        ),
    ]
