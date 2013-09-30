from django.utils.translation import ugettext as _

from usertagging.managers import ModelTaggedItemManager, TagDescriptor

VERSION = (0, 4, 'pre')

registry = []

def register(model, tag_descriptor_attr='tags',
             tagged_item_manager_attr='tagged'):
    """
    Sets the given model class up for working with tags.
    """
    # Issue 128: http://code.google.com/p/django-tagging/issues/detail?id=128
    # manage.py runserver run twice this code, manage.py shell run when start
    # shell and when you import your model, manage.py dbshell run only one time.
    # manage.py shell raises AlreadyRegistered when you try to load your model,
    # in http://code.google.com/p/django-tagging/issues/detail?id=128&q=shell#c1
    # trentm use a try ... except to handle it, but, apparently is best to
    # simple ignore if model already register.
    # Felipe Prenholato <philipe.rp@gmail.com>
    if model not in registry:
        registry.append(model)

        # Add tag descriptor
        setattr(model, tag_descriptor_attr, TagDescriptor())

        # Add custom manager
        ModelTaggedItemManager().contribute_to_class(model,
                tagged_item_manager_attr)
