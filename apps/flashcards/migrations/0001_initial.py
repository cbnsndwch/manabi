
from south.db import db
from django.db import models
from flashcards.models import *

class Migration:
    
    def forwards(self, orm):
        
        # Adding model 'Textbook'
        db.create_table('flashcards_textbook', (
            ('id', orm['flashcards.Textbook:id']),
            ('name', orm['flashcards.Textbook:name']),
            ('edition', orm['flashcards.Textbook:edition']),
            ('description', orm['flashcards.Textbook:description']),
            ('purchase_url', orm['flashcards.Textbook:purchase_url']),
            ('isbn', orm['flashcards.Textbook:isbn']),
            ('cover_picture', orm['flashcards.Textbook:cover_picture']),
        ))
        db.send_create_signal('flashcards', ['Textbook'])
        
        # Adding model 'SharedFact'
        db.create_table('flashcards_sharedfact', (
            ('id', orm['flashcards.SharedFact:id']),
            ('fact_type', orm['flashcards.SharedFact:fact_type']),
            ('active', orm['flashcards.SharedFact:active']),
            ('priority', orm['flashcards.SharedFact:priority']),
            ('notes', orm['flashcards.SharedFact:notes']),
            ('created_at', orm['flashcards.SharedFact:created_at']),
            ('modified_at', orm['flashcards.SharedFact:modified_at']),
            ('deck', orm['flashcards.SharedFact:deck']),
            ('parent_fact', orm['flashcards.SharedFact:parent_fact']),
        ))
        db.send_create_signal('flashcards', ['SharedFact'])
        
        # Adding model 'FieldContent'
        db.create_table('flashcards_fieldcontent', (
            ('id', orm['flashcards.FieldContent:id']),
            ('field_type', orm['flashcards.FieldContent:field_type']),
            ('content', orm['flashcards.FieldContent:content']),
            ('media_uri', orm['flashcards.FieldContent:media_uri']),
            ('media_file', orm['flashcards.FieldContent:media_file']),
            ('cached_transliteration_without_markup', orm['flashcards.FieldContent:cached_transliteration_without_markup']),
            ('fact', orm['flashcards.FieldContent:fact']),
        ))
        db.send_create_signal('flashcards', ['FieldContent'])
        
        # Adding model 'ReviewStatistics'
        db.create_table('flashcards_reviewstatistics', (
            ('id', orm['flashcards.ReviewStatistics:id']),
            ('user', orm['flashcards.ReviewStatistics:user']),
            ('new_reviews_today', orm['flashcards.ReviewStatistics:new_reviews_today']),
            ('last_new_review_at', orm['flashcards.ReviewStatistics:last_new_review_at']),
            ('failed_reviews_today', orm['flashcards.ReviewStatistics:failed_reviews_today']),
            ('last_failed_review_at', orm['flashcards.ReviewStatistics:last_failed_review_at']),
        ))
        db.send_create_signal('flashcards', ['ReviewStatistics'])
        
        # Adding model 'CardHistory'
        db.create_table('flashcards_cardhistory', (
            ('id', orm['flashcards.CardHistory:id']),
            ('card', orm['flashcards.CardHistory:card']),
            ('response', orm['flashcards.CardHistory:response']),
            ('reviewed_at', orm['flashcards.CardHistory:reviewed_at']),
        ))
        db.send_create_signal('flashcards', ['CardHistory'])
        
        # Adding model 'SharedDeck'
        db.create_table('flashcards_shareddeck', (
            ('id', orm['flashcards.SharedDeck:id']),
            ('name', orm['flashcards.SharedDeck:name']),
            ('description', orm['flashcards.SharedDeck:description']),
            ('owner', orm['flashcards.SharedDeck:owner']),
            ('textbook_source', orm['flashcards.SharedDeck:textbook_source']),
            ('picture', orm['flashcards.SharedDeck:picture']),
            ('priority', orm['flashcards.SharedDeck:priority']),
            ('created_at', orm['flashcards.SharedDeck:created_at']),
            ('modified_at', orm['flashcards.SharedDeck:modified_at']),
            ('downloads', orm['flashcards.SharedDeck:downloads']),
        ))
        db.send_create_signal('flashcards', ['SharedDeck'])
        
        # Adding model 'CardStatistics'
        db.create_table('flashcards_cardstatistics', (
            ('id', orm['flashcards.CardStatistics:id']),
            ('card', orm['flashcards.CardStatistics:card']),
            ('failure_count', orm['flashcards.CardStatistics:failure_count']),
            ('yes_count', orm['flashcards.CardStatistics:yes_count']),
            ('no_count', orm['flashcards.CardStatistics:no_count']),
            ('average_thinking_time', orm['flashcards.CardStatistics:average_thinking_time']),
            ('successive_count', orm['flashcards.CardStatistics:successive_count']),
            ('successive_streak_count', orm['flashcards.CardStatistics:successive_streak_count']),
            ('average_successive_count', orm['flashcards.CardStatistics:average_successive_count']),
            ('skip_count', orm['flashcards.CardStatistics:skip_count']),
            ('total_review_time', orm['flashcards.CardStatistics:total_review_time']),
            ('first_reviewed_at', orm['flashcards.CardStatistics:first_reviewed_at']),
            ('first_success_at', orm['flashcards.CardStatistics:first_success_at']),
        ))
        db.send_create_signal('flashcards', ['CardStatistics'])
        
        # Adding model 'Deck'
        db.create_table('flashcards_deck', (
            ('id', orm['flashcards.Deck:id']),
            ('name', orm['flashcards.Deck:name']),
            ('description', orm['flashcards.Deck:description']),
            ('owner', orm['flashcards.Deck:owner']),
            ('textbook_source', orm['flashcards.Deck:textbook_source']),
            ('picture', orm['flashcards.Deck:picture']),
            ('priority', orm['flashcards.Deck:priority']),
            ('created_at', orm['flashcards.Deck:created_at']),
            ('modified_at', orm['flashcards.Deck:modified_at']),
        ))
        db.send_create_signal('flashcards', ['Deck'])
        
        # Adding model 'FieldType'
        db.create_table('flashcards_fieldtype', (
            ('id', orm['flashcards.FieldType:id']),
            ('name', orm['flashcards.FieldType:name']),
            ('fact_type', orm['flashcards.FieldType:fact_type']),
            ('transliteration_field_type', orm['flashcards.FieldType:transliteration_field_type']),
            ('unique', orm['flashcards.FieldType:unique']),
            ('blank', orm['flashcards.FieldType:blank']),
            ('editable', orm['flashcards.FieldType:editable']),
            ('numeric', orm['flashcards.FieldType:numeric']),
            ('multi_line', orm['flashcards.FieldType:multi_line']),
            ('choices', orm['flashcards.FieldType:choices']),
            ('help_text', orm['flashcards.FieldType:help_text']),
            ('language', orm['flashcards.FieldType:language']),
            ('character_restriction', orm['flashcards.FieldType:character_restriction']),
            ('accepts_media', orm['flashcards.FieldType:accepts_media']),
            ('media_restriction', orm['flashcards.FieldType:media_restriction']),
            ('hidden_in_form', orm['flashcards.FieldType:hidden_in_form']),
            ('hidden_in_grid', orm['flashcards.FieldType:hidden_in_grid']),
            ('grid_column_width', orm['flashcards.FieldType:grid_column_width']),
            ('ordinal', orm['flashcards.FieldType:ordinal']),
            ('active', orm['flashcards.FieldType:active']),
            ('created_at', orm['flashcards.FieldType:created_at']),
            ('modified_at', orm['flashcards.FieldType:modified_at']),
        ))
        db.send_create_signal('flashcards', ['FieldType'])
        
        # Adding model 'SharedFieldContent'
        db.create_table('flashcards_sharedfieldcontent', (
            ('id', orm['flashcards.SharedFieldContent:id']),
            ('field_type', orm['flashcards.SharedFieldContent:field_type']),
            ('content', orm['flashcards.SharedFieldContent:content']),
            ('media_uri', orm['flashcards.SharedFieldContent:media_uri']),
            ('media_file', orm['flashcards.SharedFieldContent:media_file']),
            ('cached_transliteration_without_markup', orm['flashcards.SharedFieldContent:cached_transliteration_without_markup']),
            ('fact', orm['flashcards.SharedFieldContent:fact']),
        ))
        db.send_create_signal('flashcards', ['SharedFieldContent'])
        
        # Adding model 'UndoCardReview'
        db.create_table('flashcards_undocardreview', (
            ('id', orm['flashcards.UndoCardReview:id']),
            ('timestamp', orm['flashcards.UndoCardReview:timestamp']),
            ('user', orm['flashcards.UndoCardReview:user']),
            ('card', orm['flashcards.UndoCardReview:card']),
            ('card_history', orm['flashcards.UndoCardReview:card_history']),
            ('pickled_card', orm['flashcards.UndoCardReview:pickled_card']),
            ('pickled_review_stats', orm['flashcards.UndoCardReview:pickled_review_stats']),
        ))
        db.send_create_signal('flashcards', ['UndoCardReview'])
        
        # Adding model 'CardTemplate'
        db.create_table('flashcards_cardtemplate', (
            ('id', orm['flashcards.CardTemplate:id']),
            ('fact_type', orm['flashcards.CardTemplate:fact_type']),
            ('name', orm['flashcards.CardTemplate:name']),
            ('description', orm['flashcards.CardTemplate:description']),
            ('front_template_name', orm['flashcards.CardTemplate:front_template_name']),
            ('back_template_name', orm['flashcards.CardTemplate:back_template_name']),
            ('front_prompt', orm['flashcards.CardTemplate:front_prompt']),
            ('back_prompt', orm['flashcards.CardTemplate:back_prompt']),
            ('card_synchronization_group', orm['flashcards.CardTemplate:card_synchronization_group']),
            ('generate_by_default', orm['flashcards.CardTemplate:generate_by_default']),
            ('ordinal', orm['flashcards.CardTemplate:ordinal']),
            ('hide_front', orm['flashcards.CardTemplate:hide_front']),
            ('allow_blank_back', orm['flashcards.CardTemplate:allow_blank_back']),
            ('active', orm['flashcards.CardTemplate:active']),
            ('created_at', orm['flashcards.CardTemplate:created_at']),
            ('modified_at', orm['flashcards.CardTemplate:modified_at']),
        ))
        db.send_create_signal('flashcards', ['CardTemplate'])
        
        # Adding model 'Fact'
        db.create_table('flashcards_fact', (
            ('id', orm['flashcards.Fact:id']),
            ('fact_type', orm['flashcards.Fact:fact_type']),
            ('active', orm['flashcards.Fact:active']),
            ('priority', orm['flashcards.Fact:priority']),
            ('notes', orm['flashcards.Fact:notes']),
            ('created_at', orm['flashcards.Fact:created_at']),
            ('modified_at', orm['flashcards.Fact:modified_at']),
            ('deck', orm['flashcards.Fact:deck']),
            ('parent_fact', orm['flashcards.Fact:parent_fact']),
        ))
        db.send_create_signal('flashcards', ['Fact'])
        
        # Adding model 'SharedCard'
        db.create_table('flashcards_sharedcard', (
            ('id', orm['flashcards.SharedCard:id']),
            ('template', orm['flashcards.SharedCard:template']),
            ('priority', orm['flashcards.SharedCard:priority']),
            ('leech', orm['flashcards.SharedCard:leech']),
            ('active', orm['flashcards.SharedCard:active']),
            ('suspended', orm['flashcards.SharedCard:suspended']),
            ('new_card_ordinal', orm['flashcards.SharedCard:new_card_ordinal']),
            ('fact', orm['flashcards.SharedCard:fact']),
        ))
        db.send_create_signal('flashcards', ['SharedCard'])
        
        # Adding model 'Card'
        db.create_table('flashcards_card', (
            ('id', orm['flashcards.Card:id']),
            ('template', orm['flashcards.Card:template']),
            ('priority', orm['flashcards.Card:priority']),
            ('leech', orm['flashcards.Card:leech']),
            ('active', orm['flashcards.Card:active']),
            ('suspended', orm['flashcards.Card:suspended']),
            ('new_card_ordinal', orm['flashcards.Card:new_card_ordinal']),
            ('fact', orm['flashcards.Card:fact']),
            ('synchronized_with', orm['flashcards.Card:synchronized_with']),
            ('ease_factor', orm['flashcards.Card:ease_factor']),
            ('interval', orm['flashcards.Card:interval']),
            ('due_at', orm['flashcards.Card:due_at']),
            ('last_ease_factor', orm['flashcards.Card:last_ease_factor']),
            ('last_interval', orm['flashcards.Card:last_interval']),
            ('last_due_at', orm['flashcards.Card:last_due_at']),
            ('last_reviewed_at', orm['flashcards.Card:last_reviewed_at']),
            ('last_review_grade', orm['flashcards.Card:last_review_grade']),
            ('last_failed_at', orm['flashcards.Card:last_failed_at']),
            ('review_count', orm['flashcards.Card:review_count']),
        ))
        db.send_create_signal('flashcards', ['Card'])
        
        # Adding model 'FactType'
        db.create_table('flashcards_facttype', (
            ('id', orm['flashcards.FactType:id']),
            ('name', orm['flashcards.FactType:name']),
            ('active', orm['flashcards.FactType:active']),
            ('parent_fact_type', orm['flashcards.FactType:parent_fact_type']),
            ('many_children_per_fact', orm['flashcards.FactType:many_children_per_fact']),
            ('min_card_space', orm['flashcards.FactType:min_card_space']),
            ('space_factor', orm['flashcards.FactType:space_factor']),
            ('created_at', orm['flashcards.FactType:created_at']),
            ('modified_at', orm['flashcards.FactType:modified_at']),
        ))
        db.send_create_signal('flashcards', ['FactType'])
        
        # Adding model 'SchedulingOptions'
        db.create_table('flashcards_schedulingoptions', (
            ('id', orm['flashcards.SchedulingOptions:id']),
            ('deck', orm['flashcards.SchedulingOptions:deck']),
            ('mature_unknown_interval_min', orm['flashcards.SchedulingOptions:mature_unknown_interval_min']),
            ('mature_unknown_interval_max', orm['flashcards.SchedulingOptions:mature_unknown_interval_max']),
            ('unknown_interval_min', orm['flashcards.SchedulingOptions:unknown_interval_min']),
            ('unknown_interval_max', orm['flashcards.SchedulingOptions:unknown_interval_max']),
            ('hard_interval_min', orm['flashcards.SchedulingOptions:hard_interval_min']),
            ('hard_interval_max', orm['flashcards.SchedulingOptions:hard_interval_max']),
            ('medium_interval_min', orm['flashcards.SchedulingOptions:medium_interval_min']),
            ('medium_interval_max', orm['flashcards.SchedulingOptions:medium_interval_max']),
            ('easy_interval_min', orm['flashcards.SchedulingOptions:easy_interval_min']),
            ('easy_interval_max', orm['flashcards.SchedulingOptions:easy_interval_max']),
        ))
        db.send_create_signal('flashcards', ['SchedulingOptions'])
        
        # Adding ManyToManyField 'CardTemplate.requisite_field_types'
        db.create_table('flashcards_cardtemplate_requisite_field_types', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('cardtemplate', models.ForeignKey(orm.CardTemplate, null=False)),
            ('fieldtype', models.ForeignKey(orm.FieldType, null=False))
        ))
        
        # Creating unique_together for [fact, template] on Card.
        db.create_unique('flashcards_card', ['fact_id', 'template_id'])
        
        # Creating unique_together for [ordinal, fact_type] on CardTemplate.
        db.create_unique('flashcards_cardtemplate', ['ordinal', 'fact_type_id'])
        
        # Creating unique_together for [ordinal, fact_type] on FieldType.
        db.create_unique('flashcards_fieldtype', ['ordinal', 'fact_type_id'])
        
        # Creating unique_together for [name, fact_type] on FieldType.
        db.create_unique('flashcards_fieldtype', ['name', 'fact_type_id'])
        
        # Creating unique_together for [name, fact_type] on CardTemplate.
        db.create_unique('flashcards_cardtemplate', ['name', 'fact_type_id'])
        
        # Creating unique_together for [fact, template] on SharedCard.
        db.create_unique('flashcards_sharedcard', ['fact_id', 'template_id'])
        
    
    
    def backwards(self, orm):
        
        # Deleting unique_together for [fact, template] on SharedCard.
        db.delete_unique('flashcards_sharedcard', ['fact_id', 'template_id'])
        
        # Deleting unique_together for [name, fact_type] on CardTemplate.
        db.delete_unique('flashcards_cardtemplate', ['name', 'fact_type_id'])
        
        # Deleting unique_together for [name, fact_type] on FieldType.
        db.delete_unique('flashcards_fieldtype', ['name', 'fact_type_id'])
        
        # Deleting unique_together for [ordinal, fact_type] on FieldType.
        db.delete_unique('flashcards_fieldtype', ['ordinal', 'fact_type_id'])
        
        # Deleting unique_together for [ordinal, fact_type] on CardTemplate.
        db.delete_unique('flashcards_cardtemplate', ['ordinal', 'fact_type_id'])
        
        # Deleting unique_together for [fact, template] on Card.
        db.delete_unique('flashcards_card', ['fact_id', 'template_id'])
        
        # Deleting model 'Textbook'
        db.delete_table('flashcards_textbook')
        
        # Deleting model 'SharedFact'
        db.delete_table('flashcards_sharedfact')
        
        # Deleting model 'FieldContent'
        db.delete_table('flashcards_fieldcontent')
        
        # Deleting model 'ReviewStatistics'
        db.delete_table('flashcards_reviewstatistics')
        
        # Deleting model 'CardHistory'
        db.delete_table('flashcards_cardhistory')
        
        # Deleting model 'SharedDeck'
        db.delete_table('flashcards_shareddeck')
        
        # Deleting model 'CardStatistics'
        db.delete_table('flashcards_cardstatistics')
        
        # Deleting model 'Deck'
        db.delete_table('flashcards_deck')
        
        # Deleting model 'FieldType'
        db.delete_table('flashcards_fieldtype')
        
        # Deleting model 'SharedFieldContent'
        db.delete_table('flashcards_sharedfieldcontent')
        
        # Deleting model 'UndoCardReview'
        db.delete_table('flashcards_undocardreview')
        
        # Deleting model 'CardTemplate'
        db.delete_table('flashcards_cardtemplate')
        
        # Deleting model 'Fact'
        db.delete_table('flashcards_fact')
        
        # Deleting model 'SharedCard'
        db.delete_table('flashcards_sharedcard')
        
        # Deleting model 'Card'
        db.delete_table('flashcards_card')
        
        # Deleting model 'FactType'
        db.delete_table('flashcards_facttype')
        
        # Deleting model 'SchedulingOptions'
        db.delete_table('flashcards_schedulingoptions')
        
        # Dropping ManyToManyField 'CardTemplate.requisite_field_types'
        db.delete_table('flashcards_cardtemplate_requisite_field_types')
        
    
    
    models = {
        'auth.group': {
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'unique_together': "(('content_type', 'codename'),)"},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
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
            'Meta': {'unique_together': "(('app_label', 'model'),)", 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'flashcards.card': {
            'Meta': {'unique_together': "(('fact', 'template'),)"},
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
            'card': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flashcards.Card']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'response': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'reviewed_at': ('django.db.models.fields.DateTimeField', [], {})
        },
        'flashcards.cardstatistics': {
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
            'Meta': {'unique_together': "(('name', 'fact_type'), ('ordinal', 'fact_type'))"},
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
            'cached_transliteration_without_markup': ('django.db.models.fields.CharField', [], {'max_length': '1000', 'blank': 'True'}),
            'content': ('django.db.models.fields.CharField', [], {'max_length': '1000', 'blank': 'True'}),
            'fact': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flashcards.Fact']"}),
            'field_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flashcards.FieldType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'media_file': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'media_uri': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'})
        },
        'flashcards.fieldtype': {
            'Meta': {'unique_together': "(('name', 'fact_type'), ('ordinal', 'fact_type'))"},
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
            'failed_reviews_today': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_failed_review_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'last_new_review_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'new_reviews_today': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.User']", 'unique': 'True'})
        },
        'flashcards.schedulingoptions': {
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
            'Meta': {'unique_together': "(('fact', 'template'),)"},
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
            'cached_transliteration_without_markup': ('django.db.models.fields.CharField', [], {'max_length': '1000', 'blank': 'True'}),
            'content': ('django.db.models.fields.CharField', [], {'max_length': '1000', 'blank': 'True'}),
            'fact': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flashcards.SharedFact']"}),
            'field_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flashcards.FieldType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'media_file': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'media_uri': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'})
        },
        'flashcards.textbook': {
            'cover_picture': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'max_length': '2000', 'blank': 'True'}),
            'edition': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'isbn': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'purchase_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'})
        },
        'flashcards.undocardreview': {
            'card': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flashcards.Card']"}),
            'card_history': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['flashcards.CardHistory']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'pickled_card': ('PickledObjectField', [], {}),
            'pickled_review_stats': ('PickledObjectField', [], {}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        }
    }
    
    complete_apps = ['flashcards']
