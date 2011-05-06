import django.dispatch
from django.dispatch import receiver
from django.db.models.signals import post_save, m2m_changed, post_delete
from models.fields import FieldContent

fact_suspended = django.dispatch.Signal()
fact_unsuspended = django.dispatch.Signal()


# This signal is used to invalidate the cache on our fact grid views.
# `decks` is a list of decks this applies to.
fact_grid_updated = django.dispatch.Signal(providing_args=['decks'])


# Below are the listeners which will send `fact_grid_updated`.
@receiver(post_save,
          sender=FieldContent, dispatch_uid='fact_grid_updated_fc_ps')
@receiver(post_delete,
          sender=FieldContent, dispatch_uid='fact_grid_updated_fc_pd')
def field_content_updated(sender, instance, created, **kwargs):
    print 'field_content_updated listened'
    fact_grid_updated.send(sender=sender,
                           decks=instance.fact.all_owner_decks())

@receiver(fact_suspended, dispatch_uid='fact_grid_updated_f_s')
@receiver(fact_unsuspended, dispatch_uid='fact_grid_updated_f_us')
def fact_status_updated(sender, **kwargs):
    print 'fact_status_updated listened'
    fact_grid_updated.send(sender=sender,
                           decks=sender.all_owner_decks())


