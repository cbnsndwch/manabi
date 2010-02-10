
from south.db import db
from django.db import models
from usertagging.models import *

class Migration:
    
    def forwards(self, orm):
        
        # Adding model 'UserTaggedItem'
        db.create_table('usertagging_usertaggeditem', (
            ('id', orm['usertagging.UserTaggedItem:id']),
            ('tag', orm['usertagging.UserTaggedItem:tag']),
            ('content_type', orm['usertagging.UserTaggedItem:content_type']),
            ('object_id', orm['usertagging.UserTaggedItem:object_id']),
        ))
        db.send_create_signal('usertagging', ['UserTaggedItem'])
        
        # Adding model 'Tag'
        db.create_table('usertagging_tag', (
            ('id', orm['usertagging.Tag:id']),
            ('name', orm['usertagging.Tag:name']),
            ('owner', orm['usertagging.Tag:owner']),
        ))
        db.send_create_signal('usertagging', ['Tag'])
        
        # Creating unique_together for [name, owner] on Tag.
        db.create_unique('usertagging_tag', ['name', 'owner_id'])
        
        # Creating unique_together for [tag, content_type, object_id] on UserTaggedItem.
        db.create_unique('usertagging_usertaggeditem', ['tag_id', 'content_type_id', 'object_id'])
        
    
    
    def backwards(self, orm):
        
        # Deleting unique_together for [tag, content_type, object_id] on UserTaggedItem.
        db.delete_unique('usertagging_usertaggeditem', ['tag_id', 'content_type_id', 'object_id'])
        
        # Deleting unique_together for [name, owner] on Tag.
        db.delete_unique('usertagging_tag', ['name', 'owner_id'])
        
        # Deleting model 'UserTaggedItem'
        db.delete_table('usertagging_usertaggeditem')
        
        # Deleting model 'Tag'
        db.delete_table('usertagging_tag')
        
    
    
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
        'usertagging.tag': {
            'Meta': {'unique_together': "(('name', 'owner'),)"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'db_index': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'})
        },
        'usertagging.usertaggeditem': {
            'Meta': {'unique_together': "(('tag', 'content_type', 'object_id'),)"},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'tag': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'items'", 'to': "orm['usertagging.Tag']"})
        }
    }
    
    complete_apps = ['usertagging']
