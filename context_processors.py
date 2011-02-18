
def site_base_extender(request):
    '''
    adds `base_template_name` to context
    '''
    return {
        'base_template_name': (
            'body_pane_base.html' if request.is_ajax()
            else 'site_base.html'
    )}

