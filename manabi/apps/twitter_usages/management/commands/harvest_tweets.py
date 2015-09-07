from django.core.management.base import BaseCommand, CommandError

from manabi.apps.twitter_usages.harvest import harvest_tweets


class Command(BaseCommand):
    help = ''

    def add_arguments(self, parser):
        pass
        #parser.add_argument('poll_id', nargs='+', type=int)

    def handle(self, *args, **options):
        count = 300 # of 19141
        self.stdout.write("Harvesting up to {} facts' tweets.".format(count))

        harvest_tweets(count)
