# encoding: utf8
from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('flashcards', '0010_facttype_parent_fact_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='fieldcontent',
            name='field_type',
            field=models.ForeignKey(to='flashcards.FieldType', to_field=u'id'),
            preserve_default=True,
        ),
    ]
