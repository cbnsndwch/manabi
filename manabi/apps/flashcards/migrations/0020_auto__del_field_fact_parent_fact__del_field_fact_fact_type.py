# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'Fact.parent_fact'
        db.delete_column(u'flashcards_fact', 'parent_fact_id')

        # Deleting field 'Fact.fact_type'
        db.delete_column(u'flashcards_fact', 'fact_type_id')


    def backwards(self, orm):
        # Adding field 'Fact.parent_fact'
        db.add_column(u'flashcards_fact', 'parent_fact',
                      self.gf('django.db.models.fields.related.ForeignKey')(related_name='child_facts', null=True, to=orm['flashcards.Fact'], blank=True),
                      keep_default=False)


        # User chose to not deal with backwards NULL issues for 'Fact.fact_type'
        raise RuntimeError("Cannot reverse this migration. 'Fact.fact_type' and its values cannot be restored.")
        
        # The following code is provided here to aid in writing a correct migration        # Adding field 'Fact.fact_type'
        db.add_column(u'flashcards_fact', 'fact_type',
                      self.gf('django.db.models.fields.related.ForeignKey')(to=orm['flashcards.FactType']),
                      keep_default=False)


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'flashcards.card': {
            'Meta': {'unique_together': "(('fact', 'template'),)", 'object_name': 'Card'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True'}),
            'due_at': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'ease_factor': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'fact': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flashcards.Fact']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'interval': ('django.db.models.fields.FloatField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'last_due_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'last_ease_factor': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'last_failed_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'last_interval': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'last_review_grade': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'last_reviewed_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'leech': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'new_card_ordinal': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'priority': ('django.db.models.fields.IntegerField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            'review_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'suspended': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'template': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flashcards.CardTemplate']"})
        },
        'flashcards.cardhistory': {
            'Meta': {'object_name': 'CardHistory'},
            'card': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flashcards.Card']"}),
            'duration': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'ease_factor': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'interval': ('django.db.models.fields.FloatField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'question_duration': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'response': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'reviewed_at': ('django.db.models.fields.DateTimeField', [], {}),
            'was_new': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'})
        },
        'flashcards.cardtemplate': {
            'Meta': {'ordering': "['ordinal']", 'unique_together': "(('name', 'fact_type'), ('ordinal', 'fact_type'))", 'object_name': 'CardTemplate'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'allow_blank_back': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'back_prompt': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'back_template_name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'card_synchronization_group': ('django.db.models.fields.SmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'max_length': '200', 'blank': 'True'}),
            'fact_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flashcards.FactType']"}),
            'front_prompt': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'front_template_name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'generate_by_default': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'hide_front': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'js_template': ('django.db.models.fields.TextField', [], {'max_length': '600', 'blank': 'True'}),
            'modified_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'ordinal': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'requisite_field_types': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['flashcards.FieldType']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'flashcards.deck': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Deck'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'max_length': '2000', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
            'picture': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'priority': ('django.db.models.fields.IntegerField', [], {'default': '0', 'blank': 'True'}),
            'shared': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'shared_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'suspended': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'synchronized_with': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'subscriber_decks'", 'null': 'True', 'to': "orm['flashcards.Deck']"}),
            'textbook_source': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flashcards.Textbook']", 'null': 'True', 'blank': 'True'})
        },
        'flashcards.fact': {
            'Meta': {'unique_together': "(('deck', 'synchronized_with'),)", 'object_name': 'Fact'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'deck': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flashcards.Deck']", 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'new_fact_ordinal': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'notes': ('django.db.models.fields.CharField', [], {'max_length': '1000', 'blank': 'True'}),
            'priority': ('django.db.models.fields.IntegerField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            'synchronized_with': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'subscriber_facts'", 'null': 'True', 'to': "orm['flashcards.Fact']"})
        },
        'flashcards.facttype': {
            'Meta': {'object_name': 'FactType'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'many_children_per_fact': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'modified_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'parent_fact_type': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'child_fact_types'", 'null': 'True', 'to': "orm['flashcards.FactType']"}),
            'space_factor': ('django.db.models.fields.FloatField', [], {'default': '0.1'})
        },
        'flashcards.fieldcontent': {
            'Meta': {'object_name': 'FieldContent'},
            'cached_transliteration_without_markup': ('django.db.models.fields.CharField', [], {'max_length': '1000', 'blank': 'True'}),
            'content': ('django.db.models.fields.CharField', [], {'max_length': '1000', 'blank': 'True'}),
            'fact': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flashcards.Fact']"}),
            'field_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flashcards.FieldType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'media_file': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'media_uri': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'})
        },
        'flashcards.fieldtype': {
            'Meta': {'unique_together': "(('name', 'fact_type'), ('ordinal', 'fact_type'), ('display_name', 'fact_type'))", 'object_name': 'FieldType'},
            'accepts_media': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'blank': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'character_restriction': ('django.db.models.fields.CharField', [], {'max_length': '3', 'null': 'True', 'blank': 'True'}),
            'choices': ('django.db.models.fields.CharField', [], {'max_length': '1000', 'blank': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'disabled_in_form': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'display_name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'editable': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'fact_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flashcards.FactType']"}),
            'grid_column_width': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'}),
            'help_text': ('django.db.models.fields.CharField', [], {'max_length': '500', 'blank': 'True'}),
            'hidden_in_form': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'hidden_in_grid': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'max_length': '3', 'null': 'True', 'blank': 'True'}),
            'media_restriction': ('django.db.models.fields.CharField', [], {'max_length': '3', 'null': 'True', 'blank': 'True'}),
            'modified_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'multi_line': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'numeric': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'ordinal': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'transliteration_field_type': ('django.db.models.fields.related.OneToOneField', [], {'blank': 'True', 'related_name': "'reverse_transliteration_field_type'", 'unique': 'True', 'null': 'True', 'to': "orm['flashcards.FieldType']"}),
            'unique': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        'flashcards.textbook': {
            'Meta': {'object_name': 'Textbook'},
            'custom_title': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'isbn': ('django.db.models.fields.CharField', [], {'max_length': '13'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'blank': 'True'})
        },
        'flashcards.undocardreview': {
            'Meta': {'object_name': 'UndoCardReview'},
            'card': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flashcards.Card']"}),
            'card_history': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flashcards.CardHistory']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'pickled_card': ('picklefield.fields.PickledObjectField', [], {}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"})
        }
    }

    complete_apps = ['flashcards']