# encoding: utf8
from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Textbook',
            fields=[
                (u'id', models.AutoField(verbose_name=u'ID', serialize=False, auto_created=True, primary_key=True)),
                ('slug', models.SlugField(blank=True)),
                ('isbn', models.CharField(max_length=13)),
                ('custom_title', models.CharField(help_text='Set this to override the Amazon product name.', max_length=200, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Card',
            fields=[
                (u'id', models.AutoField(verbose_name=u'ID', serialize=False, auto_created=True, primary_key=True)),
                ('template', models.SmallIntegerField(choices=[(0, 'Production'), (1, 'Recognition'), (2, 'Kanji Reading'), (3, 'Kanji Writing')])),
                ('active', models.BooleanField(default=True, db_index=True)),
                ('ease_factor', models.FloatField(null=True, blank=True)),
                ('interval', models.FloatField(db_index=True, null=True, blank=True)),
                ('due_at', models.DateTimeField(db_index=True, null=True, blank=True)),
                ('last_ease_factor', models.FloatField(null=True, blank=True)),
                ('last_interval', models.FloatField(null=True, blank=True)),
                ('last_due_at', models.DateTimeField(null=True, blank=True)),
                ('last_reviewed_at', models.DateTimeField(null=True, blank=True)),
                ('last_review_grade', models.PositiveIntegerField(null=True, blank=True)),
                ('last_failed_at', models.DateTimeField(null=True, blank=True)),
                ('review_count', models.PositiveIntegerField(default=0, editable=False)),
                ('new_card_ordinal', models.PositiveIntegerField(null=True, blank=True)),
                ('suspended', models.BooleanField(default=False, db_index=True)),
                ('leech', models.BooleanField(default=False)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CardHistory',
            fields=[
                (u'id', models.AutoField(verbose_name=u'ID', serialize=False, auto_created=True, primary_key=True)),
                ('card', models.ForeignKey(to='flashcards.Card', to_field=u'id')),
                ('response', models.PositiveIntegerField(editable=False)),
                ('reviewed_at', models.DateTimeField()),
                ('ease_factor', models.FloatField(null=True, blank=True)),
                ('interval', models.FloatField(db_index=True, null=True, blank=True)),
                ('was_new', models.BooleanField(default=False, db_index=True)),
                ('question_duration', models.FloatField(null=True, blank=True)),
                ('duration', models.FloatField(null=True, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
