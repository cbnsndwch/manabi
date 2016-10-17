from django.db.models.signals import post_save, post_delete, pre_delete
from django.dispatch import receiver

from manabi.apps.flashcards.models import Card


@receiver(post_save, sender=Card, dispatch_uid='card_saved_redis')
def card_saved(sender, instance, created, **kwargs):
    card = instance
    if not created:
        return
    # card.redis.update_deck()

@receiver(post_delete, sender=Card, dispatch_uid='card_deleted_redis')
def card_deleted(sender, card, **kwargs):
    # card.redis.delete()
    pass
