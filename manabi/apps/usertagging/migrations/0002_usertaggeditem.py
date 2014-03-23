# encoding: utf8
from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '__first__'),
        (u'usertagging', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserTaggedItem',
            fields=[
                (u'id', models.AutoField(verbose_name=u'ID', serialize=False, auto_created=True, primary_key=True)),
                ('tag', models.ForeignKey(to=u'usertagging.Tag', to_field=u'id', verbose_name=u'tag')),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType', to_field=u'id', verbose_name=u'content type')),
                ('object_id', models.PositiveIntegerField(verbose_name=u'object id', db_index=True)),
            ],
            options={
                u'unique_together': set([('tag', 'content_type', 'object_id')]),
                u'verbose_name': u'tagged item',
                u'verbose_name_plural': u'tagged items',
            },
            bases=(models.Model,),
        ),
    ]
