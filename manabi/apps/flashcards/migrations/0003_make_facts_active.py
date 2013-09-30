# encoding: utf-8
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models

class Migration(DataMigration):
    
    def forwards(self, orm):
        "Write your forwards methods here."
        # the active field on facts was not used until the 0002 migration, even though it existed before
        for fact in orm.Fact.objects.all():
            fact.active = True
            fact.save()
    
    
    def backwards(self, orm):
        "Write your backwards methods here."
        raise RuntimeError("Cannot reverse this migration.")

    
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
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'max_length': '2000', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'picture': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'priority': ('django.db.models.fields.IntegerField', [], {'default': '0', 'blank': 'True'}),
            'shared': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'shared_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'synchronized_with': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'subscriber_decks'", 'null': 'True', 'to': "orm['flashcards.Deck']"}),
            'textbook_source': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flashcards.Textbook']", 'null': 'True', 'blank': 'True'})
        },
        'flashcards.fact': {
            'Meta': {'unique_together': "(('deck', 'synchronized_with'),)", 'object_name': 'Fact'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'deck': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flashcards.Deck']", 'null': 'True', 'blank': 'True'}),
            'fact_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flashcards.FactType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'new_fact_ordinal': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'notes': ('django.db.models.fields.CharField', [], {'max_length': '1000', 'blank': 'True'}),
            'parent_fact': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'child_facts'", 'null': 'True', 'to': "orm['flashcards.Fact']"}),
            'priority': ('django.db.models.fields.IntegerField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            'synchronized_with': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'subscriber_facts'", 'null': 'True', 'to': "orm['flashcards.Fact']"})
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
            'disabled_in_form': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
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
            'transliteration_field_type': ('django.db.models.fields.related.OneToOneField', [], {'blank': 'True', 'related_name': "'reverse_transliteration_field_type'", 'unique': 'True', 'null': 'True', 'to': "orm['flashcards.FieldType']"}),
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
