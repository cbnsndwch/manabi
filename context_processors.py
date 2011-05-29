
def site_base_extender(request):
    '''
    Adds `base_template_name` to context for pages like the ToS.

    And `fragment_base_template_name` for ajax pages that need to be rendered
    differently for googlebot.

    Also adds `request_is_ajax` boolean to context.
    '''
    ctx = {'request_is_ajax': request.is_ajax()}

    if hasattr(request, 'fragment_base_template_name'):
        fragment_name = request.fragment_base_template_name
    else:
        if request.is_ajax():
            name = 'body_pane_base.html' 
        else:
            name ='site_base.html'
        ctx['base_template_name'] = name

        # Googlebot?
        if (request.META.get('HTTP_X_ESCAPED_FRAGMENT', 'false').lower()
                == 'true'):
            fragment_name = 'site_base.html'
        else:
            fragment_name = 'body_pane_base.html'
    ctx['fragment_base_template_name'] = fragment_name
    return ctx

