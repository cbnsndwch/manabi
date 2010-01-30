from django.db import models
from django.contrib.auth.models import User
from picklefield import PickledObjectField
import datetime
from django.db import transaction

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
        '''Returns the last undo for `user`.'''
        try:
            last_undo = self.of_user(user).order_by('timestamp')[0]
        except IndexError:
            return None
        return last_undo


    @transaction.commit_on_success    
    def reset(self, user):
        '''Clears the Undo stack for `user`.'''
        self.of_user(user).delete()


    @transaction.commit_on_success
    def add_undo(self, card_history):
        '''
        Only keeps 1 level undo for now, to simplify things.
        '''
        #FIXME review_stats pickle
        user = card_history.card.fact.deck.owner

        undo = UndoCardReview(
            user = user,
            card = card_history.card,
            card_history = card_history,
            pickled_card = card_history.card,
            pickled_review_stats = user.reviewstatistics)

        # Delete previous undo if it exists
        for user_undo in self.of_user(user):
            user_undo.delete()

        undo.save()


    @transaction.commit_on_success    
    def undo(self, user):
        '''
        Undoes the last review for `user`.
        Returns False if there wasn't anything in the undo stack,
        otherwise returns True.
        '''
        last_undo = self._last_undo(user)
        if not last_undo:
            return False
        card = last_undo.card
        review_stats = user.reviewstatistics
        card_history = last_undo.card_history
        undone_card = last_undo.pickled_card
        undone_review_stats = last_undo.pickled_review_stats
        
        # Overwrite the card model with its pickled counterpart
        for from_model, to_model in [(undone_card, card,), (undone_review_stats, review_stats,)]:
            for field_name in _get_model_fields(from_model):
                setattr(to_model, field_name, getattr(from_model, field_name))
            to_model.save()

        # Delete the card history item
        card_history.delete()

        # Delete this undo now that it's done
        last_undo.delete()
        return True


class UndoCardReview(models.Model):
    objects = UndoCardReviewManager()

    timestamp = models.DateTimeField(auto_now_add=True, editable=False)
    user = models.ForeignKey(User) # Denormalization optimization
    card = models.ForeignKey('Card')
    card_history = models.ForeignKey('CardHistory')
    pickled_card = PickledObjectField()
    pickled_review_stats = PickledObjectField()

    class Meta:
        app_label = 'flashcards'

    

