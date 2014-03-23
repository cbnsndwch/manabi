# encoding: utf8
from django.db import models, migrations
from django.conf import settings
import picklefield.fields


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('flashcards', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='UndoCardReview',
            fields=[
                (u'id', models.AutoField(verbose_name=u'ID', serialize=False, auto_created=True, primary_key=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, to_field=u'id')),
                ('card', models.ForeignKey(to='flashcards.Card', to_field=u'id')),
                ('card_history', models.ForeignKey(to='flashcards.CardHistory', to_field=u'id')),
                ('pickled_card', picklefield.fields.PickledObjectField(editable=False)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CardTemplate',
            fields=[
                (u'id', models.AutoField(verbose_name=u'ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=50)),
                ('description', models.TextField(max_length=200, blank=True)),
                ('front_template_name', models.CharField(max_length=50)),
                ('back_template_name', models.CharField(max_length=50)),
                ('front_prompt', models.CharField(max_length=200, blank=True)),
                ('back_prompt', models.CharField(max_length=200, blank=True)),
                ('js_template', models.TextField(max_length=600, blank=True)),
                ('card_synchronization_group', models.SmallIntegerField(null=True, blank=True)),
                ('generate_by_default', models.BooleanField(default=True)),
                ('ordinal', models.IntegerField(null=True, blank=True)),
                ('hide_front', models.BooleanField(default=False)),
                ('allow_blank_back', models.BooleanField(default=True)),
                ('active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                u'ordering': ['ordinal'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Deck',
            fields=[
                (u'id', models.AutoField(verbose_name=u'ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField(max_length=2000, blank=True)),
                ('owner', models.ForeignKey(to=settings.AUTH_USER_MODEL, to_field=u'id')),
                ('textbook_source', models.ForeignKey(to_field=u'id', blank=True, to='flashcards.Textbook', null=True)),
                ('picture', models.FileField(null=True, upload_to='/deck_media/', blank=True)),
                ('priority', models.IntegerField(default=0, blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('shared', models.BooleanField(default=False)),
                ('shared_at', models.DateTimeField(null=True, blank=True)),
                ('suspended', models.BooleanField(default=False, db_index=True)),
                ('active', models.BooleanField(default=True, db_index=True)),
            ],
            options={
                u'ordering': ('name',),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Fact',
            fields=[
                (u'id', models.AutoField(verbose_name=u'ID', serialize=False, auto_created=True, primary_key=True)),
                ('deck', models.ForeignKey(to_field=u'id', blank=True, to='flashcards.Deck', null=True)),
                ('new_fact_ordinal', models.PositiveIntegerField(null=True, blank=True)),
                ('active', models.BooleanField(default=True)),
                ('expression', models.CharField(max_length=500)),
                ('reading', models.CharField(max_length=1500, blank=True)),
                ('meaning', models.CharField(max_length=1000)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(null=True, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='FactType',
            fields=[
                (u'id', models.AutoField(verbose_name=u'ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=50)),
                ('active', models.BooleanField(default=True)),
                ('many_children_per_fact', models.NullBooleanField()),
                ('space_factor', models.FloatField(default=0.1)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='FieldContent',
            fields=[
                (u'id', models.AutoField(verbose_name=u'ID', serialize=False, auto_created=True, primary_key=True)),
                ('fact', models.ForeignKey(to='flashcards.Fact', to_field=u'id')),
                ('content', models.CharField(max_length=1000, blank=True)),
                ('media_uri', models.URLField(blank=True)),
                ('media_file', models.FileField(null=True, upload_to='/card_media/', blank=True)),
                ('cached_transliteration_without_markup', models.CharField(max_length=1000, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='FieldType',
            fields=[
                (u'id', models.AutoField(verbose_name=u'ID', serialize=False, auto_created=True, primary_key=True)),
                ('fact_type', models.ForeignKey(to='flashcards.FactType', to_field=u'id')),
                ('name', models.CharField(max_length=50)),
                ('display_name', models.CharField(max_length=50)),
                ('unique', models.BooleanField(default=True)),
                ('blank', models.BooleanField(default=False)),
                ('editable', models.BooleanField(default=True)),
                ('numeric', models.BooleanField(default=False)),
                ('multi_line', models.BooleanField(default=True)),
                ('choices', models.CharField(help_text='Use a pickled choices tuple. The "none" value is used to indicate no selection, so don\'t use it in the choices tuple.', max_length=1000, blank=True)),
                ('help_text', models.CharField(max_length=500, blank=True)),
                ('language', models.CharField(blank=True, max_length=3, null=True, choices=[('eng', 'English'), ('jpn', 'Japanese')])),
                ('character_restriction', models.CharField(blank=True, max_length=3, null=True, choices=[('num', 'Numeric'), ('knj', 'Kanji'), ('kna', 'Kana'), ('hir', 'Hiragana'), ('kat', 'Katakana')])),
                ('accepts_media', models.BooleanField(default=False)),
                ('media_restriction', models.CharField(blank=True, max_length=3, null=True, choices=[('img', 'Image'), ('vid', 'Video'), ('snd', 'Sound')])),
                ('hidden_in_form', models.BooleanField(default=False)),
                ('disabled_in_form', models.BooleanField(default=False, help_text='Disable this field when adding/editing a fact. If hidden_in_form is also True, then it will supress the Add `name` link in the form.')),
                ('hidden_in_grid', models.BooleanField(default=False)),
                ('grid_column_width', models.CharField(max_length=10, blank=True)),
                ('ordinal', models.IntegerField(null=True, blank=True)),
                ('active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
