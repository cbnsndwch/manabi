from django import template

register = template.Library()
def key(d, key_name):
    if hasattr(d, 'has_key') and key_name in d:
        return d[key_name]
    else:
        return None
key = register.filter('key', key)

