from django.core.cache import cache
import hashlib
from functools import wraps

# A memcached limit.
MAX_KEY_LENGTH = 250

def make_key(*args):
    '''
    This does several things to cleanly make a key out of the given arguments:
        1. Removes any spaces (which are illegal in memcached) and control characters.
        2. If the resulting length is > 250 bytes, generates a hash out of the key instead,
           disregarding any unhashable arguments.
    
    It's possible the resulting key would be empty. In that case, supply your own key,
    or don't cache that value. Choose args that won't result in an empty key.

    TODO a further refinemine of this would be to hash only the smallest part necessary
    to get it under the limit. Don't hash an entire key just for being 1 char too long.
    '''
    keys = []
    for arg in args:
        keys.append(str(arg).replace(' ', ''))

    key = '.'.join(keys)

    # If our key is too long, hash the part after the prefix, and truncate as needed.
    if len(cache.make_key(key)) > MAX_KEY_LENGTH:
        prefix = cache.make_key('')
        
        # Just to be safe...
        if len(prefix) > MAX_KEY_LENGTH:
            raise Exception('Your cache key prefixes are too long.')

        key = hashlib.sha512(key).hexdigest()[:MAX_KEY_LENGTH - len(prefix)]

    return key





def cached_function(func, _decorates_method=False):
    '''
    Adds a kwarg to the function, `invalidate_cache`.
    '''
    @wraps(func)
    def cached_func(*args, **kwargs):
        # Add a bunch of hopefully uniquely identifying parameters to the key.
        keys = ['cached_func']
        keys.append(func.__name__)
                
        # For DRY - this works on both functions and methods.
        if _decorates_method:
            self = args[0]
            keys.append(self.__class__.__name__)
            if hasattr(self, 'pk'):
                keys.append(self.pk)
            keys.extend(args[1:])
        else:
            keys.extend(args)

        keys.extend(kwargs.values())
        key = make_key(*keys)

        def invalidate():
           delete(key)

        ret = cache.get(key)
        if ret is None:
            ret = func(*args, invalidate_cache=invalidate, **kwargs)
            cache.set(key, ret)
        return ret
    return cached_func

def cached_method(*args, **kwargs):
    return cached_function(*args, _decorates_method=True, **kwargs)


