from django_rq import job

from manabi.apps.twitter_usages import harvest


@job
def harvest_tweets(fact):
    harvest.harvest_tweets(fact)
