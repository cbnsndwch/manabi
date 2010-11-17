from functools import wraps


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
    
