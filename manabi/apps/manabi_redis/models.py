from redis import StrictRedis

from settings import REDIS

class ManabiRedis(StrictRedis):
    pass

redis = ManabiRedis(host=REDIS['host'], port=REDIS['port'], db=REDIS['db'])

