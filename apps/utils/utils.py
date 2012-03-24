from time import mktime

def unix_time(dt):
    return int(mktime(dt.timetuple()))

