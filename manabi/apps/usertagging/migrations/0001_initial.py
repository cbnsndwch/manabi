# encoding: utf8
from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Tag',
            fields=[
                (u'id', models.AutoField(verbose_name=u'ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=50, verbose_name=u'name', db_index=True)),
                ('owner', models.ForeignKey(to_field=u'id', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                u'ordering': ('name',),
                u'unique_together': set([('name', 'owner')]),
                u'verbose_name': u'tag',
                u'verbose_name_plural': u'tags',
            },
            bases=(models.Model,),
        ),
    ]
