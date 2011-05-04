from django.core.cache import cache
from django.http import HttpRequest
from functools import wraps
import hashlib
import re
import inspect
from itertools import chain

# A memcached limit.
MAX_KEY_LENGTH = 250

# Regex to match any control characters, plus space.
# (All of which are illegal in memcached keys.)
_CONTROL_KEY_RE = re.compile(r'[ ' + ''.join(chr(i) for i in xrange(31)) + ']')

def _format_key_arg(arg):
    '''
    Selectively formats args passed to `make_key`. Defaults to serializing
    into a string and then encoding in UTF-8.
    '''
    to_string = lambda x: unicode(x).encode('utf8')

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
    This does a couple things to cleanly make a key out of the given arguments:
        1. Removes any spaces (which are illegal in memcached) and control
           characters.
        2. After serializing all arguments and joining them into one string, if
           the resulting length is > 250 bytes, generates a hash out of the
           key instead.
    
    It's possible the resulting key would be empty. In that case, supply your 
    own key, or don't cache that value. Better yet, choose args that won't
    result in an empty key!

    TODO a further refinement of this would be to hash only the smallest part
    necessary to get it under the limit. Don't hash an entire key just for 
    being 1 char too long. This would improve readability.
    '''
    key = '.'.join(map(_format_key_arg, args))

    # If our key is too long, hash the part after the prefix,
    # and truncate as needed.
    if len(cache.make_key(key)) > MAX_KEY_LENGTH:
        prefix = cache.make_key('')
        
        # Just to be safe... we should be able to have a key >= 1 char long :)
        if len(prefix) >= MAX_KEY_LENGTH:
            raise Exception('Your cache key prefixes are too long.')

        key = hashlib.sha512(key).hexdigest()[:MAX_KEY_LENGTH - len(prefix)]
    return key



def _assemble_keys(func, *args, **kwargs):
    '''
    Add a bunch of hopefully uniquely identifying parameters to a list to be 
    passed to `make_key`.
    '''
    keys = ['cached_func']
    keys.append(func.__name__)

    # This works on both functions and class methods.
    signature_args = inspect.getargspec(func).args
    if (hasattr(func, '__self__') or
        (signature_args and signature_args[0] == 'self')):
        # Method, probably.
        # A guess is good enough, since it only means that we add some extra
        # fields from the first arg. If we're wrong, it just means the key
        # is more conservative (more detailed) than need be. We could wrongly
        # call it a function when it's actually a method, but only if they're
        # doing unsightly things like naming the "self" arg something else.
        self = args[0]
        keys.append(self.__class__.__name__)
        if hasattr(self, 'pk'): # django model? `pk` is a great differentiator!
            keys.append(self.pk)
        keys.extend(args[1:])
    else:
        # Function.
        keys.extend(args)
    keys.extend(kwargs.values())

    # To be extra safe! (unreadable, so at end of key.)
    # If this results in any collisions, it actually won't make a difference.
    # It's fine to memoize functions that collide on this as if
    # they are one, since they're identical if their codeblock hash is the same.
    keys.append(hex(func.__code__.__hash__()))

    return keys


def _cached_function(keys, func, args_and_kwargs):
    args, kwargs = args_and_kwargs
    key = make_key(*(keys or _assemble_keys(func, *args, **kwargs)))
    print key

    def invalidate():
        print 'cache deleting: ',
        print key
        cache.delete(key)

    ret = cache.get(key)
    if ret is None:
        ret = func(*args, invalidate_cache=invalidate, **kwargs)
        cache.set(key, ret)
    return ret


def cached_function(timeout=0, keys=None):
    '''
    Adds a kwarg to the function, `invalidate_cache`. This allows the function
    to setup signal listeners for invalidating the cache.

    Works on both functions and class methods.
    '''
    def decorator(func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            return _cached_function(keys, func, (args, kwargs))
        return wrapped
    return decorator


def cached_view(timeout=0, keys=None):
    '''
    Handles HttpRequest object args intelligently when auto-generating the 
    cache key.

    Only caches GET and HEAD requests.
    '''
    def decorator(func):
        @wraps(func)
        def wrapped(request, *args, **kwargs):
            # Don't cache non-GET/HEAD requests.
            if request.method not in ['GET', 'HEAD']:
                return func(request, *args, **kwargs)

            if not keys:
                # Don't naively add the `request` arg to the cache key.
                keys2 = _assemble_keys(func, *args, **kwargs)
                
                # Only add specific parts of the `request` object to the key.
                # Add the URL query parameters.
                keys2.extend(list(chain.from_iterable(request.GET.items())))
            return _cached_function(keys2, func, ((request,) + args, kwargs,))
        return wrapped
    return decorator



