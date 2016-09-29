#TODO-OLD from account.models import Account
import pytz
import datetime

from django.conf import settings


def seconds_to_days(s):
    return s / 86400.


def start_and_end_of_day(user, time_zone, date=None):
    '''
    `date` is a datetime.date object.
    `time_zone` is a pytz object.

    Returns a tuple of 2 UTC datetimes.

    Uses waking hours, not calendar day.
    '''
    if date is None:
        # Today
        date = datetime.datetime.now(time_zone).date()

    start = datetime.datetime.combine(date, datetime.time(
        hour=settings.START_OF_DAY, minute=0, second=0, tzinfo=time_zone)
    ).astimezone(pytz.utc)

    #start = datetime.datetime.now(timezone).replace(
    #    hour=settings.START_OF_DAY, minute=0, second=0).astimezone(pytz.utc)

    end = start + datetime.timedelta(hours=23, minutes=59, seconds=59)

    return (start, end)
