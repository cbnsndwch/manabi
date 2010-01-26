from django.db import models
from django.contrib.auth.models import User

from django.db import transaction
import datetime, time
from timezones.utils import adjust_datetime_to_timezone
from account.models import Account

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


    #TODO refactor into a custom model field
    def get_new_reviews_today(self):
        if not self._is_review_time_within_users_day(self.last_new_review_at):
            self.new_reviews_today = 0
        return self.new_reviews_today


    #TODO refactor into a custom model field
    def get_failed_reviews_today(self):
        if not self._is_review_time_within_users_day(self.last_failed_review_at):
            self.failed_reviews_today = 0
        return self.failed_reviews_today


    def _is_review_time_within_users_day(self, reviewed_at):
        'Returns whether `reviewed_at` (a datetime in UTC) is within the current study day for the user'
        user_timezone = Account.objects.get(user=self.user).timezone
        now = datetime.datetime.utcnow()
        user_now = adjust_datetime_to_timezone(now, from_tz='UTC', to_tz=user_timezone)
        user_eod = adjust_datetime_to_timezone(datetime.datetime.combine(user_now.date(), end_of_day), from_tz='UTC', to_tz='UTC')
        if (user_now.time() >= end_of_day):
            user_eod += datetime.timedelta(days=1)
        user_reviewed_at = adjust_datetime_to_timezone(reviewed_at, from_tz='UTC', to_tz=user_timezone)
        return user_eod - datetime.timedelta(days=1) < user_reviewed_at
        

    #TODO refactor for DRY
    def increment_new_reviews(self):
        now = datetime.datetime.utcnow()
        if now.time() >= end_of_day and self.last_new_review_at and self.last_new_review_at.time() < end_of_day:
            self.new_reviews_today = 1
        else:
            self.new_reviews_today += 1
        self.last_new_review_at = now

    def increment_failed_reviews(self):
        now = datetime.datetime.utcnow()
        if now.time() >= end_of_day and self.last_failed_review_at and self.last_failed_review_at.time() < end_of_day:
            self.failed_reviews_today = 1
        else:
            self.failed_reviews_today += 1
        self.last_failed_review_at = now

    class Meta:
        app_label = 'flashcards'

    def __unicode__(self):
        return self.user.__unicode__()
