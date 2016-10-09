from time import mktime


def unix_time(dt):
    return int(mktime(dt.timetuple()))

def timedelta_to_float(timedelta_obj):
    '''Returns a float of days.'''
    return float(timedelta_obj.days) + timedelta_obj.seconds / 86400.0

