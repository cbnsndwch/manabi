import datetime

from django.contrib.auth.models import User
from django.contrib.postgres.fields import JSONField
from django.db import (
    models,
    transaction,
)


def _get_model_fields(model_instance, excluded_field_types=['AutoField', 'ForeignKey']):
    field_names = []
    for field in model_instance._meta.fields:
        if field.get_internal_type() in excluded_field_types:
            continue
        field_names.append(field.name)
    return field_names


class UndoCardReviewManager(models.Manager):
    def of_user(self, user):
        undos = self.filter(user=user)
        return undos

    def _last_undo(self, user):
        '''
        Returns the last undo for `user`.
        '''
        try:
            last_undo = self.of_user(user).order_by('timestamp')[0]
        except IndexError:
            return None
        return last_undo

    @transaction.atomic
    def reset(self, user):
        '''
        Clears the Undo stack for `user`.
        '''
        self.of_user(user).delete()

    @transaction.atomic
    def add_undo(self, card_history):
        '''
        Only keeps 1 level undo for now, to simplify things.
        '''
        user = card_history.card.fact.deck.owner

        snapshot = {
            getattr(card_history.card, field_name)
            for field_name in _get_model_fields(card_history.card)
        }

        undo = UndoCardReview(
            user = user,
            card = card_history.card,
            card_history = card_history,
            card_snapshot = list(snapshot),
        )

        # Delete previous undo if it exists.
        for user_undo in self.of_user(user):
            user_undo.delete()

        undo.save()

    @transaction.atomic
    def undo(self, user):
        '''
        Undoes the last review for `user`.

        Returns the undone review's card, or None if there wasn't
        anything in the undo stack.
        '''
        last_undo = self._last_undo(user)
        if not last_undo:
            return

        card = last_undo.card
        card_history = last_undo.card_history

        # Overwrite the card model with its pickled counterpart
        for field_name in _get_model_fields(card):
            try:
                setattr(card, field_name, last_undo.card_snapshot[field_name])
            except KeyError:
                continue
        card.save()

        card_history.delete()

        # Delete this undo now that it's done
        last_undo.delete()

        return card


class UndoCardReview(models.Model):
    objects = UndoCardReviewManager()

    timestamp = models.DateTimeField(auto_now_add=True, editable=False)
    user = models.ForeignKey(User)  # Denormalization optimization
    card = models.ForeignKey('Card')
    card_history = models.ForeignKey('CardHistory')

    card_snapshot = JSONField()

    class Meta:
        app_label = 'flashcards'
