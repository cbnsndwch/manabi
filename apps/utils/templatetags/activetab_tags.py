from django import template
from snippetscream import resolve_to_name
from manabi import tabs

register = template.Library()

@register.simple_tag
def is_active_tab(request, tab_name):
    '''
    Returns 'active' if this tab is the active one.
    Otherwise returns ''.
    '''

    url_name = resolve_to_name(request.path)
    print url_name

    if url_name in tabs.TAB_URLS[tab_name]:
        return 'active'
    else:
        return ''

@register.simple_tag
def active_tab(request):
    print 'active_tab'
    print request.path
    url_name = resolve_to_name(request.path)
    print request.path
    print url_name

    for tab_name, urls in tabs.TAB_URLS.iteritems():
        if url_name in urls:
            return tab_name

    return ''




