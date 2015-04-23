from catnap.rest_views import JsonEmitterMixin, AutoContentTypeMixin, RestView
from catnap.permissions import PermissionsMixin
import catnap.permissions
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt


class ManabiRestView(PermissionsMixin, JsonEmitterMixin, RestView):
    '''
    Our JSON-formatted response base class.
    '''
    #content_type_template_string = 'application/vnd.org.manabi.{0}+json; charset=utf-8'
    content_type = 'application/json; charset=utf-8'
    permissions = catnap.permissions.AllowAny()

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(ManabiRestView, self).dispatch(*args, **kwargs)
