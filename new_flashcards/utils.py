
def str_to_bool(string):
    '''
    Returns a bool corresponding to the string's value.
    e.g. `false` or `False` will both return False
    '''
    return string.lower() == 'true'


def timedelta_to_float(timedelta_obj):
    '''Returns a float of days.'''
    return float(timedelta_obj.days) + timedelta_obj.seconds / 86400.0



