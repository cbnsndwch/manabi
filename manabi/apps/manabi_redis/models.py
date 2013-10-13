from redis import StrictRedis

from django.conf import settings


class ManabiRedis(StrictRedis):
    pass


redis = ManabiRedis(host=settings.REDIS['host'], port=settings.REDIS['port'], db=settings.REDIS['db'])

