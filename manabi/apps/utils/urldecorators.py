from django.core.urlresolvers import RegexURLPattern, RegexURLResolver
from django.conf.urls import patterns

class DecoratedURLPattern(RegexURLPattern):
    def resolve(self, *args, **kwargs):
        result = RegexURLPattern.resolve(self, *args, **kwargs)
        if result:
            result.func = self._decorate_with(result.func)
        return result

def decorated_patterns(prefix, func, *args, **kwargs):
    '''
    http://djangosnippets.org/snippets/532/

    Example usage:

        def control_access(view_func):
            def _checklogin(request, *args, **kwargs):
                raise Http404()
            return _checklogin

        urlpatterns = patterns('views',
            # unprotected views
            (r'^public/contact/$', 'contact'),
            (r'^public/imprint/$', 'imprint'),
        ) + decorated_patterns('views', control_access,
            (r'^admin/add/$', 'add'),
            (r'^admin/edit/$', 'edit'),
        )
    '''
    result = patterns(prefix, *args, **kwargs)
    if func:
        for p in result:
            if isinstance(p, RegexURLPattern):
                p.__class__ = DecoratedURLPattern
                p._decorate_with = func
            elif isinstance(p, RegexURLResolver):
                for pp in p._get_url_patterns():
                    if isinstance(pp, RegexURLPattern):
                        pp.__class__ = DecoratedURLPattern
                        pp._decorate_with = func
    return result




