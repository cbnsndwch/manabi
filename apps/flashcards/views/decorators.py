from functools import wraps
from dojango.decorators import json_response
from django.contrib.auth.decorators import login_required

#decorator_with_arguments = lambda decorator: lambda *args, **kwargs: lambda func: decorator(func, *args, **kwargs)


def all_http_methods(view_func):
    '''
    Decorator that adds headers to a response so that it will
    never be cached.
    '''
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        #modified_request = request #shallow copy is enough
        if request.method == 'POST':
            if '_method' in request.POST and request.POST['_method'] in ['PUT', 'DELETE', 'GET', 'POST']:
                method = request.POST['_method']
                request.method = method
        return view_func(request, *args, **kwargs)
    return wrapper


def has_card_query_filters(func):
    '''
    Adds some kwargs to the `func` call for cleaning request GET data into
    querysets.

    Adds the following (potentially with value None):
        `deck`, `tags`
    '''
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        # Deck
        if 'deck' in request.GET and request.GET['deck'].strip():
            deck = get_object_or_404(Deck, pk=request.GET['deck'])
        else:
            deck = None
        kwargs['deck'] = deck

        # Tags
        try:
            tag_id = int(request.GET.get('tag', -1))
        except ValueError:
            tag_id = -1
        if tag_id != -1:
            tag_ids = [tag_id] #TODO support multiple tags
            tags = usertagging.models.Tag.objects.filter(id__in=tag_ids)
        else:
            tags = None
        kwargs['tags'] = tags

        return func(request, *args, **kwargs)

    return wrapper
    


def flashcard_api(view_func):
    '''
    Our standard decorator for JSON API views,
    within our flashcard API.

    It's just a shortcut for decorating with the following:
        `@json_response`
        `@login_required`
        `@all_http_methods`
        `@has_card_query_filters`
    '''
    return json_response(
           login_required(
           all_http_methods(
           has_card_query_filters(view_func))))

