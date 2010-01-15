from django.db import models
from django.contrib.auth.models import User

from django.db import transaction
import datetime

end_of_day = datetime.time(5) #5:00am

class ReviewStatistics(models.Model):
    '''
    Some stats per user. Notably, tracks the number of new cards
    reviewed each day, so that it can be limited.
    '''
    user = models.OneToOneField(User)

    new_reviews_today = models.PositiveIntegerField(default=0, editable=False)
    last_new_review_at = models.DateTimeField(blank=True, null=True) #use this to know when to reset new_reviews_today

    failed_reviews_today = models.PositiveIntegerField(default=0, editable=False)
    last_failed_review_at = models.DateTimeField(blank=True, null=True)

    #TODO refactor for DRY
    def increment_new_reviews(self):
        now = datetime.datetime.utcnow()
        if now.time() >= end_of_day and last_new_review_at.time() < end_of_day:
            self.new_reviews_today = 1
        else:
            self.new_reviews_today += 1
        self.last_new_review_at = now

    def increment_failed_reviews(self):
        now = datetime.datetime.utcnow()
        if now.time() >= end_of_day and last_failed_review_at.time() < end_of_day:
            self.failed_reviews_today = 1
        else:
            self.failed_reviews_today += 1
        self.last_failed_review_at = now

    class Meta:
        app_label = 'flashcards'

    def __unicode__(self):
        return self.user.__unicode__()
