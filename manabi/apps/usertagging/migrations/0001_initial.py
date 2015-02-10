# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=50, verbose_name='name', db_index=True)),
                ('owner', models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'ordering': ('name',),
                'verbose_name': 'tag',
                'verbose_name_plural': 'tags',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UserTaggedItem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField(verbose_name='object id', db_index=True)),
                ('content_type', models.ForeignKey(verbose_name='content type', to='contenttypes.ContentType')),
                ('tag', models.ForeignKey(related_name=b'items', verbose_name='tag', to='usertagging.Tag')),
            ],
            options={
                'verbose_name': 'tagged item',
                'verbose_name_plural': 'tagged items',
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='usertaggeditem',
            unique_together=set([('tag', 'content_type', 'object_id')]),
        ),
        migrations.AlterUniqueTogether(
            name='tag',
            unique_together=set([('name', 'owner')]),
        ),
    ]
