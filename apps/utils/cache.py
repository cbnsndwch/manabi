from django.core.cache import cache
from django.http import HttpRequest
import hashlib
from functools import wraps
import re

# A memcached limit.
MAX_KEY_LENGTH = 250

_CONTROL_KEY_RE = re.compile(r'[ ' + ''.join(chr(i) for i in xrange(31)) + ']')

def _format_key_arg(arg):
    '''
    Selectively formats args passed to `make_key`. Defaults to serializing in UTF-8.
    '''
    def to_string(x):
        return unicode(x).encode('utf8')

    if isinstance(arg, dict):
        # `str` is wasteful for dicts, for our case here.
        s = ','.join([to_string(key) + ':' + to_string(val)
                      for key,val in arg.items()])
    else:
        s = to_string(arg)

    # Strip control characters and spaces (which memcached won't allow).
    return _CONTROL_KEY_RE.sub('', s)

def make_key(*args):
    '''
    This does several things to cleanly make a key out of the given arguments:
        1. Removes any spaces (which are illegal in memcached) and control characters.
        2. If the resulting length is > 250 bytes, generates a hash out of the key
           instead, disregarding any unhashable arguments.
    
    It's possible the resulting key would be empty. In that case, supply your own key,
    or don't cache that value. Choose args that won't result in an empty key.

    TODO a further refinemine of this would be to hash only the smallest part necessary
    to get it under the limit. Don't hash an entire key just for being 1 char too long.
    '''
    key = '.'.join(map(_format_key_arg, args))

    # If our key is too long, hash the part after the prefix, and truncate as needed.
    if len(cache.make_key(key)) > MAX_KEY_LENGTH:
        prefix = cache.make_key('')
        
        # Just to be safe...
        if len(prefix) > MAX_KEY_LENGTH:
            raise Exception('Your cache key prefixes are too long.')

        key = hashlib.sha512(key).hexdigest()[:MAX_KEY_LENGTH - len(prefix)]

    return key



def _assemble_keys(func, *args, **kwargs):
    '''
    Add a bunch of hopefully uniquely identifying parameters to a list to be passed to
    `make_key`.
    '''
    keys = ['cached_func']
    keys.append(func.__name__)
            
    # This works on both functions and class methods.
    if hasattr(func, '__self__'):
        # Method.
        self = args[0]
        keys.append(self.__class__.__name__)
        if hasattr(self, 'pk'):
            keys.append(self.pk)
        keys.extend(args[1:])
    else:
        # Function.
        keys.extend(args)

    keys.extend(kwargs.values())



def cached_function(func, keys=None):
    '''
    Adds a kwarg to the function, `invalidate_cache`. This allows the function to 
    setup signal listeners for invalidating the cache.

    Also works on class methods.

    '''
    @wraps(func)
    def cached_func(*args, **kwargs):
        key = make_key(_assemble_keys(func, *args, **kwargs))

        def invalidate():
           delete(key)

        ret = cache.get(key)
        if ret is None:
            ret = func(*args, invalidate_cache=invalidate, **kwargs)
            cache.set(key, ret)
        return ret
    return cached_func


def cached_view(func, keys=None):
    '''
    Handles HttpRequest object args intelligently when auto-generating the cache key.

    Only caches GET requests.
    '''
    @wraps(func)
    def wrapped(request, *args, **kwargs):
        # Don't cache non-GET requests.
        if request.method != 'GET':
            return func(request, *args, **kwargs)

        # Don't naively add the `request` arg to the cache key.
        keys = _assemble_keys(*args, **kwargs)
        
        # Only add parts of the `request` object to the key.
        keys.extend(request.GET)

        return cached_function(func)(request, *args, **kwargs)




