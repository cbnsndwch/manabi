import rq
from django.conf import settings
from raven import Client
from rq.contrib.sentry import register_sentry


class ManabiWorker(rq.Worker):
    def __init__(self, *args, **kwargs):
        super(ManabiWorker, self).__init__(*args, **kwargs)

        dsn = settings.RAVEN_CONFIG['dsn']
        client = Client(dsn, tarnsport=HTTPTransport)
        register_sentry(client, self)
