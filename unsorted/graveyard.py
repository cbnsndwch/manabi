# Contains some commented-out code I don't feel like deleting.
# Yea I have git... but I don't want to forget about this stuff.
# Consider them TODOs.

#TODO implement (remember to update UndoReview too)
# This can probably just be a proxy model for CardHistory or something.
#class CardStatistics(models.Model):
#    card = models.ForeignKey(Card)

#    failure_count = models.PositiveIntegerField(default=0, editable=False)
#    #TODO review stats depending on how card was rated, and how mature it is

#    #apparently needed for synchronization/import purposes
#    yes_count = models.PositiveIntegerField(default=0, editable=False)
#    no_count = models.PositiveIntegerField(default=0, editable=False)

#    average_thinking_time = models.PositiveIntegerField(null=True, editable=False)

#    #initial_ease 
    
#    successive_count = models.PositiveIntegerField(default=0, editable=False) #incremented at each success, zeroed at failure
#    successive_streak_count = models.PositiveIntegerField(default=0, editable=False) #incremented at each failure after a success
#    average_successive_count = models.PositiveIntegerField(default=0, editable=False) #

#    skip_count = models.PositiveIntegerField(default=0, editable=False)
#    total_review_time = models.FloatField(default=0) #s
#    first_reviewed_at = models.DateTimeField()
#    first_success_at = models.DateTimeField()
    
    
#    #these take into account short-term memory effects
#    #they ignore any more than a single review per day (or 8 hours - TBD)
#    #adjusted_review_count = models.PositiveIntegerField(default=0, editable=False)
#    #adjusted_success_count = models.PositiveIntegerField(default=0, editable=False)
#    #first_adjusted_success_at = models.DateTimeField()
#    #failures_in_a_row = models.PositiveIntegerField(default=0, editable=False)
#    #adjusted_failures_in_a_row = models.PositiveIntegerField(default=0, editable=False)

#    class Meta:
#        app_label = 'flashcards'

