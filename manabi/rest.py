from catnap.rest_views import JsonEmitterMixin, AutoContentTypeMixin, RestView
from catnap.permissions import PermissionsMixin
import catnap.permissions

class ManabiRestView(PermissionsMixin, JsonEmitterMixin, AutoContentTypeMixin, RestView):
    '''
    Our JSON-formatted response base class.
    '''
    content_type_template_string = 'application/vnd.org.manabi.{0}+json'
    permissions = catnap.permissions.AllowAny()

