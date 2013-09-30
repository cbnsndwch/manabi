# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
    
    def forwards(self, orm):
        
        # Adding model 'FieldType'
        db.create_table('flashcards_fieldtype', (
            ('numeric', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('grid_column_width', self.gf('django.db.models.fields.CharField')(max_length=10, blank=True)),
            ('blank', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('help_text', self.gf('django.db.models.fields.CharField')(max_length=500, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('accepts_media', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('character_restriction', self.gf('django.db.models.fields.CharField')(max_length=3, null=True, blank=True)),
            ('hidden_in_form', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('multi_line', self.gf('django.db.models.fields.BooleanField')(default=True, blank=True)),
            ('ordinal', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('hidden_in_grid', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('editable', self.gf('django.db.models.fields.BooleanField')(default=True, blank=True)),
            ('fact_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['flashcards.FactType'])),
            ('media_restriction', self.gf('django.db.models.fields.CharField')(max_length=3, null=True, blank=True)),
            ('transliteration_field_type', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['flashcards.FieldType'], unique=True, null=True, blank=True)),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=True, blank=True)),
            ('unique', self.gf('django.db.models.fields.BooleanField')(default=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('language', self.gf('django.db.models.fields.CharField')(max_length=3, null=True, blank=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('choices', self.gf('django.db.models.fields.CharField')(max_length=1000, blank=True)),
        ))
        db.send_create_signal('flashcards', ['FieldType'])

        # Adding unique constraint on 'FieldType', fields ['name', 'fact_type']
        db.create_unique('flashcards_fieldtype', ['name', 'fact_type_id'])

        # Adding unique constraint on 'FieldType', fields ['ordinal', 'fact_type']
        db.create_unique('flashcards_fieldtype', ['ordinal', 'fact_type_id'])

        # Adding model 'SharedFieldContent'
        db.create_table('flashcards_sharedfieldcontent', (
            ('field_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['flashcards.FieldType'])),
            ('cached_transliteration_without_markup', self.gf('django.db.models.fields.CharField')(max_length=1000, blank=True)),
            ('content', self.gf('django.db.models.fields.CharField')(max_length=1000, blank=True)),
            ('media_file', self.gf('django.db.models.fields.files.FileField')(max_length=100, null=True, blank=True)),
            ('media_uri', self.gf('django.db.models.fields.URLField')(max_length=200, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('fact', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['flashcards.SharedFact'])),
        ))
        db.send_create_signal('flashcards', ['SharedFieldContent'])

        # Adding model 'FieldContent'
        db.create_table('flashcards_fieldcontent', (
            ('field_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['flashcards.FieldType'])),
            ('cached_transliteration_without_markup', self.gf('django.db.models.fields.CharField')(max_length=1000, blank=True)),
            ('content', self.gf('django.db.models.fields.CharField')(max_length=1000, blank=True)),
            ('media_file', self.gf('django.db.models.fields.files.FileField')(max_length=100, null=True, blank=True)),
            ('media_uri', self.gf('django.db.models.fields.URLField')(max_length=200, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('fact', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['flashcards.Fact'])),
        ))
        db.send_create_signal('flashcards', ['FieldContent'])

        # Adding model 'FactType'
        db.create_table('flashcards_facttype', (
            ('space_factor', self.gf('django.db.models.fields.FloatField')(default=0.10000000000000001)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('min_card_space', self.gf('django.db.models.fields.FloatField')(default=0.0069444444444444441)),
            ('modified_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('many_children_per_fact', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('parent_fact_type', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='child_fact_types', null=True, to=orm['flashcards.FactType'])),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=True, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('flashcards', ['FactType'])

        # Adding model 'SharedFact'
        db.create_table('flashcards_sharedfact', (
            ('priority', self.gf('django.db.models.fields.IntegerField')(default=0, null=True, blank=True)),
            ('parent_fact', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='child_facts', null=True, to=orm['flashcards.SharedFact'])),
            ('deck', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['flashcards.SharedDeck'], null=True, blank=True)),
            ('notes', self.gf('django.db.models.fields.CharField')(max_length=1000, blank=True)),
            ('modified_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('fact_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['flashcards.FactType'])),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=True, blank=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('flashcards', ['SharedFact'])

        # Adding model 'Fact'
        db.create_table('flashcards_fact', (
            ('priority', self.gf('django.db.models.fields.IntegerField')(default=0, null=True, blank=True)),
            ('parent_fact', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='child_facts', null=True, to=orm['flashcards.Fact'])),
            ('deck', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['flashcards.Deck'], null=True, blank=True)),
            ('notes', self.gf('django.db.models.fields.CharField')(max_length=1000, blank=True)),
            ('modified_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('fact_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['flashcards.FactType'])),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=True, blank=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('flashcards', ['Fact'])

        # Adding model 'CardTemplate'
        db.create_table('flashcards_cardtemplate', (
            ('back_prompt', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True)),
            ('ordinal', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('back_template_name', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('description', self.gf('django.db.models.fields.TextField')(max_length=200, blank=True)),
            ('front_prompt', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('hide_front', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('modified_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('fact_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['flashcards.FactType'])),
            ('card_synchronization_group', self.gf('django.db.models.fields.SmallIntegerField')(null=True, blank=True)),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=True, blank=True)),
            ('generate_by_default', self.gf('django.db.models.fields.BooleanField')(default=True, blank=True)),
            ('allow_blank_back', self.gf('django.db.models.fields.BooleanField')(default=True, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('front_template_name', self.gf('django.db.models.fields.CharField')(max_length=50)),
        ))
        db.send_create_signal('flashcards', ['CardTemplate'])

        # Adding unique constraint on 'CardTemplate', fields ['name', 'fact_type']
        db.create_unique('flashcards_cardtemplate', ['name', 'fact_type_id'])

        # Adding unique constraint on 'CardTemplate', fields ['ordinal', 'fact_type']
        db.create_unique('flashcards_cardtemplate', ['ordinal', 'fact_type_id'])

        # Adding M2M table for field requisite_field_types on 'CardTemplate'
        db.create_table('flashcards_cardtemplate_requisite_field_types', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('cardtemplate', models.ForeignKey(orm['flashcards.cardtemplate'], null=False)),
            ('fieldtype', models.ForeignKey(orm['flashcards.fieldtype'], null=False))
        ))
        db.create_unique('flashcards_cardtemplate_requisite_field_types', ['cardtemplate_id', 'fieldtype_id'])

        # Adding model 'ReviewStatistics'
        db.create_table('flashcards_reviewstatistics', (
            ('new_reviews_today', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('last_failed_review_at', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['auth.User'], unique=True)),
            ('last_new_review_at', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('failed_reviews_today', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
        ))
        db.send_create_signal('flashcards', ['ReviewStatistics'])

        # Adding model 'UndoCardReview'
        db.create_table('flashcards_undocardreview', (
            ('card_history', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['flashcards.CardHistory'])),
            ('timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('pickled_review_stats', self.gf('picklefield.fields.PickledObjectField')()),
            ('pickled_card', self.gf('picklefield.fields.PickledObjectField')()),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('card', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['flashcards.Card'])),
        ))
        db.send_create_signal('flashcards', ['UndoCardReview'])

        # Adding model 'SharedCard'
        db.create_table('flashcards_sharedcard', (
            ('template', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['flashcards.CardTemplate'])),
            ('priority', self.gf('django.db.models.fields.IntegerField')(default=0, null=True, blank=True)),
            ('new_card_ordinal', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
            ('fact', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['flashcards.SharedFact'])),
            ('suspended', self.gf('django.db.models.fields.BooleanField')(default=False, db_index=True, blank=True)),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=True, db_index=True, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('leech', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
        ))
        db.send_create_signal('flashcards', ['SharedCard'])

        # Adding unique constraint on 'SharedCard', fields ['fact', 'template']
        db.create_unique('flashcards_sharedcard', ['fact_id', 'template_id'])

        # Adding model 'Card'
        db.create_table('flashcards_card', (
            ('last_reviewed_at', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('last_failed_at', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('synchronized_with', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['flashcards.Card'], null=True, blank=True)),
            ('review_count', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('template', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['flashcards.CardTemplate'])),
            ('due_at', self.gf('django.db.models.fields.DateTimeField')(db_index=True, null=True, blank=True)),
            ('last_due_at', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('ease_factor', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('last_review_grade', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
            ('interval', self.gf('django.db.models.fields.FloatField')(db_index=True, null=True, blank=True)),
            ('priority', self.gf('django.db.models.fields.IntegerField')(default=0, null=True, blank=True)),
            ('new_card_ordinal', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
            ('fact', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['flashcards.Fact'])),
            ('suspended', self.gf('django.db.models.fields.BooleanField')(default=False, db_index=True, blank=True)),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=True, db_index=True, blank=True)),
            ('last_ease_factor', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('last_interval', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('leech', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
        ))
        db.send_create_signal('flashcards', ['Card'])

        # Adding unique constraint on 'Card', fields ['fact', 'template']
        db.create_unique('flashcards_card', ['fact_id', 'template_id'])

        # Adding model 'CardStatistics'
        db.create_table('flashcards_cardstatistics', (
            ('first_success_at', self.gf('django.db.models.fields.DateTimeField')()),
            ('failure_count', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('yes_count', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('skip_count', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('successive_count', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('average_successive_count', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('successive_streak_count', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('average_thinking_time', self.gf('django.db.models.fields.PositiveIntegerField')(null=True)),
            ('total_review_time', self.gf('django.db.models.fields.FloatField')(default=0)),
            ('first_reviewed_at', self.gf('django.db.models.fields.DateTimeField')()),
            ('no_count', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('card', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['flashcards.Card'])),
        ))
        db.send_create_signal('flashcards', ['CardStatistics'])

        # Adding model 'CardHistory'
        db.create_table('flashcards_cardhistory', (
            ('reviewed_at', self.gf('django.db.models.fields.DateTimeField')()),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('card', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['flashcards.Card'])),
            ('response', self.gf('django.db.models.fields.PositiveIntegerField')()),
        ))
        db.send_create_signal('flashcards', ['CardHistory'])

        # Adding model 'Textbook'
        db.create_table('flashcards_textbook', (
            ('isbn', self.gf('django.db.models.fields.CharField')(max_length=20, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(max_length=2000, blank=True)),
            ('purchase_url', self.gf('django.db.models.fields.URLField')(max_length=200, blank=True)),
            ('edition', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('cover_picture', self.gf('django.db.models.fields.files.FileField')(max_length=100, null=True, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
        ))
        db.send_create_signal('flashcards', ['Textbook'])

        # Adding model 'SharedDeck'
        db.create_table('flashcards_shareddeck', (
            ('downloads', self.gf('django.db.models.fields.PositiveIntegerField')(default=0, blank=True)),
            ('picture', self.gf('django.db.models.fields.files.FileField')(max_length=100, null=True, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(max_length=2000, blank=True)),
            ('textbook_source', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['flashcards.Textbook'], null=True, blank=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('priority', self.gf('django.db.models.fields.IntegerField')(default=0, blank=True)),
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
        ))
        db.send_create_signal('flashcards', ['SharedDeck'])

        # Adding model 'Deck'
        db.create_table('flashcards_deck', (
            ('picture', self.gf('django.db.models.fields.files.FileField')(max_length=100, null=True, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(max_length=2000, blank=True)),
            ('textbook_source', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['flashcards.Textbook'], null=True, blank=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('priority', self.gf('django.db.models.fields.IntegerField')(default=0, blank=True)),
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
        ))
        db.send_create_signal('flashcards', ['Deck'])

        # Adding model 'SchedulingOptions'
        db.create_table('flashcards_schedulingoptions', (
            ('medium_interval_min', self.gf('django.db.models.fields.FloatField')(default=3.0)),
            ('unknown_interval_min', self.gf('django.db.models.fields.FloatField')(default=0.013888888888888888)),
            ('easy_interval_max', self.gf('django.db.models.fields.FloatField')(default=9.0)),
            ('deck', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['flashcards.Deck'], unique=True)),
            ('hard_interval_min', self.gf('django.db.models.fields.FloatField')(default=0.33300000000000002)),
            ('easy_interval_min', self.gf('django.db.models.fields.FloatField')(default=7.0)),
            ('hard_interval_max', self.gf('django.db.models.fields.FloatField')(default=0.5)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('mature_unknown_interval_max', self.gf('django.db.models.fields.FloatField')(default=0.33300000000000002)),
            ('medium_interval_max', self.gf('django.db.models.fields.FloatField')(default=5.0)),
            ('unknown_interval_max', self.gf('django.db.models.fields.FloatField')(default=0.017361111111111112)),
            ('mature_unknown_interval_min', self.gf('django.db.models.fields.FloatField')(default=0.33300000000000002)),
        ))
        db.send_create_signal('flashcards', ['SchedulingOptions'])
    
    
    def backwards(self, orm):
        
        # Deleting model 'FieldType'
        db.delete_table('flashcards_fieldtype')

        # Removing unique constraint on 'FieldType', fields ['name', 'fact_type']
        db.delete_unique('flashcards_fieldtype', ['name', 'fact_type_id'])

        # Removing unique constraint on 'FieldType', fields ['ordinal', 'fact_type']
        db.delete_unique('flashcards_fieldtype', ['ordinal', 'fact_type_id'])

        # Deleting model 'SharedFieldContent'
        db.delete_table('flashcards_sharedfieldcontent')

        # Deleting model 'FieldContent'
        db.delete_table('flashcards_fieldcontent')

        # Deleting model 'FactType'
        db.delete_table('flashcards_facttype')

        # Deleting model 'SharedFact'
        db.delete_table('flashcards_sharedfact')

        # Deleting model 'Fact'
        db.delete_table('flashcards_fact')

        # Deleting model 'CardTemplate'
        db.delete_table('flashcards_cardtemplate')

        # Removing unique constraint on 'CardTemplate', fields ['name', 'fact_type']
        db.delete_unique('flashcards_cardtemplate', ['name', 'fact_type_id'])

        # Removing unique constraint on 'CardTemplate', fields ['ordinal', 'fact_type']
        db.delete_unique('flashcards_cardtemplate', ['ordinal', 'fact_type_id'])

        # Removing M2M table for field requisite_field_types on 'CardTemplate'
        db.delete_table('flashcards_cardtemplate_requisite_field_types')

        # Deleting model 'ReviewStatistics'
        db.delete_table('flashcards_reviewstatistics')

        # Deleting model 'UndoCardReview'
        db.delete_table('flashcards_undocardreview')

        # Deleting model 'SharedCard'
        db.delete_table('flashcards_sharedcard')

        # Removing unique constraint on 'SharedCard', fields ['fact', 'template']
        db.delete_unique('flashcards_sharedcard', ['fact_id', 'template_id'])

        # Deleting model 'Card'
        db.delete_table('flashcards_card')

        # Removing unique constraint on 'Card', fields ['fact', 'template']
        db.delete_unique('flashcards_card', ['fact_id', 'template_id'])

        # Deleting model 'CardStatistics'
        db.delete_table('flashcards_cardstatistics')

        # Deleting model 'CardHistory'
        db.delete_table('flashcards_cardhistory')

        # Deleting model 'Textbook'
        db.delete_table('flashcards_textbook')

        # Deleting model 'SharedDeck'
        db.delete_table('flashcards_shareddeck')

        # Deleting model 'Deck'
        db.delete_table('flashcards_deck')

        # Deleting model 'SchedulingOptions'
        db.delete_table('flashcards_schedulingoptions')
    
    
    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'flashcards.card': {
            'Meta': {'unique_together': "(('fact', 'template'),)", 'object_name': 'Card'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True', 'blank': 'True'}),
            'due_at': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'ease_factor': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'fact': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flashcards.Fact']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'interval': ('django.db.models.fields.FloatField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'last_due_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'last_ease_factor': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'last_failed_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'last_interval': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'last_review_grade': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'last_reviewed_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'leech': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'new_card_ordinal': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'priority': ('django.db.models.fields.IntegerField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            'review_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'suspended': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True', 'blank': 'True'}),
            'synchronized_with': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flashcards.Card']", 'null': 'True', 'blank': 'True'}),
            'template': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flashcards.CardTemplate']"})
        },
        'flashcards.cardhistory': {
            'Meta': {'object_name': 'CardHistory'},
            'card': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flashcards.Card']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'response': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'reviewed_at': ('django.db.models.fields.DateTimeField', [], {})
        },
        'flashcards.cardstatistics': {
            'Meta': {'object_name': 'CardStatistics'},
            'average_successive_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'average_thinking_time': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'}),
            'card': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flashcards.Card']"}),
            'failure_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'first_reviewed_at': ('django.db.models.fields.DateTimeField', [], {}),
            'first_success_at': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'no_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'skip_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'successive_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'successive_streak_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'total_review_time': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'yes_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'})
        },
        'flashcards.cardtemplate': {
            'Meta': {'unique_together': "(('name', 'fact_type'), ('ordinal', 'fact_type'))", 'object_name': 'CardTemplate'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'allow_blank_back': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'back_prompt': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'back_template_name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'card_synchronization_group': ('django.db.models.fields.SmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'max_length': '200', 'blank': 'True'}),
            'fact_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flashcards.FactType']"}),
            'front_prompt': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'front_template_name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'generate_by_default': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'hide_front': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'ordinal': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'requisite_field_types': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['flashcards.FieldType']", 'blank': 'True'})
        },
        'flashcards.deck': {
            'Meta': {'object_name': 'Deck'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'max_length': '2000', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'picture': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'priority': ('django.db.models.fields.IntegerField', [], {'default': '0', 'blank': 'True'}),
            'textbook_source': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flashcards.Textbook']", 'null': 'True', 'blank': 'True'})
        },
        'flashcards.fact': {
            'Meta': {'object_name': 'Fact'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'deck': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flashcards.Deck']", 'null': 'True', 'blank': 'True'}),
            'fact_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flashcards.FactType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'notes': ('django.db.models.fields.CharField', [], {'max_length': '1000', 'blank': 'True'}),
            'parent_fact': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'child_facts'", 'null': 'True', 'to': "orm['flashcards.Fact']"}),
            'priority': ('django.db.models.fields.IntegerField', [], {'default': '0', 'null': 'True', 'blank': 'True'})
        },
        'flashcards.facttype': {
            'Meta': {'object_name': 'FactType'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'many_children_per_fact': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'min_card_space': ('django.db.models.fields.FloatField', [], {'default': '0.0069444444444444441'}),
            'modified_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'parent_fact_type': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'child_fact_types'", 'null': 'True', 'to': "orm['flashcards.FactType']"}),
            'space_factor': ('django.db.models.fields.FloatField', [], {'default': '0.10000000000000001'})
        },
        'flashcards.fieldcontent': {
            'Meta': {'object_name': 'FieldContent'},
            'cached_transliteration_without_markup': ('django.db.models.fields.CharField', [], {'max_length': '1000', 'blank': 'True'}),
            'content': ('django.db.models.fields.CharField', [], {'max_length': '1000', 'blank': 'True'}),
            'fact': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flashcards.Fact']"}),
            'field_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flashcards.FieldType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'media_file': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'media_uri': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'})
        },
        'flashcards.fieldtype': {
            'Meta': {'unique_together': "(('name', 'fact_type'), ('ordinal', 'fact_type'))", 'object_name': 'FieldType'},
            'accepts_media': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'blank': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'character_restriction': ('django.db.models.fields.CharField', [], {'max_length': '3', 'null': 'True', 'blank': 'True'}),
            'choices': ('django.db.models.fields.CharField', [], {'max_length': '1000', 'blank': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'editable': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'fact_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flashcards.FactType']"}),
            'grid_column_width': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'}),
            'help_text': ('django.db.models.fields.CharField', [], {'max_length': '500', 'blank': 'True'}),
            'hidden_in_form': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'hidden_in_grid': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'max_length': '3', 'null': 'True', 'blank': 'True'}),
            'media_restriction': ('django.db.models.fields.CharField', [], {'max_length': '3', 'null': 'True', 'blank': 'True'}),
            'modified_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'multi_line': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'numeric': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'ordinal': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'transliteration_field_type': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['flashcards.FieldType']", 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'unique': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'})
        },
        'flashcards.reviewstatistics': {
            'Meta': {'object_name': 'ReviewStatistics'},
            'failed_reviews_today': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_failed_review_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'last_new_review_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'new_reviews_today': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.User']", 'unique': 'True'})
        },
        'flashcards.schedulingoptions': {
            'Meta': {'object_name': 'SchedulingOptions'},
            'deck': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['flashcards.Deck']", 'unique': 'True'}),
            'easy_interval_max': ('django.db.models.fields.FloatField', [], {'default': '9.0'}),
            'easy_interval_min': ('django.db.models.fields.FloatField', [], {'default': '7.0'}),
            'hard_interval_max': ('django.db.models.fields.FloatField', [], {'default': '0.5'}),
            'hard_interval_min': ('django.db.models.fields.FloatField', [], {'default': '0.33300000000000002'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mature_unknown_interval_max': ('django.db.models.fields.FloatField', [], {'default': '0.33300000000000002'}),
            'mature_unknown_interval_min': ('django.db.models.fields.FloatField', [], {'default': '0.33300000000000002'}),
            'medium_interval_max': ('django.db.models.fields.FloatField', [], {'default': '5.0'}),
            'medium_interval_min': ('django.db.models.fields.FloatField', [], {'default': '3.0'}),
            'unknown_interval_max': ('django.db.models.fields.FloatField', [], {'default': '0.017361111111111112'}),
            'unknown_interval_min': ('django.db.models.fields.FloatField', [], {'default': '0.013888888888888888'})
        },
        'flashcards.sharedcard': {
            'Meta': {'unique_together': "(('fact', 'template'),)", 'object_name': 'SharedCard'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True', 'blank': 'True'}),
            'fact': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flashcards.SharedFact']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'leech': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'new_card_ordinal': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'priority': ('django.db.models.fields.IntegerField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            'suspended': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True', 'blank': 'True'}),
            'template': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flashcards.CardTemplate']"})
        },
        'flashcards.shareddeck': {
            'Meta': {'object_name': 'SharedDeck'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'max_length': '2000', 'blank': 'True'}),
            'downloads': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'picture': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'priority': ('django.db.models.fields.IntegerField', [], {'default': '0', 'blank': 'True'}),
            'textbook_source': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flashcards.Textbook']", 'null': 'True', 'blank': 'True'})
        },
        'flashcards.sharedfact': {
            'Meta': {'object_name': 'SharedFact'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'deck': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flashcards.SharedDeck']", 'null': 'True', 'blank': 'True'}),
            'fact_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flashcards.FactType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'notes': ('django.db.models.fields.CharField', [], {'max_length': '1000', 'blank': 'True'}),
            'parent_fact': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'child_facts'", 'null': 'True', 'to': "orm['flashcards.SharedFact']"}),
            'priority': ('django.db.models.fields.IntegerField', [], {'default': '0', 'null': 'True', 'blank': 'True'})
        },
        'flashcards.sharedfieldcontent': {
            'Meta': {'object_name': 'SharedFieldContent'},
            'cached_transliteration_without_markup': ('django.db.models.fields.CharField', [], {'max_length': '1000', 'blank': 'True'}),
            'content': ('django.db.models.fields.CharField', [], {'max_length': '1000', 'blank': 'True'}),
            'fact': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flashcards.SharedFact']"}),
            'field_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flashcards.FieldType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'media_file': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'media_uri': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'})
        },
        'flashcards.textbook': {
            'Meta': {'object_name': 'Textbook'},
            'cover_picture': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'max_length': '2000', 'blank': 'True'}),
            'edition': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'isbn': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'purchase_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'})
        },
        'flashcards.undocardreview': {
            'Meta': {'object_name': 'UndoCardReview'},
            'card': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flashcards.Card']"}),
            'card_history': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flashcards.CardHistory']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'pickled_card': ('picklefield.fields.PickledObjectField', [], {}),
            'pickled_review_stats': ('picklefield.fields.PickledObjectField', [], {}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        }
    }
    
    complete_apps = ['flashcards']
