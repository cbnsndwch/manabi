from functools import wraps

#decorator_with_arguments = lambda decorator: lambda *args, **kwargs: lambda func: decorator(func, *args, **kwargs)


def all_http_methods(view_func):
    """
    Decorator that adds headers to a response so that it will
    never be cached.
    """
    def _wrapped_view_func(request, *args, **kwargs):
        #modified_request = request #shallow copy is enough
        if request.method == 'POST':
            if '_method' in request.POST and request.POST['_method'] in ['PUT', 'DELETE', 'GET', 'POST']:
                method = request.POST['_method']
                #modified_request = request.copy()
                request.method = method
        return view_func(request, *args, **kwargs)
    return wraps(view_func)(_wrapped_view_func)

