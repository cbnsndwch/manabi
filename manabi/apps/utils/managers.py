from django.db.models.query import QuerySet
from model_utils.managers import PassThroughManager


# This is an awful hack just for backwards-compatibility's sake.
# We will not be playing with this kind of fire for new code going forward.
#def manager_from(*classes):
#    class ManagerFrom(QuerySet):
#        pass

#    #ManagerFrom.__bases__ = classes + (ManagerFrom.__class__,)
#    ManagerFrom = type(
#        'ExtendedManagerFrom',
#        classes + (ManagerFrom.__class__,), 
#        {}
#    )

#    return PassThroughManager.for_queryset_class(ManagerFrom)

